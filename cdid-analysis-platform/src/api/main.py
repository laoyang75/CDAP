"""FastAPI 主应用

CDID 数据分析平台 API 服务器
"""

import os
from pathlib import Path
from datetime import datetime, timezone, date
import tempfile
import zipfile
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from sqlalchemy.orm import Session
import ulid

from src.config import get_config
from src.db import Job, User, Pipeline, Script, ClientConfig, get_db, get_engine
from src.models.schemas import JobCreate, JobResponse, JobListResponse
from src.models.schemas import PipelinePublicResponse
from src.admin.auth import init_default_admin
from src.admin.bootstrap import init_default_admin_assets
from src.api.routes import (
    admin_auth,
    admin_users,
    admin_config,
    admin_monitoring,
    admin_pipelines,
    admin_scripts,
)

# 创建 FastAPI 应用
app = FastAPI(
    title="CDID 数据分析平台",
    description="CDID Data Analysis Platform API",
    version="1.0.0",
)

# 注册管理端路由
app.include_router(admin_auth.router)
app.include_router(admin_users.router)
app.include_router(admin_config.router)
app.include_router(admin_monitoring.router)
app.include_router(admin_pipelines.router)
app.include_router(admin_scripts.router)

# 获取配置
config = get_config()

# 配置静态文件和模板
static_dir = Path(__file__).parent.parent / "ui" / "static"
templates_dir = Path(__file__).parent.parent / "ui" / "templates"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates = Jinja2Templates(directory=str(templates_dir))


# ==================== 健康检查 ====================


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "version": "1.0.0"}


# ==================== 用户端 API ====================


@app.post("/api/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    name: str = Form(...),
    package_name: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    message_types: Optional[str] = Form(None),  # 逗号分隔的字符串（调试模式可省略）
    pipeline_ids: str = Form(...),  # 逗号分隔的管线ID列表（必填）
    debug_mode: bool = Form(False),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """创建新任务

    Args:
        name: 任务名称
        package_name: 包名
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        message_types: 消息类型（逗号分隔，如 "dna,daa"）
        file: 上传的文件
        db: 数据库会话

    Returns:
        JobResponse: 创建的任务
    """
    # 调试模式：允许用户直接上传已下载好的 raw_data.xlsx（跳过内网请求/下载）
    if debug_mode:
        if not package_name:
            package_name = "debug"
        today = date.today().isoformat()
        if not start_date:
            start_date = today
        if not end_date:
            end_date = today

    # 非调试模式：强制必填
    if not debug_mode:
        if not package_name:
            raise HTTPException(status_code=400, detail="package_name 必填")
        if not start_date or not end_date:
            raise HTTPException(status_code=400, detail="start_date/end_date 必填")
        if not message_types:
            raise HTTPException(status_code=400, detail="message_types 必填")

    # 验证文件类型
    file_ext = Path(file.filename).suffix.lower()
    if debug_mode:
        if file_ext != ".xlsx":
            raise HTTPException(status_code=400, detail="调试模式仅支持上传 .xlsx（与上游下载格式一致）")
    elif file_ext not in config.storage_allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}，仅支持 {config.storage_allowed_extensions}",
        )

    job_id = str(ulid.new())

    # 保存上传文件（原始上传）
    upload_dir = Path(config.storage_upload_dir) / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename

    with open(file_path, "wb") as f:
        content = await file.read()

        # 检查文件大小
        if len(content) > config.storage_max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件太大: {len(content)} bytes，最大允许 {config.storage_max_file_size} bytes",
            )

        f.write(content)

    # 解析 message_types（调试模式可为空）
    message_types_list: list[str] = []
    if message_types:
        message_types_list = [m.strip() for m in message_types.split(",") if m.strip()]

    # 解析 pipeline_ids（必填，允许多选）
    pipeline_id_list: list[int] = []
    for part in [p.strip() for p in pipeline_ids.split(",") if p.strip()]:
        try:
            pipeline_id_list.append(int(part))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的管线ID: {part}")

    if not pipeline_id_list:
        raise HTTPException(status_code=400, detail="必须至少选择一个分析管线")

    active_pipelines = (
        db.query(Pipeline)
        .filter(Pipeline.id.in_(pipeline_id_list))
        .filter(Pipeline.is_active == True)  # noqa: E712
        .all()
    )
    active_ids = {p.id for p in active_pipelines}
    missing = [pid for pid in pipeline_id_list if pid not in active_ids]
    if missing:
        raise HTTPException(status_code=400, detail=f"管线不存在或未启用: {missing}")

    raw_data_path = None
    if debug_mode:
        # 直接把上传文件作为 raw_data.xlsx 放到 outputs/<job_id>/raw_data.xlsx
        out_dir = Path(config.storage_output_dir) / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        raw_data_file = out_dir / "raw_data.xlsx"
        raw_data_file.write_bytes(content)
        raw_data_path = str(raw_data_file)

    # 创建任务记录
    job = Job(
        id=job_id,
        name=name,
        package_name=package_name,
        start_date=start_date,
        end_date=end_date,
        message_types=message_types_list,
        pipeline_ids=pipeline_id_list,
        status="queued",
        progress=0,
        progress_message="任务已创建，等待处理",
        input_file_path=str(file_path),
        raw_data_path=raw_data_path,
        debug_mode=debug_mode,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


@app.get("/api/jobs", response_model=JobListResponse)
async def list_jobs(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    db: Session = Depends(get_db),
):
    """获取任务列表

    Args:
        skip: 跳过数量
        limit: 返回数量限制
        status: 按状态过滤（可选）
        db: 数据库会话

    Returns:
        JobListResponse: 任务列表
    """
    query = db.query(Job)

    if status:
        query = query.filter(Job.status == status)

    total = query.count()
    jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()

    return JobListResponse(total=total, jobs=jobs)


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """获取任务详情

    Args:
        job_id: 任务ID
        db: 数据库会话

    Returns:
        JobResponse: 任务详情
    """
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    return job


@app.get("/api/pipelines", response_model=list[PipelinePublicResponse])
async def list_public_pipelines(db: Session = Depends(get_db)):
    """用户端获取可用管线列表（仅返回启用管线）"""
    pipelines = (
        db.query(Pipeline)
        .filter(Pipeline.is_active == True)  # noqa: E712
        .order_by(Pipeline.created_at.desc())
        .all()
    )

    default_id = None
    for p in pipelines:
        if isinstance(p.config, dict) and p.config.get("is_default") is True:
            default_id = p.id
            break
    if default_id is None and pipelines:
        default_id = pipelines[0].id

    return [
        PipelinePublicResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            is_default=(p.id == default_id),
        )
        for p in pipelines
    ]


@app.get("/api/jobs/{job_id}/report")
async def get_job_report(job_id: str, db: Session = Depends(get_db)):
    """下载任务报告

    Args:
        job_id: 任务ID
        db: 数据库会话

    Returns:
        FileResponse: HTML 报告文件
    """
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    if job.status != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")

    if not job.report_path or not Path(job.report_path).exists():
        raise HTTPException(status_code=404, detail="报告文件不存在")

    # 多管线：打包下载（包含索引 + pipelines/** 所有文件）
    job_dir = Path(job.report_path).parent
    pipelines_dir = job_dir / "pipelines"

    pipeline_dir_count = 0
    if pipelines_dir.exists():
        pipeline_dir_count = len([p for p in pipelines_dir.iterdir() if p.is_dir()])

    if pipeline_dir_count > 1:
        tmp_dir = Path(tempfile.mkdtemp(prefix=f"cdid_report_{job_id}_"))
        zip_path = tmp_dir / f"report_{job_id}.zip"

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # index
            zf.write(Path(job.report_path), arcname="report.html")

            # pipelines/**
            for file_path in pipelines_dir.rglob("*"):
                if not file_path.is_file():
                    continue
                arcname = str(file_path.relative_to(job_dir))
                zf.write(file_path, arcname=arcname)

        return FileResponse(
            str(zip_path),
            media_type="application/zip",
            filename=f"report_{job_id}.zip",
        )

    # 单管线：直接返回 HTML
    return FileResponse(
        job.report_path,
        media_type="text/html",
        filename=f"report_{job_id}.html",
    )


@app.get("/api/jobs/{job_id}/report/view")
async def view_job_report(
    job_id: str,
    pipeline_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """预览任务报告（用于页面 iframe 展示）

    - 单管线：直接返回该管线 report.html
    - 多管线：默认返回“第一个管线”的 report.html（也可指定 pipeline_id）
    - 下载全集请使用 /api/jobs/{job_id}/report
    """
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    if job.status != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")

    if not job.report_path or not Path(job.report_path).exists():
        raise HTTPException(status_code=404, detail="报告文件不存在")

    job_dir = Path(job.report_path).parent
    pipelines_dir = job_dir / "pipelines"

    def _file_response(path: Path) -> FileResponse:
        # 预览接口必须 inline 展示，避免浏览器触发“下载”
        return FileResponse(
            str(path),
            media_type="text/html",
            headers={
                "Content-Disposition": "inline",
                "Cache-Control": "no-store",
            },
        )

    # 指定了 pipeline_id：直接返回
    if pipeline_id is not None:
        candidate = pipelines_dir / str(pipeline_id) / "report.html"
        if not candidate.exists():
            raise HTTPException(status_code=404, detail="指定管线报告不存在")
        return _file_response(candidate)

    # 无 pipelines 目录：按单管线处理（job.report_path 就是 report.html）
    if not pipelines_dir.exists():
        return _file_response(Path(job.report_path))

    # 多管线：优先按 job.pipeline_ids 顺序取第一个存在的 report.html
    ordered = [str(pid) for pid in (job.pipeline_ids or [])]
    checked: set[str] = set()
    for pid in ordered:
        checked.add(pid)
        candidate = pipelines_dir / pid / "report.html"
        if candidate.exists():
            return _file_response(candidate)

    # 回退：按目录名排序取第一个
    pipeline_dirs = sorted([p for p in pipelines_dir.iterdir() if p.is_dir()], key=lambda p: p.name)
    for pdir in pipeline_dirs:
        if pdir.name in checked:
            continue
        candidate = pdir / "report.html"
        if candidate.exists():
            return _file_response(candidate)

    # 实在没有就返回索引页（至少存在）
    return _file_response(Path(job.report_path))


@app.get("/api/jobs/{job_id}/raw-data")
async def get_job_raw_data(job_id: str, db: Session = Depends(get_db)):
    """下载原始数据文件"""
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    if not job.raw_data_path or not Path(job.raw_data_path).exists():
        raise HTTPException(status_code=404, detail="原始数据文件不存在")

    return FileResponse(
        job.raw_data_path,
        media_type="application/octet-stream",
        filename=f"raw_data_{job_id}{Path(job.raw_data_path).suffix}",
    )


# ==================== 用户端 UI 路由 ====================


@app.get("/", response_class=HTMLResponse)
async def ui_index():
    """首页 - 任务列表"""
    return RedirectResponse(url="/tasks")


@app.get("/create", response_class=HTMLResponse)
async def ui_create(request: Request):
    """创建任务页"""
    return templates.TemplateResponse(
        "user/user-create-task.html",
        {"request": request, "config": config},
    )


@app.get("/tasks", response_class=HTMLResponse)
async def ui_task_list(request: Request, db: Session = Depends(get_db)):
    """任务列表页"""
    query = db.query(Job)
    total = query.count()
    jobs = query.order_by(Job.created_at.desc()).limit(50).all()
    return templates.TemplateResponse(
        "user/user-task-list.html",
        {"request": request, "jobs": jobs, "total": total},
    )


@app.get("/tasks/{job_id}", response_class=HTMLResponse)
async def ui_task_detail(job_id: str, request: Request, db: Session = Depends(get_db)):
    """任务详情页"""
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")

    return templates.TemplateResponse(
        "user/user-task-detail.html",
        {"request": request, "job": job},
    )


# ==================== 管理后台 UI ====================


@app.get("/admin", response_class=HTMLResponse)
async def ui_admin_index(request: Request, db: Session = Depends(get_db)):
    """管理后台首页 - 任务监控"""
    jobs = db.query(Job).order_by(Job.created_at.desc()).limit(50).all()
    return templates.TemplateResponse(
        "admin/admin-task-monitoring.html",
        {"request": request, "jobs": jobs},
    )


@app.get("/admin/users", response_class=HTMLResponse)
async def ui_admin_users(request: Request, db: Session = Depends(get_db)):
    """管理后台 - 用户管理"""
    users = db.query(User).all()
    return templates.TemplateResponse(
        "admin/admin-user-management.html",
        {"request": request, "users": users},
    )


@app.get("/admin/config", response_class=HTMLResponse)
async def ui_admin_config(request: Request, db: Session = Depends(get_db)):
    """管理后台 - 客户端配置"""
    configs = db.query(ClientConfig).all()
    return templates.TemplateResponse(
        "admin/admin-client-config.html",
        {"request": request, "configs": configs},
    )


@app.get("/admin/pipelines", response_class=HTMLResponse)
async def ui_admin_pipelines(request: Request, db: Session = Depends(get_db)):
    """管理后台 - 流程管理"""
    pipelines = db.query(Pipeline).all()
    return templates.TemplateResponse(
        "admin/admin-pipeline-management.html",
        {"request": request, "pipelines": pipelines},
    )


@app.get("/admin/scripts", response_class=HTMLResponse)
async def ui_admin_scripts(request: Request, db: Session = Depends(get_db)):
    """管理后台 - 脚本编辑器"""
    scripts = db.query(Script).all()
    return templates.TemplateResponse(
        "admin/admin-script-editor.html",
        {"request": request, "scripts": scripts},
    )


# ==================== 启动事件 ====================


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    # 初始化默认管理员账户
    engine = get_engine(config)
    from src.db import get_db_session

    with get_db_session(engine) as db:
        init_default_admin(db, config)
        init_default_admin_assets(db)


# ==================== 启动函数 ====================


def start_server():
    """启动服务器（用于 pyproject.toml 脚本）"""
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=config.server_host,
        port=config.server_port,
        reload=True,
        log_level=config.server_log_level,
    )


if __name__ == "__main__":
    start_server()
