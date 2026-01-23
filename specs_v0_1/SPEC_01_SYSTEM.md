# SPEC_01_SYSTEM — 系统概述与需求

- Spec Version: 0.1.0
- Last Updated: 2026-01-23

## 1. 术语
- **Job**：一次用户发起的端到端洞察任务（fetch → preprocess → analyze → report）。
- **Dataset 包**：统一数据包目录，包含 schema/meta/表数据（Parquet 优先）。
- **Skill**：一个独立的 Python 分析插件（可并发、可失败隔离），输出 `result.json`。
- **Artifacts**：插件输出的附加文件（csv/png/html 等），用于报告引用或下载。
- **Bundle**：最终打包产物 `bundle.zip`（可复现 + 可审计）。

## 2. 目标（Goals）
G1. **完全抛弃 Go**：分析逻辑全部在 Python skills 中实现。  
G2. **先跑通最简单分析**：MVP 提供 `basic_stats` skill，能产出可预览 HTML。  
G3. **可扩展**：新增分析能力只需新增一个 skill 目录（manifest + plugin）。  
G4. **可复现**：每次 Job 必须记录 dataset_hash、参数快照、代码版本、运行时间。  
G5. **可观察**：每阶段必须有日志；对外可查询状态/错误/产物。  

## 3. 非目标（Non-Goals）
N1. MVP 不追求分布式大数据计算（先单机 worker）。  
N2. MVP 不实现复杂的 DAG 编排（先支持“串行 + 无依赖并行”）。  
N3. MVP 不强制依赖 LLM（LLM 作为可选增强层）。  

## 4. 高层流程（Normative）
S1. 用户调用 `POST /jobs` 创建 Job（上传 cdid 文件 + 参数）。  
S2. 系统创建独立工作目录 `jobs/<job_id>/` 并写入 `job.json`。  
S3. Worker 执行状态机：
- fetching：调用内网 API 拉取上游结果并落盘 raw
- preprocessing：将 raw 转换为 dataset 包（统一表 + schema + meta + data_quality）
- analyzing：按配置运行 skills（插件），每个 skill 输出 result.json + artifacts
- reporting：汇总 skills 结果并渲染 report.html
- done：生成 bundle.zip，更新 Job 状态与产物索引

S4. 用户通过 `GET /jobs/<id>` 查询状态与产物；通过 `/report` 或 `/bundle` 下载结果。

## 5. 组件划分
- API Server（FastAPI）：接入层 + job 管理 + 文件上传 + 查询接口
- Queue：任务队列（Redis + RQ/Celery 任选其一）
- Worker：执行状态机与 skills（多进程隔离）
- Storage：MVP 本地磁盘；后续可替换 MinIO/S3
- DB：MVP SQLite；后续 PostgreSQL

## 6. 非功能需求（NFR）
NFR1. 可靠性：同一 Job 在 Worker 重启后可继续（断点续跑，至少能从最近阶段重试）。  
NFR2. 隔离性：每个 Job 独立目录；每个 Skill 独立 out_dir；Skill 进程级隔离。  
NFR3. 性能：MVP 单 Job 在 10 分钟内产出报告（取决于上游延迟；本地分析 ≤ 3 分钟）。  
NFR4. 安全：默认脱敏；日志禁止输出原始敏感标识；bundle 可配置留存周期。  
NFR5. 兼容：dataset 表格式优先 Parquet；至少支持 CSV fallback（debug）。  
