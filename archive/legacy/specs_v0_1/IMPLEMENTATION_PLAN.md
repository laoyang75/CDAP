# IMPLEMENTATION_PLAN — 实施计划（默认两周 MVP）

- Spec Version: 0.1.0
- Last Updated: 2026-01-23

## Week 1：Job 框架 + Fetch + Preprocess
- [ ] FastAPI：实现 POST /jobs、GET /jobs/{id}、GET /report、GET /bundle
- [ ] Queue + Worker：实现状态机（queued/fetching/preprocessing/analyzing/reporting/done/failed）
- [ ] Fetch Adapter：对接内网 API（create/poll/download），落盘 raw/upstream.xlsx
- [ ] Preprocess：解析 upstream.xlsx → dataset（schema/meta/data_quality + parquet tables）
- [ ] Schema 校验：生成的 json 必须通过 schemas/*.schema.json

**验收**：固定输入可稳定产生 dataset；job 可查到 preprocessing 完成。

## Week 2：Skills 引擎 + basic_stats + HTML 报告
- [ ] Skills Registry：扫描 plugins/*/manifest.yaml，校验 manifest schema
- [ ] Skill Runner：subprocess 运行每个 skill；写 result.json（成功/失败都写）
- [ ] MVP Skill：basic_stats（行数、缺失率、TopK 值，输出 metrics + preview table csv）
- [ ] 汇总：combined_result.json + report_context.json（可选）+ report.html（Jinja2）
- [ ] bundle.zip：打包 dataset+analysis+report+logs

**验收**：端到端自动化跑通；报告可预览；新增 skill 目录可被发现执行。

## 后续（可选）
- 并行执行无依赖 skills
- LLM 文本增强（Gemini CLI adapter）
- 存储迁移到 S3/MinIO + DB 迁移到 Postgres
- 取消/重跑接口（/cancel, /rerun）
