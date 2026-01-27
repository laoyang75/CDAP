"""数据库模型定义

定义所有 SQLAlchemy ORM 模型
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Job(Base):
    """任务模型"""

    __tablename__ = "jobs"

    id = Column(String(26), primary_key=True)  # ULID
    name = Column(String(255), nullable=False)
    package_name = Column(String(255), nullable=False)
    start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=False)
    message_types = Column(JSON, nullable=False)  # ["dna", "daa"]
    pipeline_ids = Column(JSON)  # [pipeline_id, ...]

    status = Column(String(20), nullable=False, default="queued", index=True)
    # 状态值: queued, fetching_data, analyzing, generating_report, completed, failed
    progress = Column(Integer, default=0)
    progress_message = Column(String(255), default="")

    input_file_path = Column(String(500))
    raw_data_path = Column(String(500))
    report_path = Column(String(500))

    error = Column(Text)
    insight_task_id = Column(String(50))

    # 运行态信息（用于后台“终止卡住进程/取消任务”）
    cancel_requested = Column(Boolean, default=False)
    active_pid = Column(Integer)  # 当前正在运行的外部进程 PID（如 gemini）
    active_step = Column(String(50))  # fetching/analyzing/generating_report 等
    active_started_at = Column(DateTime)

    # 调试模式：用户直接上传已下载好的 raw_data.xlsx，跳过内网拉取与下载
    debug_mode = Column(Boolean, default=False)

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class User(Base):
    """用户模型（管理端）"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100))
    role = Column(String(20), default="user")  # user | admin
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_login = Column(DateTime)


class Pipeline(Base):
    """流程配置模型（管理端）"""

    __tablename__ = "pipelines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    config = Column(JSON)  # 流程配置（分析步骤、参数等）
    # 示例: {"steps": ["fetch", "analyze", "report"], "analyzer": "duofa", "threshold": 2.0}
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )


class Script(Base):
    """自定义脚本模型（管理端）"""

    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    script_type = Column(String(20))  # preprocessing | analysis | postprocessing
    code = Column(Text, nullable=False)  # Python 代码
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ClientConfig(Base):
    """客户端配置模型（管理端）"""

    __tablename__ = "client_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text)
    description = Column(String(255))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
