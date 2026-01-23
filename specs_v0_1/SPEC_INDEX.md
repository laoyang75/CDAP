# 数据洞察服务（Python Skills）— Spec Pack

- Spec Version: **0.1.0**
- Last Updated: **2026-01-23**
- Target: **Spec-driven 开发**（Agent 直接按契约实现）

## 1. 总目标（One-liner）
用户发起 Job → 服务端拉取内网数据 → 统一预处理为 dataset 包 → 运行多个独立 Python skills（插件）生成结构化结果 → 汇总渲染 HTML 报告 → 返回给用户（并提供 bundle.zip）。

## 2. 文档清单
1) `SPEC_01_SYSTEM.md`：系统目标/组件/非功能需求/术语  
2) `SPEC_02_API.md`：对外 API 契约 + 错误模型（MVP 必须）  
3) `openapi.yaml`：OpenAPI 3.0（与 SPEC_02 一致）  
4) `SPEC_03_DATASET.md`：统一数据包（dataset）规范（目录结构、schema、hash、脱敏）  
5) `SPEC_04_SKILLS.md`：Skills（插件）规范（manifest、接口、result.json schema、运行隔离）  
6) `SPEC_05_ORCHESTRATION.md`：状态机、worker 编排、并发/超时/重试、产物落盘  
7) `SPEC_06_REPORTING.md`：报告汇总与 HTML 渲染规范（可选 LLM 文本增强）  
8) `SPEC_07_OBSERVABILITY_SECURITY.md`：日志/指标/审计/PII/权限/留存  
9) `SPEC_08_TESTING_ACCEPTANCE.md`：测试策略与验收标准  
10) `IMPLEMENTATION_PLAN.md`：两周 MVP + 后续扩展路线

## 3. 代码实现约束（Agent 必须遵守）
- 所有契约字段、文件名、状态机必须严格按本 spec。
- 任何新增字段必须通过版本升级（schema_version / spec_version）。
- 所有 skills 必须“只读 dataset_dir，只写 out_dir”，不得写其它路径。

## 4. MVP 强制产物
- `report/report.html`
- `bundle.zip`（包含 dataset + analysis + report + logs）
- `GET /jobs/{id}` 可查到 job 状态、阶段、进度、错误与产物索引
