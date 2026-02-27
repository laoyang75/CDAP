# SPEC_07_OBSERVABILITY_SECURITY — 可观察性与安全

- Spec Version: 0.1.0
- Last Updated: 2026-01-23

## 1. 日志（MUST）
- 每个 job MUST 写入 `logs/*.log`（按阶段分文件）
- 日志行 SHOULD 采用 JSON Lines（便于检索）
- 每条日志 MUST 包含：`ts`, `job_id`, `stage`, `level`, `msg`
- 错误 MUST 记录 `error.code`, `error.message`, `retryable`

## 2. 指标（SHOULD）
服务端 SHOULD 暴露指标（Prometheus 或日志聚合）：
- job_count_by_status
- stage_duration_seconds（histogram）
- skill_duration_seconds（by skill_name）
- fetch_fail_rate
- report_fail_rate

## 3. PII/脱敏（MUST）
- 日志不得输出明文敏感标识（cdid/imei/idfa/...）
- artifacts 表格 preview 不得含明文敏感标识
- meta.json 必须记录脱敏策略（pii_policy）

## 4. 权限（MVP MAY）
- MVP 可不做鉴权，但 MUST 预留 caller_id 字段（以后接 auth）
- 若启用鉴权，bundle 下载必须鉴权通过

## 5. 留存（SHOULD）
- 默认 bundle 留存 7 天（可配置）
- raw/upstream 与 dataset 可配置留存策略（合规要求优先）
