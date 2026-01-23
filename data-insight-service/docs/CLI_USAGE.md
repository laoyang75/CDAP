# CLI 使用文档（CLI_USAGE.md）

**项目**：Data Insight Service (Python Skills)
**版本**：0.1.0
**最后更新**：2026-01-23

---

## 1. 概述

`insight-cli` 是 Data Insight Service 的命令行管理工具，提供任务管理、Worker 控制、服务启动等功能。

**技术栈**：Click（Python CLI 框架）

---

## 2. 安装与配置

### 2.1 安装

```bash
# 方式 1：开发模式（推荐本地开发）
cd data-insight-service
pip install -e .

# 方式 2：生产安装
pip install data-insight-service

# 验证安装
insight-cli --version
```

### 2.2 配置

CLI 工具读取配置文件（`config/config.yaml`）和环境变量（见 `CONFIG.md`）。

**指定配置文件**：
```bash
export DIS_CONFIG_PATH=/custom/config.yaml
insight-cli [command]
```

---

## 3. 命令清单

### 3.1 全局选项

```bash
insight-cli [全局选项] <command> [子命令] [参数]
```

**全局选项**：

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--config PATH` | 指定配置文件路径 | `config/config.yaml` |
| `--log-level LEVEL` | 日志级别（DEBUG/INFO/WARNING/ERROR) | `INFO` |
| `--help` | 显示帮助信息 | - |
| `--version` | 显示版本号 | - |

**示例**：
```bash
insight-cli --config /etc/dis/config.yaml job list
insight-cli --log-level DEBUG worker start
```

---

## 4. 任务管理（job）

### 4.1 创建任务（job create）

**语法**：
```bash
insight-cli job create <file> --params <json_string>
insight-cli job create <file> --params-file <json_file>
```

**参数**：

| 参数/选项 | 必填 | 说明 |
|-----------|------|------|
| `<file>` | ✅ | CDID 列表文件（CSV/XLSX） |
| `--params TEXT` | ✅ | 任务参数（JSON 字符串） |
| `--params-file PATH` | ✅ | 任务参数文件（JSON） |

**示例 1：使用 JSON 字符串**：
```bash
insight-cli job create cdid_list.csv --params '{
  "package_name": "com.example.app",
  "time_range": {"start": "2026-01-01", "end": "2026-01-07"},
  "message_types": ["dna", "daa"],
  "skills": {
    "enabled": ["basic_stats"],
    "params": {"basic_stats": {}}
  },
  "report": {"format": "html", "llm": {"enabled": false}}
}'
```

**示例 2：使用参数文件**：
```bash
# job_params.json
{
  "package_name": "com.example.app",
  "time_range": {"start": "2026-01-01", "end": "2026-01-07"},
  "message_types": ["dna"],
  "skills": {"enabled": ["basic_stats"]}
}

# 创建任务
insight-cli job create cdid_list.xlsx --params-file job_params.json
```

**输出**：
```
Job created successfully!
Job ID: 01J1A2B3C4D5E6F7G8H9K0M1
Status: queued
Created at: 2026-01-23T18:00:00Z

Links:
  Status: http://localhost:8000/jobs/01J1A2B3C4D5E6F7G8H9K0M1
  Report: http://localhost:8000/jobs/01J1A2B3C4D5E6F7G8H9K0M1/report
  Bundle: http://localhost:8000/jobs/01J1A2B3C4D5E6F7G8H9K0M1/bundle
  Web UI: http://localhost:8000/ui/jobs/01J1A2B3C4D5E6F7G8H9K0M1
```

---

### 4.2 查询任务列表（job list）

**语法**：
```bash
insight-cli job list [选项]
```

**选项**：

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--status TEXT` | 按状态筛选（queued/done/failed 等） | 全部 |
| `--limit INT` | 限制返回数量 | 20 |
| `--offset INT` | 偏移量（分页） | 0 |
| `--format TEXT` | 输出格式（table/json/csv） | table |

**示例 1：查看所有任务**：
```bash
insight-cli job list
```

**输出（table 格式）**：
```
┌──────────────────────────────┬───────────────┬──────────────┬──────────────────────┬──────────────────────┐
│ Job ID                       │ Status        │ Stage        │ Created At           │ Updated At           │
├──────────────────────────────┼───────────────┼──────────────┼──────────────────────┼──────────────────────┤
│ 01J1A2B3C4D5E6F7G8H9K0M1     │ done          │ done         │ 2026-01-23T18:00:00Z │ 2026-01-23T18:05:00Z │
│ 01J1A2B3C4D5E6F7G8H9K0M2     │ analyzing     │ analyzing    │ 2026-01-23T18:10:00Z │ 2026-01-23T18:12:00Z │
│ 01J1A2B3C4D5E6F7G8H9K0M3     │ queued        │ queued       │ 2026-01-23T18:15:00Z │ 2026-01-23T18:15:00Z │
└──────────────────────────────┴───────────────┴──────────────┴──────────────────────┴──────────────────────┘
```

**示例 2：只查看失败任务**：
```bash
insight-cli job list --status failed
```

**示例 3：JSON 格式输出（便于脚本解析）**：
```bash
insight-cli job list --format json --limit 5
```

**输出（JSON）**：
```json
{
  "jobs": [
    {
      "job_id": "01J1A2B3C4D5E6F7G8H9K0M1",
      "status": "done",
      "stage": "done",
      "created_at": "2026-01-23T18:00:00Z",
      "updated_at": "2026-01-23T18:05:00Z"
    }
  ],
  "total": 1,
  "limit": 5,
  "offset": 0
}
```

---

### 4.3 查询任务详情（job get）

**语法**：
```bash
insight-cli job get <job_id> [选项]
```

**选项**：

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--format TEXT` | 输出格式（table/json/yaml） | table |
| `--watch` | 持续监控（每 3 秒刷新） | false |

**示例 1：查看任务详情**：
```bash
insight-cli job get 01J1A2B3C4D5E6F7G8H9K0M1
```

**输出**：
```
Job ID: 01J1A2B3C4D5E6F7G8H9K0M1
Status: analyzing
Stage: analyzing
Progress: 55% - running skill basic_stats

Timestamps:
  Created At: 2026-01-23T18:00:00Z
  Updated At: 2026-01-23T18:02:30Z

Parameters:
  Package Name: com.example.app
  Time Range: 2026-01-01 to 2026-01-07
  Message Types: dna, daa
  Skills: basic_stats

Artifacts:
  Report HTML: (not ready)
  Bundle ZIP: (not ready)

Error: None
```

**示例 2：监控模式（持续刷新）**：
```bash
insight-cli job get 01J1A2B3C4D5E6F7G8H9K0M1 --watch
```

**输出（每 3 秒刷新）**：
```
Job ID: 01J1A2B3C4D5E6F7G8H9K0M1
Status: reporting  ← 状态实时更新
Stage: reporting
Progress: 90% - generating HTML report

[Watching... Press Ctrl+C to stop]
```

**示例 3：JSON 格式（脚本友好）**：
```bash
insight-cli job get 01J1A2B3C4D5E6F7G8H9K0M1 --format json
```

---

### 4.4 删除任务（job delete）

**语法**：
```bash
insight-cli job delete <job_id> [选项]
```

**选项**：

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--force` | 强制删除（跳过确认） | false |
| `--cleanup` | 同时删除工作目录 | true |

**示例 1：删除任务（需确认）**：
```bash
insight-cli job delete 01J1A2B3C4D5E6F7G8H9K0M1
```

**输出**：
```
Are you sure you want to delete job 01J1A2B3C4D5E6F7G8H9K0M1? [y/N]: y
Job deleted successfully.
Work directory removed: jobs/01J1A2B3C4D5E6F7G8H9K0M1/
```

**示例 2：强制删除（脚本使用）**：
```bash
insight-cli job delete 01J1A2B3C4D5E6F7G8H9K0M1 --force
```

---

## 5. Worker 管理（worker）

### 5.1 启动 Worker（worker start）

**语法**：
```bash
insight-cli worker start [选项]
```

**选项**：

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--poll-interval INT` | 轮询间隔（秒） | 5 |
| `--daemon` | 后台运行（守护进程） | false |
| `--pid-file PATH` | PID 文件路径 | `/var/run/dis-worker.pid` |

**示例 1：前台运行（开发/调试）**：
```bash
insight-cli worker start
```

**输出**：
```
[INFO] Worker started (PID: 12345)
[INFO] Polling for jobs every 5 seconds...
[INFO] Waiting for jobs...
[INFO] Found job: 01J1A2B3C4D5E6F7G8H9K0M1 (status: queued)
[INFO] Starting job execution...
[INFO] Stage: fetching (0%)
[INFO] Stage: fetching (50%)
[INFO] Stage: fetching → preprocessing (100%)
[INFO] Stage: preprocessing (30%)
...
[INFO] Job completed: 01J1A2B3C4D5E6F7G8H9K0M1 (status: done)
[INFO] Waiting for jobs...
```

**示例 2：后台运行（生产环境）**：
```bash
insight-cli worker start --daemon --pid-file /var/run/dis-worker.pid
```

**输出**：
```
Worker started in background (PID: 12345)
PID file: /var/run/dis-worker.pid
Log file: ./logs/worker.log
```

**示例 3：自定义轮询间隔**：
```bash
insight-cli worker start --poll-interval 10  # 每 10 秒检查一次
```

---

### 5.2 停止 Worker（worker stop）

**语法**：
```bash
insight-cli worker stop [选项]
```

**选项**：

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--pid-file PATH` | PID 文件路径 | `/var/run/dis-worker.pid` |
| `--force` | 强制终止（SIGKILL） | false |

**示例**：
```bash
insight-cli worker stop
```

**输出**：
```
Stopping worker (PID: 12345)...
Worker stopped successfully.
```

---

### 5.3 查看 Worker 状态（worker status）

**语法**：
```bash
insight-cli worker status [选项]
```

**选项**：

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--pid-file PATH` | PID 文件路径 | `/var/run/dis-worker.pid` |

**示例**：
```bash
insight-cli worker status
```

**输出（运行中）**：
```
Worker Status: Running
PID: 12345
Uptime: 2h 15m 30s
Current Job: 01J1A2B3C4D5E6F7G8H9K0M1 (stage: analyzing, progress: 55%)
```

**输出（未运行）**：
```
Worker Status: Not running
```

---

## 6. 服务管理（server）

### 6.1 启动完整服务（server start）

**语法**：
```bash
insight-cli server start [选项]
```

**说明**：同时启动 API Server + Worker

**选项**：

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--host TEXT` | API 监听地址 | `0.0.0.0` |
| `--port INT` | API 监听端口 | `8000` |
| `--reload` | 热重载（开发模式） | false |
| `--daemon` | 后台运行 | false |

**示例 1：前台运行（开发）**：
```bash
insight-cli server start --reload
```

**输出**：
```
[INFO] Starting Data Insight Service...
[INFO] API Server starting on http://0.0.0.0:8000
[INFO] Worker starting...
[INFO] ===============================================
[INFO] Data Insight Service is running!
[INFO]
[INFO]   API: http://localhost:8000
[INFO]   Web UI: http://localhost:8000/ui
[INFO]   OpenAPI Docs: http://localhost:8000/docs
[INFO]
[INFO] Press Ctrl+C to stop
[INFO] ===============================================
```

**示例 2：生产部署**：
```bash
insight-cli server start --host 0.0.0.0 --port 8000 --daemon
```

**示例 3：自定义端口**：
```bash
insight-cli server start --port 9000
```

---

### 6.2 停止服务（server stop）

**语法**：
```bash
insight-cli server stop
```

**示例**：
```bash
insight-cli server stop
```

**输出**：
```
Stopping API Server...
Stopping Worker...
Data Insight Service stopped.
```

---

## 7. 配置管理（config）

### 7.1 查看配置（config show）

**语法**：
```bash
insight-cli config show [选项]
```

**选项**：

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--format TEXT` | 输出格式（yaml/json） | yaml |

**示例**：
```bash
insight-cli config show
```

**输出（YAML）**：
```yaml
version: "0.1.0"
api:
  host: "0.0.0.0"
  port: 8000
database:
  url: "sqlite:///./jobs.db"
worker:
  poll_interval: 5
  concurrency: 1
...
```

**示例（JSON）**：
```bash
insight-cli config show --format json
```

---

### 7.2 验证配置（config validate）

**语法**：
```bash
insight-cli config validate [选项]
```

**选项**：

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--config PATH` | 指定配置文件 | `config/config.yaml` |

**示例**：
```bash
insight-cli config validate
```

**输出（成功）**：
```
Configuration is valid ✓
```

**输出（失败）**：
```
Configuration validation failed ✗
Error: Missing required field: api.port
```

---

## 8. 日志管理（logs）

### 8.1 查看日志（logs show）

**语法**：
```bash
insight-cli logs show [选项]
```

**选项**：

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--follow` / `-f` | 实时跟踪日志 | false |
| `--lines INT` / `-n` | 显示最后 N 行 | 50 |
| `--level TEXT` | 按级别过滤（INFO/WARNING/ERROR） | 全部 |

**示例 1：查看最近日志**：
```bash
insight-cli logs show
```

**示例 2：实时跟踪**：
```bash
insight-cli logs show --follow
```

**示例 3：只看错误**：
```bash
insight-cli logs show --level ERROR --lines 100
```

---

### 8.2 清理日志（logs clean）

**语法**：
```bash
insight-cli logs clean [选项]
```

**选项**：

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--days INT` | 删除 N 天前的日志 | 30 |
| `--force` | 跳过确认 | false |

**示例**：
```bash
insight-cli logs clean --days 7 --force
```

---

## 9. 使用场景示例

### 9.1 完整任务流程

```bash
# 1. 启动服务
insight-cli server start --reload

# 2. 创建任务
insight-cli job create data.csv --params-file params.json

# 输出 Job ID: 01J1A2B3C4D5E6F7G8H9K0M1

# 3. 监控任务（实时）
insight-cli job get 01J1A2B3C4D5E6F7G8H9K0M1 --watch

# 4. 任务完成后，查看详情
insight-cli job get 01J1A2B3C4D5E6F7G8H9K0M1

# 5. 浏览器打开报告
open http://localhost:8000/jobs/01J1A2B3C4D5E6F7G8H9K0M1/report

# 6. 下载 bundle（命令行）
curl -O http://localhost:8000/jobs/01J1A2B3C4D5E6F7G8H9K0M1/bundle
```

---

### 9.2 批量任务管理

```bash
# 批量创建任务（脚本）
for file in data/*.csv; do
  insight-cli job create "$file" --params-file params.json
  sleep 1
done

# 查看所有排队中的任务
insight-cli job list --status queued

# 查看所有失败任务
insight-cli job list --status failed --format json > failed_jobs.json
```

---

### 9.3 生产部署（Systemd）

**创建 systemd 服务文件**（`/etc/systemd/system/data-insight.service`）：
```ini
[Unit]
Description=Data Insight Service
After=network.target

[Service]
Type=simple
User=dis-user
WorkingDirectory=/opt/data-insight-service
ExecStart=/usr/local/bin/insight-cli server start --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

**管理服务**：
```bash
# 启动
sudo systemctl start data-insight

# 停止
sudo systemctl stop data-insight

# 查看状态
sudo systemctl status data-insight

# 开机自启
sudo systemctl enable data-insight

# 查看日志
sudo journalctl -u data-insight -f
```

---

### 9.4 Docker 部署

**Dockerfile**：
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .

ENV DIS_API_HOST=0.0.0.0
ENV DIS_API_PORT=8000
ENV DIS_DATABASE_URL=postgresql://user:pass@db:5432/dis

CMD ["insight-cli", "server", "start"]
```

**启动容器**：
```bash
docker build -t data-insight-service .
docker run -d -p 8000:8000 \
  -v $(pwd)/jobs:/app/jobs \
  -e DIS_DATABASE_URL=postgresql://... \
  --name dis-service \
  data-insight-service
```

**查看容器日志**：
```bash
docker logs -f dis-service
```

---

## 10. 故障排查

### 10.1 CLI 命令不存在

```bash
# 错误：insight-cli: command not found

# 解决：
pip install -e .  # 开发模式安装
# 或
pip install data-insight-service  # 正式安装
```

---

### 10.2 Worker 无法启动

```bash
# 错误：Database connection failed

# 检查配置
insight-cli config show

# 验证数据库连接
export DIS_DATABASE_URL=sqlite:///./jobs.db
insight-cli worker start --log-level DEBUG
```

---

### 10.3 任务一直排队

```bash
# 检查 Worker 是否运行
insight-cli worker status

# 如果未运行，启动 Worker
insight-cli worker start
```

---

## 11. 开发与调试

### 11.1 开发模式启动

```bash
# 热重载 + 详细日志
insight-cli server start --reload --log-level DEBUG
```

---

### 11.2 模拟错误

```bash
# 编辑配置
cat >> config/config.yaml <<EOF
testing:
  simulate_error:
    enabled: true
    stage: "analyzing"
    probability: 1.0
EOF

# 启动服务
insight-cli server start

# 创建任务（将在 analyzing 阶段失败）
insight-cli job create test.csv --params '{"package_name":"test"}'
```

---

## 12. 总结

### 12.1 常用命令速查

| 功能 | 命令 |
|------|------|
| 启动服务 | `insight-cli server start` |
| 创建任务 | `insight-cli job create <file> --params <json>` |
| 查看任务 | `insight-cli job get <id>` |
| 监控任务 | `insight-cli job get <id> --watch` |
| 任务列表 | `insight-cli job list` |
| 启动 Worker | `insight-cli worker start` |
| 查看配置 | `insight-cli config show` |
| 查看日志 | `insight-cli logs show -f` |

---

### 12.2 帮助信息

所有命令支持 `--help` 查看详细说明：
```bash
insight-cli --help
insight-cli job --help
insight-cli job create --help
```

---

### 12.3 相关文档

- `docs/ARCHITECTURE.md`：架构设计
- `docs/CONFIG.md`：配置体系
- `docs/API_MAPPING.md`：API 使用
- `specs_v0_1/SPEC_02_API.md`：API 规范
