# SPEC_05_ORCHESTRATION — 状态机与 Worker 编排

- Spec Version: 0.1.0
- Last Updated: 2026-01-23

## 1. 状态机（MUST）
状态枚举：
- queued → fetching → preprocessing → analyzing → reporting → done
- 任意阶段失败 → failed

## 2. 阶段产物（MUST）
- queued：`job.json`（参数快照 + 初始状态）
- fetching：`raw/upstream.xlsx` + `logs/fetch.log`
- preprocessing：`dataset/*` + `logs/preprocess.log`
- analyzing：`analysis/plugins/*/result.json` + `analysis/combined_result.json` + `logs/analyze.log`
- reporting：`report/report.html` + `logs/report.log`
- done：`bundle.zip`
- failed：`error.json`（stage/code/message/retryable）+ 当前阶段日志

## 3. Worker 行为（MUST）
W1. Worker MUST 获取一个 job 后，原子地将状态置为 `fetching` 并写 DB/落盘。  
W2. 每阶段开始 MUST 写 stage-start 日志；结束 MUST 写 stage-end 日志（含耗时）。  
W3. Worker MUST 支持重试（见第 5 节），重试不得覆盖旧产物（需写入 attempt 子目录或附带 attempt 号）。  

## 4. 并发与隔离（MUST）
- 每个 job MUST 拥有独立 workdir：`jobs/<job_id>/`
- 每个 skill MUST 写入独立目录：`analysis/plugins/<skill_name>/`
- Worker SHOULD 以 subprocess 运行 skill，防止内存污染与崩溃扩散。

## 5. 重试策略（MVP）
- fetching：retry 2 次（指数退避 1s/4s/16s），总超时可配置（默认 20 分钟）
- preprocessing：retry 0 次（除非是临时 IO 错误）
- analyzing：单 skill 失败时：
  - critical=true → job failed
  - critical=false → 标记该 skill failed，继续其它 skills
- reporting：retry 1 次（模板渲染失败通常不可恢复；若 LLM enabled 则可重试）

## 6. 超时（MUST）
- 每阶段 MUST 有 timeout（配置默认值）：
  - fetching_timeout_sec = 1200
  - preprocessing_timeout_sec = 600
  - analyzing_timeout_sec = 1800（或按 skill 累加）
  - reporting_timeout_sec = 300
- 超时 MUST 触发阶段失败（error.code = *_TIMEOUT）

## 7. 清理与留存（MAY）
- MVP MAY 不实现自动清理
- 后续 SHOULD 支持：
  - bundle 留存 N 天
  - raw/dataset 留存可配置
