"""数据库连接管理

提供数据库初始化和会话管理功能
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.config import Config
from src.db.models import Base


def init_db(config: Config) -> Engine:
    """初始化数据库

    Args:
        config: 配置对象

    Returns:
        Engine: SQLAlchemy Engine 对象
    """
    url = make_url(config.database_url)

    engine_kwargs: dict = {"echo": config.database_echo}

    # SQLite 需要特殊处理：
    # - 内存库默认使用 SingletonThreadPool，不支持 max_overflow 等参数
    # - FastAPI 常见场景涉及多线程，建议关闭 check_same_thread
    if url.get_backend_name() == "sqlite":
        engine_kwargs["connect_args"] = {"check_same_thread": False}

        if url.database in (None, "", ":memory:"):
            # 使用 StaticPool 保证内存库在同一进程内可复用同一连接
            engine_kwargs["poolclass"] = StaticPool
        else:
            engine_kwargs["pool_size"] = config.database_pool_size
            engine_kwargs["max_overflow"] = config.database_max_overflow
    else:
        engine_kwargs["pool_size"] = config.database_pool_size
        engine_kwargs["max_overflow"] = config.database_max_overflow

    engine = create_engine(config.database_url, **engine_kwargs)

    # 创建所有表
    Base.metadata.create_all(engine)

    # 轻量级 SQLite schema migration（开发环境）
    if url.get_backend_name() == "sqlite":
        _migrate_sqlite_schema(engine)

    return engine


def _migrate_sqlite_schema(engine: Engine) -> None:
    """SQLite 轻量级 schema 迁移（仅补充新增列，不做复杂变更）"""
    with engine.begin() as conn:
        tables = {
            row[0]
            for row in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
        }

        if "jobs" in tables:
            columns = {
                row[1]
                for row in conn.execute(text("PRAGMA table_info(jobs)")).fetchall()
            }
            if "pipeline_ids" not in columns:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN pipeline_ids JSON"))
            if "cancel_requested" not in columns:
                conn.execute(
                    text(
                        "ALTER TABLE jobs ADD COLUMN cancel_requested BOOLEAN DEFAULT 0"
                    )
                )
            if "active_pid" not in columns:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN active_pid INTEGER"))
            if "active_step" not in columns:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN active_step VARCHAR(50)"))
            if "active_started_at" not in columns:
                conn.execute(text("ALTER TABLE jobs ADD COLUMN active_started_at DATETIME"))
            if "debug_mode" not in columns:
                conn.execute(
                    text("ALTER TABLE jobs ADD COLUMN debug_mode BOOLEAN DEFAULT 0")
                )


def get_session(engine: Engine) -> Session:
    """获取数据库会话

    Args:
        engine: SQLAlchemy Engine 对象

    Returns:
        Session: 数据库会话对象
    """
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()


@contextmanager
def get_db_session(engine: Engine) -> Generator[Session, None, None]:
    """获取数据库会话（上下文管理器）

    使用示例:
        with get_db_session(engine) as session:
            job = session.query(Job).first()

    Args:
        engine: SQLAlchemy Engine 对象

    Yields:
        Session: 数据库会话对象
    """
    session = get_session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# 全局 Engine 实例
_engine: Engine = None


def get_engine(config: Config = None) -> Engine:
    """获取全局 Engine 实例

    Args:
        config: 配置对象（首次调用时需要提供）

    Returns:
        Engine: SQLAlchemy Engine 对象
    """
    global _engine
    if _engine is None:
        if config is None:
            from src.config import get_config

            config = get_config()
        _engine = init_db(config)
    return _engine


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖注入函数

    使用示例:
        @app.get("/jobs")
        def list_jobs(db: Session = Depends(get_db)):
            return db.query(Job).all()

    Yields:
        Session: 数据库会话对象
    """
    engine = get_engine()
    with get_db_session(engine) as session:
        yield session
