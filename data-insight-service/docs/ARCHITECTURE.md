# 架构设计文档（ARCHITECTURE.md）

**项目**：Data Insight Service (Python Skills)
**版本**：0.1.0
**最后更新**：2026-01-23

---

## 1. 系统概述

Data Insight Service 是一个内网数据洞察分析服务，通过**插件化 Python Skills** 完成数据获取、预处理、分析和报告生成的全流程。系统采用 **spec-driven** 设计，严格遵循 `specs_v0_1/` 中的规范契约。

### 1.1 核心流程

```
用户发起 Job → API 接收 → 入队 → Worker 单线程 FIFO 处理 → 产出 HTML 报告 + Bundle
```

状态机：`queued → fetching → preprocessing → analyzing → reporting → done` (或 `failed`)

---

## 2. 组件划分

### 2.1 API Server (FastAPI)

**职责**：
- 接收用户请求（`POST /jobs` 创建任务）
- 提供任务查询接口（`GET /jobs/{id}`）
- 提供产物下载接口（`/report`, `/bundle`）
- 提供 Web UI 界面（`/ui/*`）

**技术栈**：
- FastAPI（异步 Web 框架）
- Pydantic（数据验证，严格遵循 `openapi.yaml`）
- Jinja2（UI 模板渲染）

**关键模块**：
- `src/api/main.py` - 应用入口
- `src/api/routes.py` - API 路由
- `src/api/errors.py` - 统一错误处理（符合 SPEC_02 错误模型）
- `src/ui/routes.py` - Web UI 路由

### 2.2 Database (SQLite → PostgreSQL)

**职责**：
- 存储 Job 元数据（状态、参数、产物索引、错误信息）
- 支持任务查询与状态更新

**表结构**：

**jobs 表**：
| 字段 | 类型 | 说明 |
|------|------|------|
| job_id | VARCHAR(26) PK | ULID 格式 |
| status | VARCHAR(20) | queued/fetching/.../done/failed |
| stage | VARCHAR(20) | 当前阶段 |
| progress | JSON | {percent: int, message: str} |
| params | JSON | 用户参数快照 |
| artifacts | JSON | {report_html: str, bundle_zip: str} |
| error | JSON | {code, message, details, retryable} |
| created_at | TIMESTAMP | UTC 时间 |
| updated_at | TIMESTAMP | UTC 时间 |

**说明**：
- MVP 阶段使用 SQLite（`jobs.db`）
- 后续可迁移到 PostgreSQL（仅需修改连接配置）

### 2.3 Worker (单线程 FIFO)

**职责**：
- 从队列中取出 `queued` 状态的 Job（FIFO 顺序）
- 执行状态机流转（fetch → preprocess → analyze → report）
- 写入日志、更新数据库、落盘产物
- 处理超时与重试

**核心约束（Override O3）**：
- **全局单线程执行**：系统一次只运行一个 Job
- **FIFO 队列**：按 `created_at` 升序取最早的 `queued` Job
- **Skills 串行执行**：同一 Job 内的多个 skills 也必须串行运行

**实现方式**：
```python
# Worker 主循环（伪代码）
while True:
    job = db.get_oldest_queued_job()  # SELECT ... WHERE status='queued' ORDER BY created_at LIMIT 1
    if not job:
        time.sleep(5)
        continue

    # 原子更新状态
    db.atomic_update(job.id, status='fetching')

    # 执行状态机
    try:
        run_fetch(job)
        run_preprocess(job)
        run_analyze(job)  # 内部串行执行所有 skills
        run_report(job)
        db.update(job.id, status='done')
    except Exception as e:
        db.update(job.id, status='failed', error={...})
```

**关键模块**：
- `src/worker/main.py` - Worker 主循环
- `src/worker/executor.py` - 状态机执行器
- `src/worker/stages/` - 各阶段实现（Phase 0 为占位实现）

### 2.4 Skills 插件系统

**职责**：
- 提供可扩展的分析能力（新增分析无需改主流程）
- 每个 Skill 独立执行、独立产出、失败隔离

**目录结构**：
```
analysis_skills/
  plugins/
    basic_stats/              # MVP 必备
      manifest.yaml           # 插件元数据
      plugin.py               # 入口函数 run(dataset_dir, params, out_dir, ctx)
      tests/
        test_basic_stats.py
```

**运行契约**（符合 SPEC_04）：
- **只读** `dataset_dir`
- **只写** `out_dir/`
- **必须输出** `out_dir/result.json`（符合 `schemas/result-v1.schema.json`）
- **进程隔离**：通过 subprocess 运行（Phase 0 可简化为直接调用）

**执行顺序**（Phase 0）**：
- 串行执行所有启用的 skills
- 顺序：按 manifest.yaml 中的 `depends_on` 或配置顺序
- 失败策略：
  - `critical=true` → Job 失败
  - `critical=false` → 标记该 skill 失败，继续其他 skills

### 2.5 Web UI (最小实现)

**职责**（Phase 0）：
- 创建任务表单（上传文件 + 输入参数）
- 展示任务列表
- 展示任务详情与实时状态（轮询）

**实现技术**：
- Jinja2 模板（无 React/Vue）
- 原生 JavaScript（轮询 GET `/jobs/{id}`）
- 简单 CSS 样式

**页面清单**：
| 路由 | 说明 |
|------|------|
| GET /ui | 创建任务表单 |
| GET /ui/jobs | 任务列表（分页） |
| GET /ui/jobs/{id} | 任务详情（轮询状态） |

**注意**：Phase 0 不展示 report/bundle（因为还未实现真实逻辑）

### 2.6 CLI 工具

**职责**：
- 提供命令行管理接口
- 启动 Worker 和 API Server

**命令清单**：
```bash
insight-cli job create <file> --params <json>
insight-cli job list [--status queued|done|failed]
insight-cli job get <job_id>
insight-cli job delete <job_id>
insight-cli worker start
insight-cli server start  # 同时启动 API + Worker
```

**实现技术**：
- Click（Python CLI 框架）
- Rich/Tabulate（表格输出）

---

## 3. 单线程 FIFO 实现（Override O3）

### 3.1 为什么单线程？

**原因**：
1. **简化复杂度**：避免并发竞争、资源争抢、死锁问题
2. **内网数据源限制**：上游 API 可能不支持并发请求
3. **可预测性**：任务按提交顺序执行，便于调试和审计

### 3.2 实现机制

**数据库层面**：
```sql
-- Worker 取任务时使用行锁（SQLite 不支持 SELECT FOR UPDATE，但可通过事务保证）
BEGIN TRANSACTION;
SELECT * FROM jobs WHERE status = 'queued' ORDER BY created_at ASC LIMIT 1;
UPDATE jobs SET status = 'fetching', updated_at = NOW() WHERE job_id = ?;
COMMIT;
```

**应用层面**：
```python
class Worker:
    def run_forever(self):
        while True:
            with db.transaction():
                job = db.get_oldest_queued_job()
                if not job:
                    time.sleep(5)  # 无任务时休眠
                    continue
                db.update_status(job.id, 'fetching')

            # 执行任务（在事务外，避免长时间锁表）
            self.execute_job(job)
```

**保证 FIFO**：
- 查询条件：`WHERE status='queued' ORDER BY created_at ASC LIMIT 1`
- 只有一个 Worker 实例运行（通过部署配置保证）

### 3.3 Skills 串行执行

```python
def run_analyze_stage(job):
    enabled_skills = job.params['skills']['enabled']
    for skill_name in enabled_skills:
        logger.info(f"Running skill: {skill_name}")
        try:
            run_skill(skill_name, dataset_dir, out_dir, params)
        except Exception as e:
            if skill_manifest['critical']:
                raise  # Job 失败
            else:
                log_skill_failure(skill_name, e)
```

---

## 4. 目录结构（运行时）

### 4.1 项目代码结构

```
data-insight-service/
├── docs/                       # 文档（Phase 0 必须）
│   ├── ARCHITECTURE.md         # 本文档
│   ├── OVERRIDES.md            # 强制覆盖说明
│   ├── CONFIG.md               # 配置体系
│   ├── API_MAPPING.md          # API 与 openapi.yaml 一致性
│   └── CLI_USAGE.md            # CLI 使用文档
├── config/                     # 配置文件
│   ├── config.yaml             # 默认配置
│   └── config.schema.json      # JSON Schema 验证
├── src/
│   ├── api/                    # FastAPI 应用
│   │   ├── main.py
│   │   ├── routes.py
│   │   ├── dependencies.py
│   │   └── errors.py
│   ├── worker/                 # Worker 实现
│   │   ├── main.py
│   │   ├── executor.py
│   │   └── stages/
│   │       ├── fetch.py
│   │       ├── preprocess.py
│   │       ├── analyze.py
│   │       └── report.py
│   ├── db/                     # 数据库
│   │   ├── connection.py
│   │   └── models.py
│   ├── models/                 # Pydantic 模型
│   │   ├── job.py
│   │   └── errors.py
│   ├── ui/                     # Web UI
│   │   ├── routes.py
│   │   ├── templates/
│   │   │   ├── index.html
│   │   │   ├── jobs.html
│   │   │   └── job_detail.html
│   │   └── static/
│   │       ├── styles.css
│   │       └── app.js
│   ├── cli/                    # CLI 工具
│   │   └── main.py
│   ├── config.py               # 配置加载
│   └── utils.py                # 工具函数
├── analysis_skills/            # Skills 插件
│   └── plugins/
│       └── basic_stats/
│           ├── manifest.yaml
│           ├── plugin.py
│           └── tests/
├── jobs/                       # 运行时目录（.gitignore）
│   └── <job_id>/
│       ├── job.json
│       ├── raw/
│       ├── dataset/
│       ├── analysis/
│       ├── report/
│       ├── logs/
│       ├── bundle.zip
│       └── error.json
├── tests/                      # 测试
│   ├── test_api.py
│   ├── test_worker.py
│   └── test_e2e.py
├── scripts/                    # 脚本
│   └── start.sh
├── requirements.txt            # 依赖
├── pyproject.toml              # 项目元数据
└── README.md
```

### 4.2 Job 工作目录（jobs/<job_id>/）

**说明**：每个 Job 拥有独立目录，包含所有中间产物和最终输出。

```
jobs/01J1A2B3C4D5E6F7G8H9K0M1/
├── job.json                    # Job 元数据快照（符合 SPEC_05）
├── raw/                        # fetching 阶段产物
│   ├── upstream.xlsx           # 上游数据原始文件
│   └── cdid_list.csv           # 用户上传的输入文件
├── dataset/                    # preprocessing 阶段产物（符合 SPEC_03）
│   ├── schema.json             # 数据集 schema
│   ├── meta.json               # 元数据（dataset_hash, row_count 等）
│   ├── data_quality.json       # 数据质量报告
│   └── tables/
│       └── main_table.parquet  # Parquet 格式表数据
├── analysis/                   # analyzing 阶段产物（符合 SPEC_04）
│   ├── combined_result.json    # 汇总结果
│   └── plugins/
│       └── basic_stats/
│           ├── result.json     # Skill 输出（符合 result-v1.schema.json）
│           └── artifacts/      # 可选附件（csv/png/html）
│               └── stats.csv
├── report/                     # reporting 阶段产物（符合 SPEC_06）
│   └── report.html             # 最终 HTML 报告
├── logs/                       # 日志（每阶段一个文件）
│   ├── fetch.log
│   ├── preprocess.log
│   ├── analyze.log
│   └── report.log
├── bundle.zip                  # 最终打包产物（done 阶段生成）
└── error.json                  # 失败时的错误详情（符合 SPEC_02）
```

**关键约束**：
- 所有路径必须在 `jobs/<job_id>/` 下（安全隔离）
- Skills 只能读 `dataset/`，只能写 `analysis/plugins/<skill_name>/`
- `bundle.zip` 包含：dataset + analysis + report + logs（用于审计与复现）

---

## 5. 状态机详细设计（Phase 0 占位实现）

### 5.1 状态流转图

```
[创建] --> queued
            ↓
        fetching (模拟: sleep 0.5s)
            ↓
      preprocessing (模拟: sleep 0.8s)
            ↓
       analyzing (模拟: 每个 skill sleep 1s)
            ↓
       reporting (模拟: sleep 0.5s)
            ↓
          done

任意阶段失败 --> failed
```

### 5.2 阶段职责（Phase 0 占位）

| 阶段 | 真实逻辑（Phase 1+） | Phase 0 占位实现 |
|------|---------------------|----------------|
| **fetching** | 调用内网 API 拉取数据 | sleep 0.5s + 写 `raw/mock.txt` |
| **preprocessing** | 解析 Excel → 统一 Parquet | sleep 0.8s + 写 `dataset/meta.json` |
| **analyzing** | 运行 skills 插件 | sleep 1s + 写 `analysis/plugins/<skill>/result.json` |
| **reporting** | 渲染 HTML 报告 | sleep 0.5s + 写 `report/report.html` (占位内容) |
| **done** | 打包 bundle.zip | 创建空 bundle.zip |

### 5.3 每阶段必须操作（Phase 0 必须实现）

**进入阶段时**：
1. 更新 DB：`status=<stage>`, `updated_at=NOW()`
2. 更新 `job.json`：`stage=<stage>`
3. 创建日志文件：`logs/<stage>.log`
4. 写日志：`[INFO] Stage <stage> started`

**执行过程中**：
1. 定期更新 `progress`（如 `{percent: 50, message: "processing..."}`）
2. 写日志：关键步骤日志

**完成阶段时**：
1. 写日志：`[INFO] Stage <stage> completed in Xms`
2. 更新 DB：`updated_at=NOW()`
3. 如果是最后阶段（reporting），额外更新 `artifacts`

**失败时**：
1. 更新 DB：`status='failed'`, `error={code, message, ...}`
2. 写 `error.json` 文件
3. 写日志：`[ERROR] Stage <stage> failed: <reason>`
4. 停止执行（不再进入下一阶段）

### 5.4 模拟错误（可选功能）

**配置开关**：
```yaml
# config/config.yaml
testing:
  simulate_error:
    enabled: false
    stage: "analyzing"     # 在哪个阶段模拟失败
    error_code: "SKILL_FAILED"
    probability: 0.5       # 50% 概率失败
```

**用途**：测试失败场景，验证 `error.json` 和日志是否正确写入。

---

## 6. 未来阶段计划（Phase 0 不实现）

**Phase 1（真实 fetch/preprocess）**：
- 实现 fetching：调用内网 API（`http://172.17.129.204:6829`）
- 实现 preprocessing：解析 Excel → Parquet + schema 推导

**Phase 2（真实 skills）**：
- 实现 `basic_stats` skill：计算行数、缺失率、Top K 值
- 实现 skills 进程隔离（subprocess）

**Phase 3（真实 report）**：
- 实现 HTML 报告渲染（Jinja2 模板 + 数据可视化）
- 可选：LLM 增强（生成自然语言总结）

**Phase 4（优化与扩展）**：
- 支持 PostgreSQL
- 支持 MinIO/S3 存储
- 支持 Redis 队列（Celery/RQ）
- 支持 Skills 并发（多进程）
- 实现自动清理与留存策略

---

## 7. 与 Spec 的对齐

| Spec 文档 | 对应实现 |
|-----------|---------|
| SPEC_01_SYSTEM.md | 本文档（组件划分、流程、NFR） |
| SPEC_02_API.md | `src/api/routes.py` + `openapi.yaml` |
| SPEC_03_DATASET.md | `jobs/<job_id>/dataset/`（Phase 1 实现） |
| SPEC_04_SKILLS.md | `analysis_skills/plugins/` + `src/worker/stages/analyze.py` |
| SPEC_05_ORCHESTRATION.md | `src/worker/executor.py`（状态机） |
| SPEC_06_REPORTING.md | `src/worker/stages/report.py`（Phase 3 实现） |
| SPEC_07_OBSERVABILITY_SECURITY.md | `logs/`（Phase 2+ 增强） |
| SPEC_08_TESTING_ACCEPTANCE.md | `tests/`（本阶段基础测试） |

---

## 8. 关键设计决策

| 决策 | 原因 | 备注 |
|------|------|------|
| 使用 FastAPI | 高性能、异步、OpenAPI 原生支持 | |
| SQLite → PostgreSQL | MVP 快速启动，后续可迁移 | 只需改配置 |
| 单线程 FIFO | 简化复杂度，满足内网场景 | 见 Override O3 |
| Parquet 优先 | 高效存储，与数据分析工具兼容 | Phase 1 实现 |
| 独立 Job 目录 | 隔离性、可复现性、审计友好 | 符合 SPEC_05 |
| Jinja2 UI | 无需前端构建，简单直接 | MVP 够用 |
| Click CLI | 标准 Python CLI 框架 | 生态成熟 |

---

## 9. 性能与扩展性考量

**MVP 阶段（单机）**：
- 预期：10-50 Jobs/天
- 单 Job 耗时：5-10 分钟（取决于上游延迟）
- 存储：单 Job ~100MB（dataset + report）

**扩展方向**：
1. **水平扩展**：多 Worker 实例 + Redis 队列
2. **存储扩展**：MinIO/S3（对象存储）
3. **数据库扩展**：PostgreSQL（主从复制）
4. **Skills 并发**：多进程执行无依赖 skills

---

## 10. 安全与合规

**Phase 0 注意事项**：
- **无鉴权**（Override O1）：内网环境，信任网络边界
- **日志脱敏**：避免记录原始 CDID/IMEI 等敏感字段（Phase 1+ 实现）
- **数据留存**：默认不自动清理（后续可配置留存周期）

**后续增强**：
- 审计日志（谁、何时、做了什么）
- 访问控制（基于 Token 或 IP 白名单）
- 数据脱敏策略（hash/mask）

---

## 11. 总结

本架构设计遵循以下原则：
1. **Spec-driven**：严格按照 `specs_v0_1/` 规范实现
2. **简单优先**：MVP 阶段避免过度设计
3. **可扩展**：预留扩展点，方便后续迭代
4. **可观察**：日志、状态、产物清晰可查
5. **可复现**：bundle.zip 包含完整执行上下文

**Phase 0 交付物**：
- ✅ 完整文档（本文档 + 其他 4 个文档）
- ✅ 项目骨架（目录结构 + 配置体系）
- ✅ 任务状态机骨架（模拟流转）
- ✅ 最小 Web UI（创建/查询）
- ✅ 最小 CLI（管理工具）
- ✅ 基础测试（端到端验证）

**等待审核通过后，进入 Phase 1（真实 fetch/preprocess 实现）。**
