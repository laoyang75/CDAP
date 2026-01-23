# SPEC_02_API — 对外 API 契约（MVP）

- Spec Version: 0.1.0
- Last Updated: 2026-01-23

> 本文是**规范性**定义；OpenAPI 见 `openapi.yaml`，二者必须一致。

## 1. 通用约定
### 1.1 Content Types
- 上传：`multipart/form-data`
- JSON：`application/json`
- HTML：`text/html`
- Bundle：`application/zip`

### 1.2 ID 规则
- `job_id` MUST 为 URL-safe 字符串（建议 ULID 或 UUIDv7）。
- 所有路径使用 `/jobs/{job_id}/...`

### 1.3 时间与时区
- 所有时间字段 MUST 使用 ISO-8601（UTC），例如 `2026-01-23T17:00:00Z`。

### 1.4 错误模型（统一）
所有 4xx/5xx 响应 MUST 为：
```json
{
  "error": {
    "code": "STRING_ENUM",
    "message": "human readable",
    "details": {},
    "retryable": false
  }
}
```

## 2. Endpoint：POST /jobs（创建任务）
### 2.1 请求（multipart）
- `file` (required)：cdid 列表文件（csv/xlsx 均可，MVP 先支持 csv）
- `params` (required, JSON string)：任务参数

`params` MUST 形如：
```json
{
  "package_name": "com.xxx.app",
  "time_range": {
    "start": "2026-01-01",
    "end": "2026-01-07"
  },
  "message_types": ["dna", "daa"],
  "skills": {
    "enabled": ["basic_stats"],
    "params": {
      "basic_stats": {}
    }
  },
  "report": {
    "format": "html",
    "llm": {
      "enabled": false
    }
  }
}
```

### 2.2 响应（201）
```json
{
  "job_id": "01J...ULID",
  "status": "queued",
  "created_at": "...Z",
  "links": {
    "self": "/jobs/{job_id}",
    "report": "/jobs/{job_id}/report",
    "bundle": "/jobs/{job_id}/bundle"
  }
}
```

## 3. Endpoint：GET /jobs/{id}（查询状态）
响应 MUST 包含（最小字段）：
```json
{
  "job_id": "01J...",
  "status": "analyzing",
  "stage": "analyzing",
  "progress": {
    "percent": 55,
    "message": "running skill basic_stats"
  },
  "created_at": "...Z",
  "updated_at": "...Z",
  "artifacts": {
    "report_html": null,
    "bundle_zip": null
  },
  "error": null
}
```

## 4. Endpoint：GET /jobs/{id}/report（获取 HTML）
- 若 job 未完成，MUST 返回 409 + error（code = JOB_NOT_READY）。
- 若完成，返回 `text/html`。

## 5. Endpoint：GET /jobs/{id}/bundle（获取 bundle.zip）
- 同上：未完成返回 409。
- 完成返回 zip（二进制流）。

## 6. Status 枚举（MUST）
- `queued`
- `fetching`
- `preprocessing`
- `analyzing`
- `reporting`
- `done`
- `failed`

## 7. 错误 code 枚举（MVP MUST）
- `INVALID_REQUEST`
- `JOB_NOT_FOUND`
- `JOB_NOT_READY`
- `UPLOAD_INVALID_FILE`
- `FETCH_UPSTREAM_FAILED`
- `FETCH_TIMEOUT`
- `PREPROCESS_FAILED`
- `SKILL_FAILED`
- `REPORT_FAILED`
- `INTERNAL_ERROR`

## 8. 鉴权（MVP 可选）
- MVP MAY 先不做；若做，建议 Bearer Token，并在审计日志记录 caller_id。
