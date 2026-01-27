# 配置体系文档（CONFIG.md）

**项目**：Data Insight Service (Python Skills)
**版本**：0.1.0
**最后更新**：2026-01-23

---

## 1. 概述

本系统采用**分层配置体系**，支持三种配置源（按优先级从低到高）：

```
默认配置文件 (config.yaml)
       ↓
   环境变量 (ENV)
       ↓
   命令行参数 (CLI)
```

**核心原则**：
- **默认值优先**：开箱即用，无需配置即可运行 MVP
- **环境变量友好**：支持容器化部署（Docker/K8s）
- **CLI 覆盖**：方便调试与临时调整

---

## 2. 配置文件（config.yaml）

### 2.1 位置

**默认路径**：
- `config/config.yaml`（项目根目录）
- 可通过环境变量覆盖：`export DIS_CONFIG_PATH=/custom/path/config.yaml`

### 2.2 结构（完整示例）

```yaml
# Data Insight Service - 默认配置
version: "0.1.0"

# API Server 配置
api:
  host: "0.0.0.0"
  port: 8000
  reload: false  # 开发时设为 true
  workers: 1     # Uvicorn worker 数（生产环境可增加）

# 数据库配置
database:
  # MVP: SQLite（单文件数据库）
  url: "sqlite:///./jobs.db"
  # 后续可迁移：
  # url: "postgresql://user:pass@localhost:5432/data_insight"
  pool_size: 5
  max_overflow: 10
  echo: false  # 设为 true 可查看 SQL 日志

# Worker 配置
worker:
  # 轮询间隔（秒）：无任务时休眠时长
  poll_interval: 5

  # 单线程 FIFO（Override O3）
  concurrency: 1  # 固定为 1，禁止修改

  # 阶段超时（秒）
  timeouts:
    fetching: 1200       # 20 分钟
    preprocessing: 600   # 10 分钟
    analyzing: 1800      # 30 分钟（或按 skill 累加）
    reporting: 300       # 5 分钟

  # 重试策略
  retries:
    fetching:
      max_attempts: 3
      backoff: [1, 4, 16]  # 指数退避（秒）
    preprocessing:
      max_attempts: 1  # 不重试（除非 IO 错误）
    reporting:
      max_attempts: 2

# 存储配置
storage:
  # MVP: 本地文件系统
  type: "local"
  base_path: "./jobs"  # Job 工作目录根路径
  # 后续可扩展：
  # type: "s3"
  # bucket: "data-insight-jobs"

  # 留存策略（Phase 2+ 实现）
  retention:
    bundle_days: 30      # bundle.zip 保留 30 天
    raw_days: 7          # raw 数据保留 7 天
    cleanup_enabled: false  # MVP 禁用自动清理

# Skills 配置
skills:
  # Skills 插件目录
  plugins_dir: "./analysis_skills/plugins"

  # 默认启用的 skills（可在 Job params 中覆盖）
  default_enabled:
    - basic_stats

  # Skills 执行模式
  execution:
    mode: "subprocess"  # subprocess | inline（Phase 0 使用 inline）
    parallel: false     # 固定为 false（Override O3）

  # 超时默认值（可被 manifest.yaml 覆盖）
  default_timeout: 600  # 10 分钟

# 日志配置
logging:
  level: "INFO"  # DEBUG | INFO | WARNING | ERROR
  format: "json"  # json | text
  file:
    enabled: true
    path: "./logs/app.log"
    rotation: "10 MB"  # 日志轮转大小
    retention: "30 days"

  # 敏感信息脱敏（Phase 1+ 实现）
  redact_fields:
    - cdid
    - imei
    - oaid
    - idfa

# 上游 API 配置（fetching 阶段使用）
upstream:
  base_url: "http://172.17.129.204:6829"
  endpoints:
    create_task: "/api/statistical-analysis/v1/task/create"
    query_task: "/api/statistical-analysis/v1/task/query"
    download: "/api/statistical-analysis/v1/task/download"
  timeout: 30  # 请求超时（秒）
  retries: 3

# 报告配置
report:
  # LLM 增强（Phase 3+ 实现）
  llm:
    enabled: false
    provider: "openai"  # openai | anthropic
    model: "gpt-4"
    api_key: "${LLM_API_KEY}"  # 从环境变量读取

  # 模板配置
  template_dir: "./src/worker/stages/templates"

# Web UI 配置
ui:
  enabled: true
  title: "Data Insight Service"
  page_size: 20  # 任务列表分页大小
  poll_interval: 3000  # 前端轮询间隔（毫秒）

# 测试与调试
testing:
  # 模拟错误（用于测试失败场景）
  simulate_error:
    enabled: false
    stage: "analyzing"  # queued | fetching | preprocessing | analyzing | reporting
    error_code: "SKILL_FAILED"
    probability: 0.5  # 0.0 - 1.0
```

---

## 3. 环境变量覆盖

### 3.1 命名规则

```
DIS_<SECTION>_<KEY>=<VALUE>
```

**示例**：
```bash
export DIS_API_PORT=9000
export DIS_DATABASE_URL="postgresql://user:pass@localhost/db"
export DIS_WORKER_POLL_INTERVAL=10
export DIS_LOGGING_LEVEL="DEBUG"
```

### 3.2 嵌套字段

使用双下划线 `__` 表示嵌套：

```bash
export DIS_WORKER__TIMEOUTS__FETCHING=600
export DIS_UPSTREAM__BASE_URL="http://192.168.1.100:8080"
```

### 3.3 特殊变量

| 变量名 | 说明 |
|--------|------|
| `DIS_CONFIG_PATH` | 指定配置文件路径 |
| `DIS_ENV` | 环境标识（dev/test/prod） |
| `DATABASE_URL` | 数据库连接（简写，等价于 DIS_DATABASE_URL） |
| `LLM_API_KEY` | LLM API Key（敏感信息） |

---

## 4. 命令行参数覆盖

### 4.1 API Server 启动

```bash
insight-cli server start \
  --host 0.0.0.0 \
  --port 9000 \
  --reload \
  --log-level DEBUG
```

### 4.2 Worker 启动

```bash
insight-cli worker start \
  --poll-interval 10 \
  --timeout-fetching 600 \
  --log-level INFO
```

### 4.3 优先级示例

```bash
# config.yaml: port = 8000
# ENV: DIS_API_PORT = 9000
# CLI: --port 8080

# 最终生效：8080（CLI 最高优先级）
```

---

## 5. 配置加载流程

### 5.1 Python 实现（src/config.py）

```python
from pathlib import Path
import os
import yaml
from pydantic import BaseSettings

class Config(BaseSettings):
    """配置类（Pydantic BaseSettings 自动支持环境变量）"""

    class Config:
        env_prefix = "DIS_"
        env_nested_delimiter = "__"

    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # 数据库配置
    database_url: str = "sqlite:///./jobs.db"

    # Worker 配置
    worker_poll_interval: int = 5
    worker_concurrency: int = 1  # 固定

    # ... 更多字段

    @classmethod
    def load(cls, config_path: str = None):
        """加载配置（yaml + env）"""
        # 1. 加载 YAML
        if config_path is None:
            config_path = os.getenv("DIS_CONFIG_PATH", "config/config.yaml")

        with open(config_path) as f:
            yaml_config = yaml.safe_load(f)

        # 2. 扁平化（支持嵌套）
        flat_config = flatten_dict(yaml_config)

        # 3. Pydantic 自动合并环境变量
        return cls(**flat_config)

def flatten_dict(d, parent_key="", sep="_"):
    """递归扁平化字典"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
```

### 5.2 使用示例

```python
from src.config import Config

# 加载配置
config = Config.load()

print(config.api_port)  # 8000 或环境变量覆盖后的值
print(config.database_url)
```

---

## 6. 配置验证

### 6.1 JSON Schema 验证（config.schema.json）

**位置**：`config/config.schema.json`

**用途**：
- 验证 `config.yaml` 格式正确性
- IDE 自动补全与提示

**验证命令**：
```bash
# 使用 jsonschema CLI 验证
jsonschema -i config/config.yaml config/config.schema.json
```

### 6.2 启动时验证

```python
from jsonschema import validate

with open("config/config.yaml") as f:
    config = yaml.safe_load(f)

with open("config/config.schema.json") as f:
    schema = json.load(f)

validate(instance=config, schema=schema)  # 抛出异常如果不合法
```

---

## 7. 不同环境的配置策略

### 7.1 开发环境（dev）

**特点**：
- 开启热重载（reload=true）
- 详细日志（level=DEBUG）
- 模拟错误开关（测试失败场景）

**配置方式**：
```bash
export DIS_ENV=dev
export DIS_API_RELOAD=true
export DIS_LOGGING_LEVEL=DEBUG
```

或创建 `config/config.dev.yaml`：
```yaml
api:
  reload: true
logging:
  level: DEBUG
testing:
  simulate_error:
    enabled: true
```

### 7.2 测试环境（test）

**特点**：
- 使用内存数据库（SQLite `:memory:`）
- 关闭外部依赖（上游 API mock）
- 快速超时（测试速度）

**pytest 配置**（`tests/conftest.py`）：
```python
@pytest.fixture
def test_config():
    return Config(
        database_url="sqlite:///:memory:",
        worker_poll_interval=0.1,
        worker_timeouts_fetching=5,
    )
```

### 7.3 生产环境（prod）

**特点**：
- PostgreSQL 数据库
- 多 Uvicorn workers
- 日志轮转 + 留存
- 关闭 reload 与 debug

**配置方式**（环境变量）：
```bash
export DIS_ENV=prod
export DIS_DATABASE_URL="postgresql://..."
export DIS_API_WORKERS=4
export DIS_API_RELOAD=false
export DIS_LOGGING_LEVEL=INFO
export DIS_STORAGE_RETENTION_CLEANUP_ENABLED=true
```

---

## 8. 敏感信息处理

### 8.1 不应写入 config.yaml 的内容

- 数据库密码
- LLM API Key
- 上游 API Token

### 8.2 推荐方式

**1. 环境变量**（最推荐）：
```bash
export DIS_DATABASE_URL="postgresql://user:${DB_PASSWORD}@localhost/db"
export LLM_API_KEY="sk-..."
```

**2. `.env` 文件**（开发环境）：
```bash
# .env（加入 .gitignore）
DIS_DATABASE_URL=postgresql://...
LLM_API_KEY=sk-...
```

加载 `.env`：
```python
from dotenv import load_dotenv
load_dotenv()  # 自动加载到环境变量
```

**3. Secrets Management**（生产环境）：
- Docker Secrets
- Kubernetes Secrets
- HashiCorp Vault

---

## 9. 配置热更新（Phase 2+ 可选）

**目标**：无需重启即可更新部分配置（如日志级别、超时时间）

**实现思路**：
```python
import signal

class ConfigManager:
    def __init__(self):
        self.config = Config.load()
        signal.signal(signal.SIGHUP, self.reload)

    def reload(self, signum, frame):
        """收到 SIGHUP 信号时重新加载配置"""
        self.config = Config.load()
        logger.info("Configuration reloaded")
```

**使用**：
```bash
# 发送信号触发重新加载
kill -HUP <pid>
```

---

## 10. 配置示例（不同场景）

### 10.1 最小启动（默认配置）

```bash
# 无需任何配置，直接启动
insight-cli server start
```

### 10.2 自定义端口

```bash
insight-cli server start --port 9000
# 或
export DIS_API_PORT=9000
insight-cli server start
```

### 10.3 使用 PostgreSQL

```bash
export DIS_DATABASE_URL="postgresql://user:pass@localhost:5432/data_insight"
insight-cli server start
```

### 10.4 调试模式

```bash
export DIS_LOGGING_LEVEL=DEBUG
export DIS_API_RELOAD=true
insight-cli server start
```

### 10.5 生产部署（Docker）

```dockerfile
# Dockerfile
ENV DIS_API_HOST=0.0.0.0
ENV DIS_API_PORT=8000
ENV DIS_DATABASE_URL=postgresql://...
ENV DIS_LOGGING_LEVEL=INFO
```

---

## 11. 配置文件位置汇总

| 文件 | 路径 | 用途 |
|------|------|------|
| 默认配置 | `config/config.yaml` | 主配置文件 |
| JSON Schema | `config/config.schema.json` | 验证与补全 |
| 环境特定配置 | `config/config.{env}.yaml` | 可选（dev/test/prod） |
| 环境变量 | `.env` | 开发环境敏感信息 |
| 配置加载器 | `src/config.py` | Python 实现 |

---

## 12. 常见问题

### Q1: 如何查看当前生效的配置？

```bash
insight-cli config show  # 显示合并后的最终配置
```

### Q2: 如何验证配置文件格式？

```bash
insight-cli config validate
# 或
jsonschema -i config/config.yaml config/config.schema.json
```

### Q3: 配置优先级如何验证？

```bash
# 1. 查看默认配置
cat config/config.yaml

# 2. 设置环境变量
export DIS_API_PORT=9000

# 3. 启动时传参
insight-cli server start --port 8080

# 结果：8080（CLI > ENV > YAML）
```

### Q4: 如何在代码中访问配置？

```python
from src.config import Config

config = Config.load()
print(config.api_port)  # 访问配置项
```

---

## 13. 总结

本配置体系具备以下特点：

1. **分层设计**：YAML < ENV < CLI
2. **开箱即用**：默认配置即可运行 MVP
3. **环境友好**：支持容器化部署
4. **类型安全**：Pydantic 验证
5. **可扩展**：易于添加新配置项

**Phase 0 实现**：
- ✅ `config/config.yaml`（完整默认配置）
- ✅ `config/config.schema.json`（JSON Schema 验证）
- ✅ `src/config.py`（配置加载器）
- ✅ 环境变量支持（Pydantic BaseSettings）
- ⏸ CLI 参数支持（通过 Click 传参）

**后续增强**：
- 配置热更新（SIGHUP 信号）
- 配置审计日志（记录配置变更）
- 配置加密（敏感字段）
