# SPEC_04_SKILLS — Python Skills（插件）规范

- Spec Version: 0.1.0
- Last Updated: 2026-01-23

## 1. 目标
- 新增分析能力 MUST 仅通过新增一个 skill 目录完成（无需改主流程）。
- 每个 skill MUST 独立执行、独立产出、失败隔离。
- 汇总与报告 MUST 只消费结构化输出（result.json），不得直接读取原始大表。

## 2. Plugins 目录结构（MUST）
代码仓中 skills 目录 MUST 形如：
```
analysis_skills/
  plugins/
    basic_stats/
      manifest.yaml
      plugin.py
      tests/
        test_basic_stats.py
```

## 3. manifest.yaml（MUST）
每个 skill MUST 提供 manifest.yaml，字段：
- `name` (string, required)
- `version` (semver string, required)
- `entrypoint` (string, required) 例如 `plugin.py:run`
- `description` (string, optional)
- `critical` (bool, default false) — 若 true，失败则 job 失败
- `default_params` (object, default {}) — skill 参数默认值
- `timeout_sec` (int, default 600) — skill 级超时
- `depends_on` (array[string], optional) — 简易 DAG（后续可扩展）

### manifest 示例
```yaml
name: basic_stats
version: 0.1.0
entrypoint: plugin.py:run
description: "Basic dataset stats (row counts, missing rates, top values)"
critical: true
timeout_sec: 300
default_params:
  top_k: 20
```

## 4. Skill 运行契约（MUST）
### 4.1 函数签名
entrypoint 对应函数 MUST 接受：
- `dataset_dir: str`
- `params: dict`
- `out_dir: str`
- `ctx: dict`（包含 job_id/run_id/logger 等，至少是 dict）

并返回（可选）任意对象，但 MUST 写出 `out_dir/result.json`。

### 4.2 I/O 约束
- Skill MUST 只读 `dataset_dir`（包括 dataset/schema.json、tables/*）。
- Skill MUST 只写 `out_dir`（禁止写其它路径）。
- Skill MUST 在开始时创建 `out_dir/artifacts/`（可选）。

### 4.3 失败行为（MUST）
- Skill 发生异常时，仍 MUST 写出 `out_dir/result.json`，其中：
  - `status = "failed"`
  - `error.message` 有值
  - `error.stacktrace` MAY 记录（注意脱敏）

## 5. result.json（MUST）
每个 skill 的输出 MUST 满足 `schemas/result-v1.schema.json`（见文件）。

顶层字段（MVP 最小集合）：
- `plugin`（name/version/schema_version）
- `status`（success|failed）
- `summary`（string）
- `metrics`（array）
- `warnings`（array）
- `provenance`（dataset_hash/params/started_at/duration_ms/env）

## 6. combined_result.json（MUST）
分析层完成后 MUST 生成 `analysis/combined_result.json`：
- `combined_version` = `"combined-v1"`
- `job_id`
- `dataset_hash`
- `skills`: map(skill_name → relative path to that skill result.json)
- `rollup`：聚合指标（例如总 warning 数、关键 high severity）
- `generated_at`

## 7. 运行隔离与并发（SHOULD）
- Worker SHOULD 使用 subprocess（或 multiprocessing）运行每个 skill，避免互相污染。
- Worker MAY 并发运行无依赖 skill（并发数可配置）。

## 8. 版本化（MUST）
- manifest 的 version MUST 是 semver。
- result.json MUST 记录 plugin.version 与 `schema_version="result-v1"`。
