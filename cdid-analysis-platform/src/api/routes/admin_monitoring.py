"""管理端任务监控路由"""

import os
import signal
import subprocess
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.admin.auth import require_admin
from src.db import Job, User, get_db
from src.models.schemas import JobResponse

router = APIRouter(prefix="/api/admin/monitoring", tags=["管理端-任务监控"])


@router.get("/stats")
async def get_task_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """获取任务统计数据"""
    total = db.query(Job).count()
    queued = db.query(Job).filter(Job.status == "queued").count()
    running = db.query(Job).filter(
        Job.status.in_(["fetching_data", "analyzing", "generating_report"])
    ).count()
    completed = db.query(Job).filter(Job.status == "completed").count()
    failed = db.query(Job).filter(Job.status == "failed").count()

    return {
        "total": total,
        "queued": queued,
        "running": running,
        "completed": completed,
        "failed": failed,
    }


@router.get("/recent-jobs", response_model=list[JobResponse])
async def get_recent_jobs(
    limit: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """获取最近的任务"""
    jobs = db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()
    return jobs


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """取消任务（尽量优雅停止；若卡住可配合 kill）"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return {"ok": False, "message": "任务不存在"}

    job.cancel_requested = True
    job.status = "canceled"
    job.progress = 100
    job.progress_message = "已取消"
    db.commit()
    return {"ok": True}


@router.post("/jobs/{job_id}/requeue")
async def requeue_job(
    job_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """将任务重新放回队列（用于修复卡住/配置变更后的重跑）"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return {"ok": False, "message": "任务不存在"}

    job.cancel_requested = False
    job.active_pid = None
    job.active_step = None
    job.active_started_at = None
    job.status = "queued"
    job.progress = 0
    job.progress_message = "已重新排队"
    job.error = None
    job.report_path = None
    db.commit()
    return {"ok": True}


def _safe_kill_pid(pid: int) -> tuple[bool, str]:
    """只允许杀 gemini 相关进程，避免误杀。"""
    try:
        cmd = subprocess.run(
            ["ps", "-p", str(pid), "-o", "command="],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        ).stdout.strip()
        if not cmd:
            return True, "进程不存在"
        lowered = cmd.lower()
        if "gemini" not in lowered:
            return False, f"拒绝终止非 gemini 进程: {cmd[:200]}"

        os.kill(pid, signal.SIGTERM)
        # 尽量优雅退出；若仍存在，再强杀
        try:
            subprocess.run(
                ["ps", "-p", str(pid)],
                capture_output=True,
                text=True,
                timeout=1,
                check=False,
            )
            os.kill(pid, signal.SIGKILL)
            return True, "已发送 SIGTERM + SIGKILL"
        except Exception:
            return True, "已发送 SIGTERM"
    except Exception as e:
        return False, str(e)


@router.post("/jobs/{job_id}/kill")
async def kill_job_process(
    job_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """强制终止任务当前外部进程（目前主要用于卡住的 gemini）"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return {"ok": False, "message": "任务不存在"}
    if not job.active_pid:
        return {"ok": False, "message": "任务当前没有记录的 active_pid"}

    ok, message = _safe_kill_pid(int(job.active_pid))
    if ok:
        # 不直接改成 failed，让 Worker 自己捕获并写入错误；这里先请求取消
        job.cancel_requested = True
        db.commit()
    return {"ok": ok, "message": message}


@router.get("/logs")
async def tail_logs(
    component: str = "worker",
    tail: int = 200,
    _: User = Depends(require_admin),
):
    """读取日志末尾（用于后台页面展示）"""
    component = (component or "worker").lower()
    tail = max(10, min(int(tail), 2000))

    project_root = Path(__file__).resolve().parents[3]
    log_file = project_root / "logs" / f"{component}.log"
    if not log_file.exists():
        return {"ok": False, "message": f"日志不存在: {log_file}", "lines": []}

    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return {"ok": True, "lines": [ln.rstrip("\n") for ln in lines[-tail:]]}
    except Exception as e:
        return {"ok": False, "message": str(e), "lines": []}
