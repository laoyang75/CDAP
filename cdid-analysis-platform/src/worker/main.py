"""Worker 主循环

FIFO 单线程任务处理器，负责执行完整的数据分析流程
"""

import asyncio
import contextlib
import json
import logging
import os
import signal
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session, sessionmaker

from src.config import Config, get_config
from src.db import Job, Pipeline, Script, get_engine
from src.worker.analyzers.duofa import DuofaAnalyzer
from src.worker.gemini_reporter import GeminiReporter
from src.worker.insight_client import InsightClient, TaskCancelledError
from src.worker.script_runner import run_analysis_script

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Worker:
    """任务处理 Worker"""

    def __init__(self, config: Config, engine):
        self.config = config
        self.engine = engine
        self.SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

        self.fetch_semaphore = asyncio.Semaphore(1)
        self.analysis_semaphore = asyncio.Semaphore(1)
        self.report_semaphore = asyncio.Semaphore(1)

        self.insight_client = InsightClient(config)
        self.analyzer = DuofaAnalyzer(config)
        self.reporter = GeminiReporter(config)

    def _session(self) -> Session:
        return self.SessionLocal()

    def claim_next_job(self) -> Optional[str]:
        """原子领取一个 queued 任务，避免并发重复领取"""
        session = self._session()
        try:
            job = (
                session.query(Job)
                .filter_by(status="queued")
                .order_by(Job.created_at.asc())
                .first()
            )
            if not job:
                session.commit()
                return None
            if job.cancel_requested:
                job.status = "canceled"
                job.progress = 100
                job.progress_message = "已取消"
                job.updated_at = datetime.now(timezone.utc)
                session.commit()
                return None

            job.status = "fetching_data"
            job.progress = job.progress or 0
            job.progress_message = job.progress_message or "任务已被 Worker 领取"
            job.updated_at = datetime.now(timezone.utc)
            session.commit()
            return job.id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_status(
        self,
        job_id: str,
        status: str,
        progress: Optional[int] = None,
        progress_message: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """更新任务状态

        Args:
            job_id: 任务ID
            status: 新状态
            progress: 进度（0-100）
            progress_message: 进度消息
            error: 错误信息
        """
        session = self._session()
        try:
            job = session.query(Job).filter_by(id=job_id).first()
            if not job:
                logger.error(f"任务不存在: {job_id}")
                return

            job.status = status
            job.updated_at = datetime.now(timezone.utc)

            if progress is not None:
                job.progress = progress

            if progress_message is not None:
                job.progress_message = progress_message

            if error is not None:
                job.error = error

            session.commit()
        finally:
            session.close()
        logger.info(
            f"任务 {job_id} 状态更新: {status} ({progress}%) - {progress_message}"
        )

    def mark_failed(self, job_id: str, error: str) -> None:
        """标记任务失败

        Args:
            job_id: 任务ID
            error: 错误信息
        """
        self.update_status(
            job_id, status="failed", progress=100, progress_message="失败", error=error
        )

    def set_active_process(self, job_id: str, *, step: str, pid: int) -> None:
        session = self._session()
        try:
            job = session.query(Job).filter_by(id=job_id).first()
            if not job:
                session.commit()
                return
            job.active_step = step
            job.active_pid = int(pid)
            job.active_started_at = datetime.now(timezone.utc)
            job.updated_at = datetime.now(timezone.utc)
            session.commit()
        finally:
            session.close()

    def clear_active_process(self, job_id: str) -> None:
        session = self._session()
        try:
            job = session.query(Job).filter_by(id=job_id).first()
            if not job:
                session.commit()
                return
            job.active_step = None
            job.active_pid = None
            job.active_started_at = None
            job.updated_at = datetime.now(timezone.utc)
            session.commit()
        finally:
            session.close()

    def is_cancel_requested(self, job_id: str) -> bool:
        session = self._session()
        try:
            job = session.query(Job).filter_by(id=job_id).first()
            if not job:
                return False
            return bool(job.cancel_requested) or job.status == "canceled"
        finally:
            session.close()

    def mark_canceled(self, job_id: str, message: str = "已取消") -> None:
        self.update_status(
            job_id,
            status="canceled",
            progress=100,
            progress_message=message,
            error="canceled",
        )

    def _get_job_snapshot(self, job_id: str) -> Job:
        session = self._session()
        try:
            job = session.query(Job).filter_by(id=job_id).first()
            if not job:
                raise ValueError(f"任务不存在: {job_id}")
            # detach-ish snapshot: 返回 ORM 对象给调用方读取即可，不跨 await 修改
            session.expunge(job)
            return job
        finally:
            session.close()

    def _set_job_fields(self, job_id: str, **fields) -> None:
        session = self._session()
        try:
            job = session.query(Job).filter_by(id=job_id).first()
            if not job:
                session.commit()
                return
            for k, v in fields.items():
                setattr(job, k, v)
            job.updated_at = datetime.now(timezone.utc)
            session.commit()
        finally:
            session.close()

    async def process_job(self, job_id: str) -> None:
        """处理单个任务

        Args:
            job_id: 任务ID

        Raises:
            Exception: 处理过程中的任何异常
        """
        job = self._get_job_snapshot(job_id)
        logger.info(f"开始处理任务: {job_id} - {job.name}")

        try:
            if self.is_cancel_requested(job_id):
                self.mark_canceled(job_id, "任务已取消")
                return

            raw_data_path: Optional[Path] = None
            if job.raw_data_path:
                candidate = Path(job.raw_data_path)
                if candidate.exists():
                    raw_data_path = candidate

            if raw_data_path is not None:
                self.update_status(
                    job_id,
                    status="fetching_data",
                    progress=40,
                    progress_message="检测到已有原始数据文件，跳过内网拉取与下载...",
                )
            else:
                # 阶段 1: 调用内网 API 获取原始数据
                self.update_status(
                    job_id,
                    status="fetching_data",
                    progress=10,
                    progress_message="正在调用内网 API 获取数据...",
                )

                if self.is_cancel_requested(job_id):
                    self.mark_canceled(job_id, "任务已取消")
                    return

                # 创建上游任务
                async with self.fetch_semaphore:
                    upstream_task_id = await self.insight_client.create_task(
                        name=job.name,
                        package_name=job.package_name,
                        file_path=job.input_file_path,
                        start_date=job.start_date,
                        end_date=job.end_date,
                        message_types=job.message_types,
                    )

                # 保存上游任务ID
                self._set_job_fields(job_id, insight_task_id=upstream_task_id)

                self.update_status(
                    job_id,
                    status="fetching_data",
                    progress=20,
                    progress_message=f"等待内网 API 处理数据（任务ID: {upstream_task_id}）...",
                )

                # 轮询直到上游任务完成
                status_info = await self.insight_client.poll_until_complete(
                    upstream_task_id,
                    poll_interval=self.config.worker_poll_interval,
                    max_wait_time=self.config.worker_job_timeout,
                    should_cancel=lambda: self.is_cancel_requested(job_id),
                )

                # 下载结果文件
                oss_url = status_info.get("oss_url")
                if not oss_url:
                    raise ValueError("上游任务已完成但未返回下载地址")
                raw_data_path = (
                    Path(self.config.storage_output_dir) / job_id / "raw_data.xlsx"
                )
                raw_data_path.parent.mkdir(parents=True, exist_ok=True)

                self.update_status(
                    job_id,
                    status="fetching_data",
                    progress=40,
                    progress_message="正在下载原始数据...",
                )

                if self.is_cancel_requested(job_id):
                    self.mark_canceled(job_id, "任务已取消")
                    return

                async with self.fetch_semaphore:
                    await self.insight_client.download_result(oss_url, str(raw_data_path))

                self._set_job_fields(job_id, raw_data_path=str(raw_data_path))

            # 阶段 2: 执行多发检测分析
            self.update_status(
                job_id,
                status="analyzing",
                progress=50,
                progress_message="正在执行多发检测分析...",
            )

            if self.is_cancel_requested(job_id):
                self.mark_canceled(job_id, "任务已取消")
                return

            job_info = {
                "job_id": job.id,
                "name": job.name,
                "package_name": job.package_name,
                "start_date": job.start_date,
                "end_date": job.end_date,
                "message_types": job.message_types,
            }

            pipeline_ids = job.pipeline_ids or []
            if not pipeline_ids:
                session = self._session()
                try:
                    pipelines = (
                        session.query(Pipeline)
                        .filter(Pipeline.is_active == True)  # noqa: E712
                        .order_by(Pipeline.created_at.desc())
                        .all()
                    )
                finally:
                    session.close()
                default_pipeline = None
                for p in pipelines:
                    cfg = p.config if isinstance(p.config, dict) else {}
                    if cfg.get("is_default") is True:
                        default_pipeline = p
                        break
                if default_pipeline is None and pipelines:
                    default_pipeline = pipelines[0]

                if default_pipeline is None:
                    raise ValueError("任务未选择任何分析管线，且系统无可用默认管线")

                pipeline_ids = [default_pipeline.id]
                self._set_job_fields(job_id, pipeline_ids=pipeline_ids)

            report_items: list[dict] = []
            total_pipelines = len(pipeline_ids)

            for idx, pipeline_id in enumerate(pipeline_ids, start=1):
                if self.is_cancel_requested(job_id):
                    self.mark_canceled(job_id, "任务已取消")
                    return

                session = self._session()
                try:
                    pipeline = (
                        session.query(Pipeline)
                        .filter(Pipeline.id == int(pipeline_id))
                        .first()
                    )
                finally:
                    session.close()
                if not pipeline or not pipeline.is_active:
                    raise ValueError(f"管线不存在或未启用: {pipeline_id}")

                cfg = pipeline.config if isinstance(pipeline.config, dict) else {}
                analysis_script_id = cfg.get("analysis_script_id")
                prompt_script_id = cfg.get("report_prompt_script_id")
                gemini_model = cfg.get("gemini_model")

                # 兼容旧字段（analysis.type/script_id/builtin）
                if analysis_script_id is None and isinstance(cfg.get("analysis"), dict):
                    analysis_script_id = cfg["analysis"].get("script_id")

                self.update_status(
                    job_id,
                    status="analyzing",
                    progress=50 + int((idx - 1) * 30 / max(total_pipelines, 1)),
                    progress_message=f"正在执行分析脚本（{idx}/{total_pipelines}）：{pipeline.name}",
                )

                analysis_result: dict
                if analysis_script_id:
                    session = self._session()
                    try:
                        script = (
                            session.query(Script)
                            .filter(Script.id == int(analysis_script_id))
                            .first()
                        )
                    finally:
                        session.close()
                    if not script or not script.is_active:
                        raise ValueError(f"分析脚本不存在或未启用: {analysis_script_id}")

                    async with self.analysis_semaphore:
                        analysis_result = await run_analysis_script(
                            code=script.code,
                            input_file=str(raw_data_path),
                            job_info={**job_info, "pipeline": {"id": pipeline.id, "name": pipeline.name}},
                            timeout_seconds=self.config.worker_job_timeout,
                        )
                else:
                    # fallback：内置 duofa
                    async with self.analysis_semaphore:
                        analysis_result = self.analyzer.analyze(str(raw_data_path), job_info)

                # 保存每条管线的分析 JSON 便于排查
                pipeline_dir = Path(self.config.storage_output_dir) / job_id / "pipelines" / str(pipeline.id)
                pipeline_dir.mkdir(parents=True, exist_ok=True)
                analysis_json_path = pipeline_dir / "analysis.json"
                analysis_json_path.write_text(
                    json.dumps(analysis_result, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

                prompt_text = None
                if prompt_script_id:
                    session = self._session()
                    try:
                        prompt_script = (
                            session.query(Script)
                            .filter(Script.id == int(prompt_script_id))
                            .first()
                        )
                    finally:
                        session.close()
                    if not prompt_script or not prompt_script.is_active:
                        raise ValueError(f"报告 Prompt 不存在或未启用: {prompt_script_id}")
                    prompt_text = prompt_script.code

                self.update_status(
                    job_id,
                    status="generating_report",
                    progress=50 + int(idx * 30 / max(total_pipelines, 1)),
                    progress_message=f"正在生成报告（{idx}/{total_pipelines}）：{pipeline.name}",
                )

                report_path = pipeline_dir / "report.html"
                try:
                    if self.is_cancel_requested(job_id):
                        self.mark_canceled(job_id, "任务已取消")
                        return

                    async with self.report_semaphore:
                        await self.reporter.generate_report(
                            analysis_result,
                            str(report_path),
                            prompt=prompt_text,
                            model=gemini_model,
                            pid_callback=lambda pid: self.set_active_process(
                                job_id, step="generating_report", pid=pid
                            ),
                        )
                finally:
                    self.clear_active_process(job_id)

                report_items.append(
                    {
                        "pipeline_id": pipeline.id,
                        "pipeline_name": pipeline.name,
                        "analysis_json": str(analysis_json_path),
                        "report_path": str(report_path),
                    }
                )

            if total_pipelines == 1:
                # 单管线：报告直接指向该管线的 report.html，保证下载即是最终报告
                self._set_job_fields(job_id, report_path=report_items[0]["report_path"])
            else:
                # 多管线：写一个索引 report.html（API 会打包下载完整报告集）
                self.update_status(
                    job_id,
                    status="generating_report",
                    progress=90,
                    progress_message="汇总多管线报告...",
                )

                index_report_path = (
                    Path(self.config.storage_output_dir) / job_id / "report.html"
                )
                index_report_path.parent.mkdir(parents=True, exist_ok=True)
                links = "\n".join(
                    f'<li><a href="pipelines/{item["pipeline_id"]}/report.html" target="_blank">{item["pipeline_name"]}</a></li>'
                    for item in report_items
                )
                index_report_path.write_text(
                    "<!doctype html><html lang='zh-CN'><head><meta charset='UTF-8'>"
                    "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
                    "<title>分析报告索引</title>"
                    "<style>body{font-family:Arial,Helvetica,sans-serif;padding:24px;}"
                    "h1{font-size:20px;}li{margin:8px 0;}</style></head><body>"
                    f"<h1>任务报告索引：{job.name}</h1>"
                    "<p>该任务选择了多个管线，请分别查看对应报告：</p>"
                    f"<ul>{links}</ul>"
                    "</body></html>",
                    encoding="utf-8",
                )

                self._set_job_fields(job_id, report_path=str(index_report_path))

            # 完成
            self.update_status(
                job_id,
                status="completed",
                progress=100,
                progress_message="任务完成",
            )

            logger.info(
                f"任务 {job_id} 处理完成，报告保存至: {report_path}"
            )

        except TaskCancelledError:
            self.mark_canceled(job_id, "任务已取消")
            return
        except Exception as e:
            logger.error(f"任务 {job_id} 处理失败: {e}", exc_info=True)
            if self.is_cancel_requested(job_id):
                self.mark_canceled(job_id, "任务已取消")
                return
            self.mark_failed(job_id, str(e))
            raise

    async def _watchdog(self) -> None:
        """监控运行中的外部进程，超时则强杀并标记失败，避免卡死堵队列。"""
        while True:
            await asyncio.sleep(5)
            session = self._session()
            try:
                now = datetime.now(timezone.utc)
                jobs = (
                    session.query(Job)
                    .filter(Job.active_pid.isnot(None))
                    .filter(Job.active_step == "generating_report")
                    .all()
                )
                for job in jobs:
                    if not job.active_started_at:
                        continue
                    elapsed = (now - job.active_started_at).total_seconds()
                    if elapsed <= (self.config.gemini_timeout + 30):
                        continue
                    pid = int(job.active_pid)
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except Exception:
                        pass
                    job.status = "failed"
                    job.progress = 100
                    job.progress_message = "报告生成超时，已终止进程"
                    job.error = f"Gemini 超时（>{self.config.gemini_timeout}s），已杀进程 pid={pid}"
                    job.active_pid = None
                    job.active_step = None
                    job.active_started_at = None
                    job.updated_at = now

                # 兜底：某些历史版本会把任务卡在 running 状态但没 active_pid（例如进程崩溃/重启）
                stale_jobs = (
                    session.query(Job)
                    .filter(Job.status.in_(["fetching_data", "analyzing", "generating_report"]))
                    .filter(Job.active_pid.is_(None))
                    .all()
                )
                for job in stale_jobs:
                    elapsed = (now - job.updated_at).total_seconds()
                    if elapsed <= max(300, int(self.config.worker_job_timeout)):
                        continue
                    job.status = "failed"
                    job.progress = 100
                    job.progress_message = "任务卡住超时（无活跃进程），已标记失败"
                    job.error = "stale_running_job"
                    job.updated_at = now
                session.commit()
            except Exception:
                session.rollback()
            finally:
                session.close()

    async def run_forever(self) -> None:
        """主循环，持续轮询并处理任务"""
        logger.info("Worker 启动，开始轮询任务...")

        watchdog_task = asyncio.create_task(self._watchdog())
        running: set[asyncio.Task] = set()

        try:
            while True:
                try:
                    # 尽量填满并发槽位
                    while len(running) < max(1, int(self.config.worker_max_concurrent_jobs)):
                        job_id = self.claim_next_job()
                        if not job_id:
                            break
                        task = asyncio.create_task(self.process_job(job_id))
                        running.add(task)
                        task.add_done_callback(lambda t: running.discard(t))

                    if not running:
                        await asyncio.sleep(self.config.worker_poll_interval)
                        continue

                    done, _pending = await asyncio.wait(
                        running,
                        timeout=self.config.worker_poll_interval,
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    for t in done:
                        with contextlib.suppress(Exception):
                            t.result()
                except KeyboardInterrupt:
                    logger.info("接收到中断信号，停止 Worker...")
                    break
                except Exception as e:
                    logger.error(f"Worker 主循环异常: {e}", exc_info=True)
                    await asyncio.sleep(self.config.worker_poll_interval)
        finally:
            watchdog_task.cancel()
            for t in list(running):
                t.cancel()
            with contextlib.suppress(Exception):
                await watchdog_task


async def main():
    """Worker 入口函数"""
    config = get_config()
    engine = get_engine(config)

    logger.info(f"Worker 配置加载完成")
    logger.info(f"  - 轮询间隔: {config.worker_poll_interval}秒")
    logger.info(f"  - 任务超时: {config.worker_job_timeout}秒")
    logger.info(f"  - 上游 API: {config.upstream_base_url}")
    logger.info(f"  - Gemini CLI: {config.gemini_cli_path}")

    # 验证 Gemini CLI
    reporter = GeminiReporter(config)
    if not reporter.validate_gemini_cli():
        logger.warning(
            f"警告: Gemini CLI 不可用（{config.gemini_cli_path}），报告生成可能失败"
        )

    worker = Worker(config, engine)
    await worker.run_forever()


def start_worker():
    """启动 Worker（同步入口）"""
    asyncio.run(main())


if __name__ == "__main__":
    start_worker()
