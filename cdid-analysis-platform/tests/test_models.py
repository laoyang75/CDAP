"""数据库模型测试"""

import pytest
from datetime import datetime, timezone

from src.config import Config
from src.db import init_db, get_session, Job


def test_job_model():
    """测试 Job 模型"""
    config = Config(database_url="sqlite:///:memory:")
    engine = init_db(config)
    session = get_session(engine)

    # 创建任务
    job = Job(
        id="test_job_123",
        name="测试任务",
        package_name="com.test",
        start_date="2026-01-01",
        end_date="2026-01-07",
        message_types=["dna"],
        status="queued",
    )

    session.add(job)
    session.commit()

    # 查询任务
    fetched = session.query(Job).filter_by(id="test_job_123").first()

    assert fetched is not None
    assert fetched.name == "测试任务"
    assert fetched.status == "queued"
    assert fetched.message_types == ["dna"]

    session.close()
