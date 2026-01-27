"""配置加载模块

支持从 YAML 文件加载配置，并允许环境变量覆盖。
"""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """应用配置类"""

    # 管理端配置
    admin_enabled: bool = Field(default=True, description="是否启用管理端")
    admin_secret_key: str = Field(
        default="change-me-in-production", description="JWT 密钥"
    )
    admin_jwt_expire_hours: int = Field(default=24, description="JWT 过期时间（小时）")
    admin_default_username: str = Field(default="admin", description="默认管理员用户名")
    admin_default_password: str = Field(default="admin123", description="默认管理员密码")

    # Gemini CLI 配置
    gemini_cli_path: str = Field(default="gemini", description="Gemini CLI 路径")
    gemini_skill_name: str = Field(default="duofa-panduan", description="Gemini Skill 名称")
    gemini_skill_path: str = Field(
        default="~/.gemini/skills/duofa-panduan/SKILL.md",
        description="Gemini Skill 文件路径",
    )
    gemini_timeout: int = Field(default=300, description="Gemini CLI 超时时间（秒）")
    gemini_version: str = Field(default="0.25.2", description="Gemini CLI 版本")
    gemini_model: Optional[str] = Field(
        default=None, description="Gemini CLI 模型（对应 gemini -m）"
    )
    gemini_fallback_models: list[str] = Field(
        default=["gemini-2.0-flash"],
        description="当主模型不可用时的备用模型列表",
    )

    # 多发检测阈值
    duofa_threshold: float = Field(default=2.0, description="多发检测阈值")

    # 上游内网 API 配置
    upstream_base_url: str = Field(
        default="http://172.17.129.204:6829", description="内网 API 基础 URL"
    )
    upstream_create_task_endpoint: str = Field(
        default="/api/statistical-analysis/v1/task/create",
        description="创建任务端点",
    )
    upstream_get_task_endpoint: str = Field(
        default="/api/statistical-analysis/v1/task/detail",
        description="查询任务端点",
    )
    upstream_timeout: int = Field(default=30, description="API 请求超时时间（秒）")
    upstream_retry_times: int = Field(default=3, description="API 重试次数")
    upstream_retry_interval: int = Field(default=5, description="API 重试间隔（秒）")

    # Worker 配置
    worker_poll_interval: int = Field(default=10, description="轮询间隔（秒）")
    worker_max_concurrent_jobs: int = Field(default=1, description="最大并发任务数")
    worker_job_timeout: int = Field(default=1800, description="任务超时时间（秒）")
    worker_cleanup_days: int = Field(default=7, description="清理旧任务天数")

    # 数据库配置
    database_url: str = Field(default="sqlite:///./jobs.db", description="数据库 URL")
    database_echo: bool = Field(default=False, description="是否打印 SQL 日志")
    database_pool_size: int = Field(default=5, description="连接池大小")
    database_max_overflow: int = Field(default=10, description="连接池最大溢出")

    # 服务器配置
    server_host: str = Field(default="0.0.0.0", description="服务器监听地址")
    server_port: int = Field(default=8000, description="服务器监听端口")
    server_workers: int = Field(default=1, description="工作进程数")
    server_log_level: str = Field(default="info", description="日志级别")

    # 文件存储配置
    storage_upload_dir: str = Field(default="./jobs/uploads", description="上传目录")
    storage_output_dir: str = Field(default="./jobs/outputs", description="输出目录")
    storage_max_file_size: int = Field(
        default=52428800, description="最大文件大小（字节）"
    )  # 50MB
    storage_allowed_extensions: list[str] = Field(
        default=[".xlsx", ".xls", ".csv"], description="允许的文件扩展名"
    )

    # 日志配置
    logging_level: str = Field(default="INFO", description="日志级别")
    logging_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式",
    )
    logging_file: str = Field(default="./logs/app.log", description="日志文件路径")
    logging_max_bytes: int = Field(default=10485760, description="日志文件最大大小")
    logging_backup_count: int = Field(default=5, description="日志文件备份数量")

    model_config = SettingsConfigDict(
        env_prefix="CDID_",  # 环境变量前缀
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


def load_config(config_file: Optional[str] = None) -> Config:
    """加载配置

    优先级：环境变量 > YAML 文件 > 默认值

    Args:
        config_file: YAML 配置文件路径，默认为 config/config.yaml

    Returns:
        Config: 配置对象
    """
    if config_file is None:
        config_file = os.getenv("CDID_CONFIG_FILE", "config/config.yaml")

    config_path = Path(config_file)
    yaml_config = {}

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)

        # 扁平化 YAML 配置（处理嵌套结构）
        for section, values in raw_config.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    # 转换为 pydantic 字段名格式：section_key
                    field_name = f"{section}_{key}"
                    yaml_config[field_name] = value

    base_config = Config()
    env_overrides = base_config.model_fields_set
    yaml_overrides = {k: v for k, v in yaml_config.items() if k not in env_overrides}
    return base_config.model_copy(update=yaml_overrides)


# 全局配置实例
config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例"""
    global config
    if config is None:
        config = load_config()
    return config
