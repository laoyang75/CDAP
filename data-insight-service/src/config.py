"""
Configuration loader with layered support (YAML < ENV < CLI).

Supports:
- Loading from config.yaml
- Environment variable overrides (DIS_<SECTION>_<KEY>)
- Validation against JSON Schema
- Nested configuration access
"""

import os
import yaml
import json
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseSettings, Field, validator


def flatten_dict(d: dict, parent_key: str = "", sep: str = "_") -> dict:
    """
    Recursively flatten nested dictionary.

    Example:
        {"api": {"port": 8000}} -> {"api_port": 8000}
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: dict, sep: str = "_") -> dict:
    """
    Unflatten dictionary (reverse of flatten_dict).

    Example:
        {"api_port": 8000} -> {"api": {"port": 8000}}
    """
    result = {}
    for key, value in d.items():
        parts = key.split(sep)
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result


class Config(BaseSettings):
    """
    Configuration class using Pydantic BaseSettings.

    Automatically loads from:
    1. config.yaml (default)
    2. Environment variables (DIS_* prefix)
    3. CLI arguments (passed as kwargs)

    Priority: CLI > ENV > YAML
    """

    class Config:
        env_prefix = "DIS_"  # Environment variables must start with DIS_
        env_nested_delimiter = "__"  # Use __ for nested fields (e.g., DIS_API__PORT)

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False
    api_workers: int = 1

    # Database Configuration
    database_url: str = "sqlite:///./jobs.db"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_echo: bool = False

    # Worker Configuration
    worker_poll_interval: int = 5
    worker_concurrency: int = 1  # MUST be 1 (Override O3)
    worker_timeouts_fetching: int = 1200
    worker_timeouts_preprocessing: int = 600
    worker_timeouts_analyzing: int = 1800
    worker_timeouts_reporting: int = 300
    worker_retries_fetching_max_attempts: int = 3
    worker_retries_preprocessing_max_attempts: int = 1
    worker_retries_reporting_max_attempts: int = 2

    # Storage Configuration
    storage_type: str = "local"
    storage_base_path: str = "./jobs"
    storage_retention_bundle_days: int = 30
    storage_retention_raw_days: int = 7
    storage_retention_cleanup_enabled: bool = False

    # Skills Configuration
    skills_plugins_dir: str = "./analysis_skills/plugins"
    skills_default_enabled: list = Field(default_factory=lambda: ["basic_stats"])
    skills_execution_mode: str = "inline"  # inline | subprocess
    skills_execution_parallel: bool = False  # MUST be False
    skills_default_timeout: int = 600

    # Logging Configuration
    logging_level: str = "INFO"
    logging_format: str = "json"
    logging_file_enabled: bool = True
    logging_file_path: str = "./logs/app.log"
    logging_file_rotation: str = "10 MB"
    logging_file_retention: str = "30 days"
    logging_redact_fields: list = Field(
        default_factory=lambda: ["cdid", "imei", "oaid", "idfa", "android_id"]
    )

    # Upstream API Configuration
    upstream_base_url: str = "http://172.17.129.204:6829"
    upstream_endpoints_create_task: str = "/api/statistical-analysis/v1/task/create"
    upstream_endpoints_query_task: str = "/api/statistical-analysis/v1/task/query"
    upstream_endpoints_download: str = "/api/statistical-analysis/v1/task/download"
    upstream_timeout: int = 30
    upstream_retries: int = 3

    # Report Configuration
    report_llm_enabled: bool = False
    report_llm_provider: str = "openai"
    report_llm_model: str = "gpt-4"
    report_llm_api_key: str = ""
    report_template_dir: str = "./src/worker/stages/templates"

    # Web UI Configuration
    ui_enabled: bool = True
    ui_title: str = "Data Insight Service"
    ui_page_size: int = 20
    ui_poll_interval: int = 3000

    # Testing Configuration
    testing_simulate_error_enabled: bool = False
    testing_simulate_error_stage: str = "analyzing"
    testing_simulate_error_error_code: str = "SKILL_FAILED"
    testing_simulate_error_probability: float = 0.5

    @validator("worker_concurrency")
    def validate_concurrency(cls, v):
        """Enforce concurrency=1 (Override O3)"""
        if v != 1:
            raise ValueError("worker_concurrency MUST be 1 (single-threaded FIFO)")
        return v

    @validator("skills_execution_parallel")
    def validate_parallel(cls, v):
        """Enforce parallel=False (Override O3)"""
        if v is True:
            raise ValueError("skills_execution_parallel MUST be False")
        return v

    @classmethod
    def load_from_yaml(cls, config_path: Optional[str] = None) -> "Config":
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config.yaml (default: config/config.yaml)

        Returns:
            Config instance with merged YAML + ENV values
        """
        if config_path is None:
            config_path = os.getenv("DIS_CONFIG_PATH", "config/config.yaml")

        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_file) as f:
            yaml_config = yaml.safe_load(f)

        # Flatten nested YAML (convert {"api": {"port": 8000}} to {"api_port": 8000})
        flat_config = flatten_dict(yaml_config)

        # Pydantic BaseSettings automatically merges with environment variables
        return cls(**flat_config)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to nested dictionary (for display)"""
        flat = self.dict()
        return unflatten_dict(flat)

    def to_yaml(self) -> str:
        """Convert config to YAML string"""
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    def to_json(self) -> str:
        """Convert config to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    def validate_schema(self, schema_path: str = "config/config.schema.json"):
        """
        Validate configuration against JSON Schema.

        Args:
            schema_path: Path to JSON Schema file

        Raises:
            jsonschema.ValidationError if invalid
        """
        try:
            from jsonschema import validate
        except ImportError:
            raise ImportError("Please install jsonschema: pip install jsonschema")

        with open(schema_path) as f:
            schema = json.load(f)

        config_dict = self.to_dict()
        validate(instance=config_dict, schema=schema)


# Global config instance
_config: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """
    Get global config instance (singleton).

    Args:
        reload: Force reload from file

    Returns:
        Config instance
    """
    global _config
    if _config is None or reload:
        _config = Config.load_from_yaml()
    return _config


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration (alias for Config.load_from_yaml).

    Args:
        config_path: Path to config.yaml

    Returns:
        Config instance
    """
    return Config.load_from_yaml(config_path)


# Example usage:
if __name__ == "__main__":
    # Load config
    config = load_config()

    # Print config
    print("=== Configuration ===")
    print(config.to_yaml())

    # Access values
    print(f"\nAPI Server: {config.api_host}:{config.api_port}")
    print(f"Database: {config.database_url}")
    print(f"Worker Poll Interval: {config.worker_poll_interval}s")

    # Validate against schema
    try:
        config.validate_schema()
        print("\nConfiguration is valid ✓")
    except Exception as e:
        print(f"\nConfiguration validation failed: {e}")
