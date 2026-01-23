# 强制覆盖说明（OVERRIDES.md）

**项目**：Data Insight Service (Python Skills)
**版本**：0.1.0
**最后更新**：2026-01-23

---

## 文档目的

本文档记录所有**偏离** `specs_v0_1/` 规范的设计决策与实现细节。任何与原始 Spec 不一致的地方，**必须**在此文档中声明理由并同步更新相关文件（`openapi.yaml`、schema 等）。

---

## 强制覆盖清单

### O1) 无鉴权（内网运行）

**原始 Spec**：
- `SPEC_02_API.md` 第 8 节提到"MVP MAY 先不做鉴权"
- `SPEC_07_OBSERVABILITY_SECURITY.md` 提到审计日志需记录 `caller_id`

**Override 决策**：
- **完全移除鉴权逻辑**：所有 API 端点和 Web UI 直接可访问，无需 Token 或认证
- **理由**：
  1. 服务运行在内网环境，信任网络边界
  2. 减少 MVP 复杂度，加速开发
  3. 用户明确要求内网部署，无需外网暴露

**实现影响**：
- `src/api/routes.py`：所有端点无 `Depends(authenticate)` 依赖
- `openapi.yaml`：移除 `securitySchemes` 和 `security` 字段
- `docs/ARCHITECTURE.md`：安全章节标注"无鉴权（内网）"

**未来迁移路径**（Phase 3+）：
- 如需启用鉴权，添加 Bearer Token 校验
- 通过配置开关控制：`config.yaml` → `security.enabled: true`

---

### O2) 上游 Excel sheet/字段样例不固化

**原始 Spec**：
- `SPEC_03_DATASET.md` 假设上游数据具有固定 schema（cdid, did, oaid 等字段）
- `examples/` 中提供了示例 Excel 格式

**Override 决策**：
- **不在代码中硬编码字段名或 sheet 结构**
- **预处理阶段需动态推导 schema**（Phase 1 实现）
- **理由**：
  1. 上游 API 返回的字段可能变化（业务迭代）
  2. 不同数据源可能有不同格式
  3. 增强系统灵活性，避免频繁改代码

**实现影响**：
- `src/worker/stages/preprocess.py`：
  - **不** 使用 hardcoded 字段列表（如 `["cdid", "did", "oaid"]`）
  - 使用 schema 推导逻辑（Pandas `infer_objects()` + 自定义规则）
  - 生成 `dataset/schema.json`（动态反映实际字段）
- `config/config.yaml`：
  - 可选配置：`preprocessing.required_columns: ["cdid"]`（只强制最小必需字段）

**Phase 0 实现**：
- 占位实现写死简单 schema（`{"cdid": "string", "value": "int"}`）
- Phase 1 实现真实推导逻辑

---

### O3) 永远单线程执行（全局 FIFO）

**原始 Spec**：
- `SPEC_05_ORCHESTRATION.md` 第 4 节提到"Worker MAY 并发运行无依赖 skill"
- 暗示支持多 Job 并发

**Override 决策**：
- **系统全局一次只运行一个 Job**（FIFO 队列）
- **同一 Job 内的 skills 也必须串行执行**
- **理由**：
  1. 简化并发控制，避免资源竞争
  2. 上游 API 可能不支持并发请求
  3. 内网环境吞吐量需求低（10-50 Jobs/天）

**实现影响**：
- `src/worker/main.py`：
  - Worker 主循环每次只取一个 Job：
    ```python
    job = db.get_oldest_queued_job()  # LIMIT 1
    ```
  - 执行完毕后再取下一个
- `src/worker/stages/analyze.py`：
  - Skills 按顺序串行执行：
    ```python
    for skill_name in enabled_skills:
        run_skill(skill_name)  # 阻塞执行
    ```
- 部署约束：
  - **只部署一个 Worker 实例**（通过容器/进程管理保证）
  - 如误启动多个 Worker，通过数据库行锁保证只有一个 Worker 处理同一 Job

**未来扩展**（Phase 4+）：
- 支持多 Worker 实例（通过 Redis 队列 + 分布式锁）
- 支持 Skills 并发（修改 `analyze.py` 使用 `multiprocessing.Pool`）

---

### O4) 提供 Web UI + 管理 CLI + 启动器 + 配置体系

**原始 Spec**：
- Spec 文档主要描述 API 层，未强制要求 UI/CLI
- `SPEC_08_TESTING_ACCEPTANCE.md` 提到通过 API 测试验收

**Override 决策**：
- **必须提供完整的用户界面与管理工具**
- **组件清单**：
  1. **Web UI**：用户友好的任务创建与监控界面
  2. **CLI 工具**：管理员命令行工具
  3. **启动器**：一键启动 API + Worker
  4. **配置体系**：YAML + 环境变量 + CLI 参数

**理由**：
- 提升用户体验（非技术用户也能使用）
- 方便运维管理（CLI）
- 简化部署（启动器）

**实现影响**：
- 新增组件：
  - `src/ui/`：Web UI（Jinja2 模板 + 静态资源）
  - `src/cli/`：CLI 工具（Click 框架）
  - `scripts/start.sh`：启动脚本
  - `config/config.yaml`：配置文件

**Phase 0 实现**：
- Web UI：只实现创建任务 + 查询状态（不展示 report/bundle）
- CLI：只实现 `job create/list/get` + `worker start`

---

## Spec 同步要求

任何 Override 必须同步更新以下文件（如适用）：

| Override | 需更新文件 |
|----------|-----------|
| O1 (无鉴权) | `openapi.yaml`（移除 security）<br>`docs/API_MAPPING.md`（说明差异） |
| O2 (不固化字段) | `SPEC_03_DATASET.md`（标注动态 schema）<br>`schemas/dataset-schema-v1.schema.json`（说明字段可变） |
| O3 (单线程) | `SPEC_05_ORCHESTRATION.md`（标注 concurrency=1）<br>`docs/ARCHITECTURE.md`（单线程设计章节） |
| O4 (UI/CLI) | `README.md`（新增使用文档）<br>`docs/CLI_USAGE.md`（CLI 文档） |

---

## 版本追踪

| Override ID | 引入版本 | 计划移除版本 | 备注 |
|-------------|---------|------------|------|
| O1 | 0.1.0 | Phase 3 | 后续可通过配置启用鉴权 |
| O2 | 0.1.0 | N/A | 永久保留（设计优势） |
| O3 | 0.1.0 | Phase 4 | 扩展时支持并发 |
| O4 | 0.1.0 | N/A | 永久保留（用户体验） |

---

## 审核与更新

**规则**：
1. 任何新的偏离 Spec 的实现，**必须**先在本文档中新增一节
2. 每次更新必须注明日期与版本
3. 定期与 `specs_v0_1/` 对账，确保同步

**责任人**：项目架构师 / Tech Lead

**最后审核**：2026-01-23

---

## 总结

本文档记录了 4 个强制覆盖：
1. **O1**：无鉴权（内网）
2. **O2**：不固化字段（动态 schema）
3. **O3**：单线程 FIFO（简化并发）
4. **O4**：提供 UI/CLI/启动器（完整产品）

所有覆盖均基于实际需求与 MVP 约束，未违反 Spec 的核心设计原则（状态机、插件化、可复现性）。
