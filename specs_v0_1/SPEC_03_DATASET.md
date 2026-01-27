# SPEC_03_DATASET — 统一数据包（dataset）规范

- Spec Version: 0.1.0
- Last Updated: 2026-01-23

## 1. 目录结构（MUST）
Job 工作目录下的 dataset MUST 形如：
```
dataset/
  meta.json
  schema.json
  data_quality.json
  tables/
    <table_name>.parquet
  raw/
    upstream.xlsx            # 可选，但强烈建议保留以便审计/复现
```

## 2. meta.json（MUST）
meta.json MUST 包含：
- `dataset_version`: 固定 `"dataset-v1"`
- `job_id`
- `created_at`
- `source`: 上游来源信息（internal api base, task_id 等）
- `params_snapshot`: fetch 参数快照
- `pii_policy`: 脱敏策略描述
- `hashes`: dataset_hash（sha256）与各表 hash（可选）

## 3. schema.json（MUST）
schema.json 用于定义 tables 与列类型：
- `schema_version`: `"dataset-schema-v1"`
- `tables`: 数组，每个 table 包含 name/path/columns
- `columns`: name/type/nullable/description（description 可选）

> 类型集合（MUST 支持）：
- string, int64, float64, boolean, timestamp, date
- json_string（仍是 string，但标注语义，便于下游插件解析）

## 4. data_quality.json（MUST）
最小质量报告：
- row_count_total
- table_row_counts
- missing_rate_by_column（按 table）
- schema_mismatch（与预期映射的差异）
- warnings（数组）

## 5. 表命名规则（MUST）
预处理阶段从上游 Excel 生成 table 时：
- 若上游 Excel 有 sheet 名：table_name = `sheet_<index>_<normalized_sheet_name>`
- 若无：table_name = `sheet_<index>`
- normalized 规则：小写、非字母数字替换为 `_`，多 `_` 合并为单个 `_`

## 6. PII 脱敏（MUST）
- dataset 中不得包含可直接识别的敏感标识明文（例如 cdid / imei / idfa 等），除非显式允许（MVP 默认不允许）。
- 建议存储：
  - `*_hash`（sha256 前 16-32 位）
  - 或 `*_masked`（前后保留少量字符）

## 7. dataset_hash（MUST）
- dataset_hash MUST 对 `schema.json + meta.json + tables/*` 做稳定 hash（内容 hash，不依赖 mtime）。
- meta.json MUST 记录 dataset_hash。

## 8. Parquet vs CSV
- MVP SHOULD 优先 Parquet（pandas+pyarrow）。
- debug MAY 额外输出 `tables/<name>.csv`，但不得替代 parquet（除非明确配置）。
