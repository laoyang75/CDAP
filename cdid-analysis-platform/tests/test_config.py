"""配置测试"""

import pytest
from src.config import load_config


def test_load_config():
    """测试配置加载"""
    config = load_config("config/config.yaml")

    assert config is not None
    assert config.admin_enabled is True
    assert config.gemini_cli_path == "gemini"
    assert config.duofa_threshold == 2.0
