"""内网 API 客户端

封装对 http://172.17.129.204:6829 的调用
"""

import asyncio
import zipfile
from pathlib import Path
from typing import Callable, Dict, List, Optional

import httpx

from src.config import Config


class TaskCancelledError(RuntimeError):
    """用于中断上游轮询的取消异常"""


class InsightClient:
    """内网 Insight API 客户端"""

    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.upstream_base_url
        self.timeout = config.upstream_timeout
        self.retry_times = config.upstream_retry_times
        self.retry_interval = config.upstream_retry_interval

    async def create_task(
        self,
        name: str,
        package_name: str,
        file_path: str,
        start_date: str,
        end_date: str,
        message_types: List[str],
    ) -> str:
        """创建任务

        Args:
            name: 任务名称
            package_name: 包名
            file_path: 文件路径
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            message_types: 消息类型列表 (如 ["dna", "daa"])

        Returns:
            str: 任务ID

        Raises:
            httpx.HTTPError: HTTP 请求错误
            ValueError: API 返回错误
        """
        url = f"{self.base_url}{self.config.upstream_create_task_endpoint}"

        # Insight 上游接口使用 multipart/form-data，并且 message 需要以“同名多字段”方式提交：
        # curl 示例：-F "message=dna" -F "message=daa"
        #
        # 注意：在 httpx==0.26.0 下，data=list[tuple] + files=... 的组合在某些环境会触发
        # h11 的 TypeError（bytes 拼接遇到 tuple）。因此这里统一把“文本字段 + 文件”都放到
        # files=list[tuple] 里编码成 multipart，避免该兼容性问题。
        #
        # 另外，httpx==0.26.0 的 AsyncClient 发送 multipart(files=...) 还会报：
        # "Attempted to send an sync request with an AsyncClient instance."
        # 因此这里使用同步 Client 放到线程池中执行，避免阻塞事件循环。
        def _post_sync() -> dict:
            with open(file_path, "rb") as f:
                files: list[tuple[str, object]] = [
                    ("name", (None, name)),
                    ("package_name", (None, package_name)),
                    ("start", (None, start_date)),
                    ("end", (None, end_date)),
                ]
                for m in message_types:
                    if m:
                        files.append(("message", (None, m)))

                files.append(
                    (
                        "file",
                        (Path(file_path).name, f, "application/octet-stream"),
                    )
                )
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, files=files)
                    resp.raise_for_status()
                    return resp.json()

        # 带重试的请求
        for attempt in range(self.retry_times):
            try:
                result = await asyncio.to_thread(_post_sync)

                # 检查业务错误码
                if result.get("code") != 0:
                    raise ValueError(
                        f"API 返回错误: code={result.get('code')}, "
                        f"message={result.get('message')}"
                    )

                # 提取 task_id
                task_id = result.get("data", {}).get("task_id")
                if not task_id:
                    raise ValueError("API 未返回 task_id")

                return task_id

            except (httpx.HTTPError, ValueError) as e:
                if attempt < self.retry_times - 1:
                    await asyncio.sleep(self.retry_interval)
                    continue
                raise

    async def query_task_status(self, task_id: str) -> Dict:
        """查询任务状态

        Args:
            task_id: 任务ID

        Returns:
            Dict: 任务状态信息，包含:
                - status: 任务状态 (running, success, failed)
                - oss_url: 结果文件URL (status=success 时存在)
                - error: 错误信息 (status=failed 时存在)

        Raises:
            httpx.HTTPError: HTTP 请求错误
            ValueError: API 返回错误
        """
        url = f"{self.base_url}{self.config.upstream_get_task_endpoint}"
        params = {"task_id": task_id}

        for attempt in range(self.retry_times):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()

                    result = response.json()

                    if result.get("code") != 0:
                        raise ValueError(
                            f"API 返回错误: code={result.get('code')}, "
                            f"message={result.get('message')}"
                        )

                    data = result.get("data", {})
                    oss_url = (
                        data.get("oss_url")
                        or data.get("download_url")
                        or data.get("url")
                    )
                    return {
                        "status": data.get("status", "unknown"),
                        "oss_url": oss_url,
                        "error": data.get("error"),
                    }

            except (httpx.HTTPError, ValueError) as e:
                if attempt < self.retry_times - 1:
                    await asyncio.sleep(self.retry_interval)
                    continue
                raise

    async def download_result(self, oss_url: str, save_path: str) -> None:
        """下载结果文件

        Args:
            oss_url: OSS 文件URL
            save_path: 本地保存路径

        Raises:
            httpx.HTTPError: HTTP 请求错误
        """
        save_path_obj = Path(save_path)
        save_path_obj.parent.mkdir(parents=True, exist_ok=True)

        for attempt in range(self.retry_times):
            try:
                async with httpx.AsyncClient(timeout=self.timeout * 2) as client:
                    response = await client.get(oss_url)
                    response.raise_for_status()

                    with open(save_path, "wb") as f:
                        f.write(response.content)

                    file_path = Path(save_path)
                    if file_path.stat().st_size == 0:
                        raise ValueError("下载结果为空文件")

                    if file_path.suffix.lower() in [".xlsx", ".xls"]:
                        if not zipfile.is_zipfile(save_path):
                            raise ValueError("下载结果不是有效的 Excel 文件")

                    return

            except (httpx.HTTPError, ValueError) as e:
                if attempt < self.retry_times - 1:
                    await asyncio.sleep(self.retry_interval)
                    continue
                raise

    async def poll_until_complete(
        self,
        task_id: str,
        poll_interval: int = 30,
        max_wait_time: int = 1800,
        *,
        should_cancel: Optional[Callable[[], bool]] = None,
    ) -> Dict:
        """轮询直到任务完成

        Args:
            task_id: 任务ID
            poll_interval: 轮询间隔（秒）
            max_wait_time: 最大等待时间（秒）
            should_cancel: 可选的取消检测回调（返回 True 则立刻停止）

        Returns:
            Dict: 任务状态信息

        Raises:
            TimeoutError: 超时
            ValueError: 任务失败
        """
        elapsed = 0

        while elapsed < max_wait_time:
            if should_cancel and should_cancel():
                raise TaskCancelledError("任务已取消")
            status_info = await self.query_task_status(task_id)
            status = status_info["status"]
            normalized = str(status).lower()

            success_statuses = {"success", "succeed", "completed", "done", "成功", "完成"}
            failed_statuses = {"failed", "error", "失败"}
            running_statuses = {"running", "pending", "processing", "queued", "处理中", "排队中"}

            if status in success_statuses or normalized in success_statuses:
                return status_info
            elif status in failed_statuses or normalized in failed_statuses:
                raise ValueError(f"任务失败: {status_info.get('error', '未知错误')}")
            elif status in running_statuses or normalized in running_statuses:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
            else:
                raise ValueError(f"未知任务状态: {status}")

        raise TimeoutError(f"任务超时: 超过 {max_wait_time} 秒未完成")
