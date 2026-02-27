# 历史线下接手说明（归档）

> 来源：`delivery/cdid-analysis-platform/docs/HANDOFF.md`

# 交付与接手说明（CDID 数据分析平台）

## 1. 目录与职责

- `launcher_web.py`：唯一启动入口（启动/停止 API + Worker，带日志面板）
- `src/api/`：FastAPI API + UI 路由（Jinja2 模板渲染）
- `src/worker/`：任务队列 Worker（拉取数据 → 跑脚本 → 调 Gemini → 写报告）
- `src/db/`：SQLite/SQLAlchemy（启动时自动建表+轻量迁移）
- `src/ui/`：前端模板与静态资源
- `config/config.yaml`：核心配置（Gemini 模型/超时、上游、存储目录等）
- `config/column_mapping.yaml`：Excel 字段别名映射（新增字段/改名优先在这里维护）

## 2. 运行方式（开发/交付通用）

前置：
- Python 3.9+（项目目前按 3.9 兼容写法）
- 已安装 Gemini CLI（命令 `gemini --version` 可用，且能正常调用模型）

步骤：
1) 创建并激活虚拟环境（推荐）
2) `pip install -r requirements.txt`
3) 启动：`python launcher_web.py`
4) 打开启动器：`http://localhost:5555`

说明：
- 启动器会使用“当前运行 launcher_web.py 的解释器”去启动 API/Worker，所以用 venv 启动最稳：
  - `./venv/bin/python launcher_web.py`

## 3. 关键 URL

- 启动器：`http://localhost:5555`
- 用户端：
  - 创建任务：`http://localhost:8000/create`
  - 我的任务：`http://localhost:8000/tasks`
  - 任务详情：`http://localhost:8000/tasks/{job_id}`
- 管理后台：`http://localhost:8000/admin`

## 4. 任务模式

### 4.1 标准模式（内网拉取）
- 用户上传 CDID 文件（CSV/XLSX），选择 DNA/DAA（message_types），Worker 调上游创建任务、轮询、下载 `raw_data.xlsx`

### 4.2 调试模式（直接上传 raw_data.xlsx）
- 创建任务页支持“调试模式”
- 用户直接上传已下载好的 `raw_data.xlsx`（强制 `.xlsx`）
- Worker 会跳过上游请求/下载，直接执行脚本与报告生成

## 5. 多管线与报告

- 任务可选择多个管线（pipeline 多选）
- 每条管线会生成：
  - `jobs/outputs/<job_id>/pipelines/<pipeline_id>/analysis.json`
  - `jobs/outputs/<job_id>/pipelines/<pipeline_id>/report_input.json`
  - `jobs/outputs/<job_id>/pipelines/<pipeline_id>/report.html`
- 下载：
  - 单管线：`/api/jobs/{id}/report` 直接返回 HTML
  - 多管线：`/api/jobs/{id}/report` 返回 zip（包含索引与 pipelines/**）
- 预览（任务详情页 iframe 用）：
  - `/api/jobs/{id}/report/view`（多管线默认第一个）
  - `/api/jobs/{id}/report/view?pipeline_id=123`

## 6. Excel 字段与脚本约定（最重要）

分析产物约定（每条管线）：
- `analysis.json`：脚本输出的 `detail_data`（用于排查，可包含更多明细，不会喂给 Gemini）
- `report_input.json`：脚本输出的 `report_input`（稳定、可控、尽量小；Worker 会原样传给 Gemini）

入口文件：`src/worker/data_formats/insight_excel.py`

- `load_raw_dataframe(path)`：
  - 支持 Excel 多 sheet（如 dna/daa），会合并并补两列：
    - `message_type`：来自 sheet 名（dna/daa/unknown）
    - `source_sheet`：原始 sheet 名
- `standardize_device_columns(df, required=..., optional=...)`：
  - 把 `did/oaid/cdid/android_id/sys__boot__id` 等关键字段映射成统一列名
  - 若上游字段新增/改名：优先改 `config/column_mapping.yaml`，重启生效
