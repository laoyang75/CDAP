# SPEC_06_REPORTING — 汇总与 HTML 报告规范

- Spec Version: 0.1.0
- Last Updated: 2026-01-23

## 1. 输入与输出（MUST）
- 输入：`analysis/combined_result.json` + 各 skill 的 `result.json` 与 artifacts
- 输出：
  - `report/report.html`（MVP 必须）
  - `report/report.json`（结构化索引，建议）
  - `bundle.zip`（MVP 必须）

## 2. report_context.json（SHOULD）
为确保报告稳定，reporting 阶段 SHOULD 先生成 `analysis/report_context.json`（给模板消费）：
- `context_version` = `report-context-v1`
- `job_id`
- `dataset_hash`
- `generated_at`
- `sections`（数组：每个 section 含标题、要点、引用 tables/charts）
- `warnings_rollup`（汇总告警）

## 3. HTML 模板结构（MUST）
report.html MUST 至少包含以下章节：
1) 摘要（Summary）
2) 关键指标（Key Metrics）
3) 关键发现与风险（Findings & Risks）
4) 数据质量与限制（Data Quality & Limitations）
5) 附录（Appendix：表/图索引、skills 列表与版本）

### 图表与表格引用规范（MUST）
- 图表文件引用使用相对路径（相对 report.html 的目录）：
  - `../analysis/plugins/<skill>/artifacts/charts/<name>.png`
- 表格引用：
  - HTML 中展示 preview（前 N 行）
  - 完整表提供下载链接到 csv artifact

## 4. 可选：LLM 文本增强（MAY）
若启用 LLM，仅用于生成“解读文本”，不得进行统计计算。
- LLM 输入 MUST 仅来自 `report_context.json`（不得喂原始大表）。
- LLM 输出 MUST 为纯文本或 Markdown 片段，由模板插入。

### Gemini CLI（headless）调用建议（可实现 Adapter）
- 使用 `--prompt/-p` 非交互运行。citeturn0search0turn0search3
- 使用 `--output-format json` 获取结构化输出，便于服务端解析与落盘。citeturn0search0turn0search6
- 支持通过 stdin 管道输入（自动化脚本）。citeturn0search3
- settings.json 支持用户级与项目级配置文件（用于 headless 环境稳定配置）。citeturn0search2turn0search6turn0search5

> 注意：Gemini CLI 的具体安装、鉴权、配额属于部署范畴；本 spec 只定义“如何调用与如何处理输出/错误”。

## 5. 错误处理（MUST）
- 渲染失败：error.code = REPORT_FAILED，job 进入 failed（MVP）
- 若 LLM 启用且失败：
  - MAY 降级：跳过 LLM 解读，仍输出 report.html（标注“LLM 文本生成失败”）
