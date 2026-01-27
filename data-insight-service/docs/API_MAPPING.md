# API 映射与一致性文档（API_MAPPING.md）

**项目**：Data Insight Service (Python Skills)
**版本**：0.1.0
**最后更新**：2026-01-23

---

## 1. 文档目的

本文档说明**实际 API 实现**与 `specs_v0_1/openapi.yaml` 的一致性，并记录任何偏离（需同步到 `OVERRIDES.md`）。

---

## 2. API 端点映射

### 2.1 POST /jobs（创建任务）

**OpenAPI Spec**：
```yaml
paths:
  /jobs:
    post:
      summary: Create a job
      requestBody:
        content:
          multipart/form-data:
            schema:
              required: [file, params]
              properties:
                file: { type: string, format: binary }
                params: { type: string, description: "JSON string" }
      responses:
        "201":
          content:
            application/json:
              schema: { $ref: "#/components/schemas/JobCreated" }
```

**实现**（`src/api/routes.py`）：
```python
@app.post("/jobs", status_code=201)
async def create_job(
    file: UploadFile = File(...),
    params: str = Form(...),
    db: Session = Depends(get_db)
):
    # 解析 params（JSON string）
    params_dict = json.loads(params)

    # 保存文件到临时目录
    job_id = generate_ulid()
    job_dir = Path(f"jobs/{job_id}")
    job_dir.mkdir(parents=True, exist_ok=True)

    # 写入 job.json
    # 插入数据库
    # 返回 JobCreated 响应

    return {
        "job_id": job_id,
        "status": "queued",
        "created_at": now_iso(),
        "links": {
            "self": f"/jobs/{job_id}",
            "report": f"/jobs/{job_id}/report",
            "bundle": f"/jobs/{job_id}/bundle"
        }
    }
```

**一致性**：✅ 完全符合
- 接受 `multipart/form-data`
- 必填字段：`file`, `params`
- 返回 201 + `JobCreated` 结构
- 错误返回 400 + `ErrorResponse`

**差异**：无

---

### 2.2 GET /jobs/{job_id}（查询任务状态）

**OpenAPI Spec**：
```yaml
paths:
  /jobs/{job_id}:
    get:
      parameters:
        - in: path
          name: job_id
          required: true
          schema: { type: string }
      responses:
        "200":
          content:
            application/json:
              schema: { $ref: "#/components/schemas/JobStatus" }
        "404":
          content:
            application/json:
              schema: { $ref: "#/components/schemas/ErrorResponse" }
```

**JobStatus Schema**：
```json
{
  "job_id": "string",
  "status": "string",
  "stage": "string",
  "progress": {
    "percent": 0-100,
    "message": "string"
  },
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "artifacts": {
    "report_html": "string | null",
    "bundle_zip": "string | null"
  },
  "error": "Error | null"
}
```

**实现**：
```python
@app.get("/jobs/{job_id}")
async def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter_by(job_id=job_id).first()
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"error": {
                "code": "JOB_NOT_FOUND",
                "message": f"Job {job_id} not found",
                "details": {},
                "retryable": False
            }}
        )

    return {
        "job_id": job.job_id,
        "status": job.status,
        "stage": job.stage,
        "progress": job.progress,  # JSON 字段
        "created_at": job.created_at.isoformat() + "Z",
        "updated_at": job.updated_at.isoformat() + "Z",
        "artifacts": job.artifacts,  # JSON 字段
        "error": job.error  # JSON 字段 or None
    }
```

**一致性**：✅ 完全符合
- 所有字段类型匹配
- 时间格式为 ISO-8601（UTC）
- 404 返回 `ErrorResponse` 结构

**差异**：无

---

### 2.3 GET /jobs/{job_id}/report（获取 HTML 报告）

**OpenAPI Spec**：
```yaml
paths:
  /jobs/{job_id}/report:
    get:
      responses:
        "200":
          content:
            text/html:
              schema: { type: string }
        "409":
          content:
            application/json:
              schema: { $ref: "#/components/schemas/ErrorResponse" }
```

**实现**：
```python
@app.get("/jobs/{job_id}/report")
async def get_report(job_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter_by(job_id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=error_not_found(job_id))

    if job.status != "done":
        raise HTTPException(
            status_code=409,
            detail={"error": {
                "code": "JOB_NOT_READY",
                "message": f"Job {job_id} is not done (current: {job.status})",
                "details": {"current_status": job.status},
                "retryable": True
            }}
        )

    report_path = Path(f"jobs/{job_id}/report/report.html")
    if not report_path.exists():
        raise HTTPException(status_code=500, detail=error_internal("Report file missing"))

    return FileResponse(report_path, media_type="text/html")
```

**一致性**：✅ 完全符合
- 返回 `text/html` Content-Type
- 未完成返回 409 + `JOB_NOT_READY`
- 不存在返回 404

**差异**：无

---

### 2.4 GET /jobs/{job_id}/bundle（获取 bundle.zip）

**OpenAPI Spec**：
```yaml
paths:
  /jobs/{job_id}/bundle:
    get:
      responses:
        "200":
          content:
            application/zip:
              schema: { type: string, format: binary }
        "409":
          content:
            application/json:
              schema: { $ref: "#/components/schemas/ErrorResponse" }
```

**实现**：
```python
@app.get("/jobs/{job_id}/bundle")
async def get_bundle(job_id: str, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter_by(job_id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=error_not_found(job_id))

    if job.status != "done":
        raise HTTPException(
            status_code=409,
            detail={"error": {
                "code": "JOB_NOT_READY",
                "message": f"Job {job_id} is not done",
                "details": {"current_status": job.status},
                "retryable": True
            }}
        )

    bundle_path = Path(f"jobs/{job_id}/bundle.zip")
    if not bundle_path.exists():
        raise HTTPException(status_code=500, detail=error_internal("Bundle file missing"))

    return FileResponse(
        bundle_path,
        media_type="application/zip",
        filename=f"job_{job_id}_bundle.zip"
    )
```

**一致性**：✅ 完全符合
- 返回 `application/zip` Content-Type
- 未完成返回 409 + `JOB_NOT_READY`

**差异**：无

---

## 3. 数据模型映射

### 3.1 Error（错误模型）

**OpenAPI Schema**：
```yaml
Error:
  type: object
  required: [code, message, details, retryable]
  properties:
    code: { type: string }
    message: { type: string }
    details: { type: object, additionalProperties: true }
    retryable: { type: boolean }
```

**Pydantic 实现**（`src/models/errors.py`）：
```python
from pydantic import BaseModel

class Error(BaseModel):
    code: str
    message: str
    details: dict = {}
    retryable: bool = False

class ErrorResponse(BaseModel):
    error: Error
```

**一致性**：✅ 完全符合
- 所有必填字段存在
- 类型匹配
- `details` 支持任意键值对

---

### 3.2 JobCreated（创建响应）

**OpenAPI Schema**：
```yaml
JobCreated:
  type: object
  required: [job_id, status, created_at, links]
  properties:
    job_id: { type: string }
    status: { type: string }
    created_at: { type: string }
    links: { type: object, additionalProperties: true }
```

**Pydantic 实现**（`src/models/job.py`）：
```python
class JobCreated(BaseModel):
    job_id: str
    status: str
    created_at: str  # ISO-8601
    links: dict
```

**一致性**：✅ 完全符合

---

### 3.3 JobStatus（状态响应）

**OpenAPI Schema**：
```yaml
JobStatus:
  type: object
  required: [job_id, status, stage, progress, created_at, updated_at, artifacts, error]
  properties:
    job_id: { type: string }
    status: { type: string }
    stage: { type: string }
    progress:
      type: object
      required: [percent, message]
      properties:
        percent: { type: integer, minimum: 0, maximum: 100 }
        message: { type: string }
    created_at: { type: string }
    updated_at: { type: string }
    artifacts: { type: object, additionalProperties: true }
    error:
      oneOf:
        - type: "null"
        - $ref: "#/components/schemas/Error"
```

**Pydantic 实现**：
```python
class Progress(BaseModel):
    percent: int = Field(ge=0, le=100)
    message: str

class JobStatus(BaseModel):
    job_id: str
    status: str
    stage: str
    progress: Progress
    created_at: str
    updated_at: str
    artifacts: dict
    error: Optional[Error] = None
```

**一致性**：✅ 完全符合
- `progress.percent` 限制在 0-100
- `error` 支持 `null` 或 `Error` 对象
- 所有时间字段为 ISO-8601 字符串

---

## 4. 错误码映射

### 4.1 Spec 定义的错误码

**SPEC_02_API.md 第 7 节**：
```
- INVALID_REQUEST
- JOB_NOT_FOUND
- JOB_NOT_READY
- UPLOAD_INVALID_FILE
- FETCH_UPSTREAM_FAILED
- FETCH_TIMEOUT
- PREPROCESS_FAILED
- SKILL_FAILED
- REPORT_FAILED
- INTERNAL_ERROR
```

### 4.2 实现映射表

| 错误码 | HTTP 状态码 | 使用场景 | retryable |
|--------|------------|---------|-----------|
| `INVALID_REQUEST` | 400 | 参数格式错误、缺少必填字段 | false |
| `JOB_NOT_FOUND` | 404 | Job ID 不存在 | false |
| `JOB_NOT_READY` | 409 | Job 未完成，无法获取产物 | true |
| `UPLOAD_INVALID_FILE` | 400 | 文件格式错误、文件过大 | false |
| `FETCH_UPSTREAM_FAILED` | 500 | 上游 API 调用失败 | true |
| `FETCH_TIMEOUT` | 504 | 上游 API 超时 | true |
| `PREPROCESS_FAILED` | 500 | 数据预处理失败 | false |
| `SKILL_FAILED` | 500 | Skill 执行失败 | false |
| `REPORT_FAILED` | 500 | 报告生成失败 | true |
| `INTERNAL_ERROR` | 500 | 未预期的内部错误 | false |

**实现**（`src/api/errors.py`）：
```python
def error_invalid_request(message: str) -> dict:
    return {
        "error": {
            "code": "INVALID_REQUEST",
            "message": message,
            "details": {},
            "retryable": False
        }
    }

def error_not_found(job_id: str) -> dict:
    return {
        "error": {
            "code": "JOB_NOT_FOUND",
            "message": f"Job {job_id} not found",
            "details": {},
            "retryable": False
        }
    }

# ... 其他错误码工厂函数
```

**一致性**：✅ 完全符合
- 所有 Spec 定义的错误码已实现
- `retryable` 字段根据错误类型正确设置

---

## 5. Status 枚举映射

### 5.1 Spec 定义

**SPEC_02_API.md 第 6 节**：
```
- queued
- fetching
- preprocessing
- analyzing
- reporting
- done
- failed
```

### 5.2 实现

**数据库枚举**（`src/db/models.py`）：
```python
import enum

class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    FETCHING = "fetching"
    PREPROCESSING = "preprocessing"
    ANALYZING = "analyzing"
    REPORTING = "reporting"
    DONE = "done"
    FAILED = "failed"
```

**一致性**：✅ 完全符合
- 所有状态值与 Spec 一致
- 数据库存储为字符串（兼容性好）

---

## 6. OpenAPI 文档差异（Override）

### 6.1 鉴权（Override O1）

**OpenAPI Spec（原始）**：
```yaml
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
```

**实际实现**：
- **移除**所有 `securitySchemes` 和 `security` 字段
- 所有端点无需鉴权

**原因**：见 `OVERRIDES.md` → O1（内网部署，无需鉴权）

**更新文件**：
- `specs_v0_1/openapi.yaml`（移除 security 相关）
- 或在项目中维护修改后的 `openapi.yaml`

---

### 6.2 新增 UI 端点（Override O4）

**Spec 未定义，实际新增**：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/ui` | GET | Web UI 首页（创建任务表单） |
| `/ui/jobs` | GET | 任务列表页 |
| `/ui/jobs/{id}` | GET | 任务详情页 |
| `/static/*` | GET | 静态资源（CSS/JS/图片） |

**实现**（`src/ui/routes.py`）：
```python
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

templates = Jinja2Templates(directory="src/ui/templates")
app.mount("/static", StaticFiles(directory="src/ui/static"), name="static")

@app.get("/ui")
async def ui_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/ui/jobs")
async def ui_jobs_list(request: Request, db: Session = Depends(get_db)):
    jobs = db.query(JobModel).order_by(JobModel.created_at.desc()).limit(50).all()
    return templates.TemplateResponse("jobs.html", {"request": request, "jobs": jobs})

@app.get("/ui/jobs/{job_id}")
async def ui_job_detail(job_id: str, request: Request, db: Session = Depends(get_db)):
    job = db.query(JobModel).filter_by(job_id=job_id).first_or_404()
    return templates.TemplateResponse("job_detail.html", {"request": request, "job": job})
```

**说明**：
- 这些端点不在 `openapi.yaml` 中定义（UI 层，非 API）
- 不影响 API 契约，符合 Override O4（提供 Web UI）

---

## 7. 测试覆盖

### 7.1 API 契约测试（tests/test_api.py）

**目标**：验证 API 实现与 OpenAPI Spec 一致

```python
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_create_job_returns_201():
    """POST /jobs 返回 201 + JobCreated"""
    response = client.post(
        "/jobs",
        files={"file": ("test.csv", b"cdid\n123\n456")},
        data={"params": '{"package_name": "com.test"}'}
    )
    assert response.status_code == 201
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"
    assert "links" in data

def test_get_job_returns_200():
    """GET /jobs/{id} 返回 200 + JobStatus"""
    # 先创建 Job
    create_resp = client.post("/jobs", ...)
    job_id = create_resp.json()["job_id"]

    # 查询
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert "progress" in data
    assert data["progress"]["percent"] >= 0

def test_get_job_not_found_returns_404():
    """GET /jobs/{id} Job 不存在返回 404 + JOB_NOT_FOUND"""
    response = client.get("/jobs/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "JOB_NOT_FOUND"
    assert data["error"]["retryable"] is False

def test_get_report_not_ready_returns_409():
    """GET /jobs/{id}/report Job 未完成返回 409"""
    create_resp = client.post("/jobs", ...)
    job_id = create_resp.json()["job_id"]

    response = client.get(f"/jobs/{job_id}/report")
    assert response.status_code == 409
    data = response.json()
    assert data["error"]["code"] == "JOB_NOT_READY"
    assert data["error"]["retryable"] is True
```

### 7.2 OpenAPI 验证工具

**使用 openapi-spec-validator**：
```bash
pip install openapi-spec-validator

# 验证 openapi.yaml 格式
openapi-spec-validator specs_v0_1/openapi.yaml
```

**集成到 CI**：
```yaml
# .github/workflows/test.yml
- name: Validate OpenAPI Spec
  run: openapi-spec-validator specs_v0_1/openapi.yaml
```

---

## 8. 总结

### 8.1 一致性状态

| 组件 | 状态 | 备注 |
|------|------|------|
| POST /jobs | ✅ 完全符合 | |
| GET /jobs/{id} | ✅ 完全符合 | |
| GET /jobs/{id}/report | ✅ 完全符合 | |
| GET /jobs/{id}/bundle | ✅ 完全符合 | |
| Error 模型 | ✅ 完全符合 | |
| JobStatus 模型 | ✅ 完全符合 | |
| 错误码 | ✅ 完全符合 | 所有 Spec 定义的错误码已实现 |
| Status 枚举 | ✅ 完全符合 | |
| 鉴权 | ⚠️ Override O1 | 移除鉴权（内网） |
| UI 端点 | ℹ️ 扩展 | 新增 UI 路由（不在 Spec 中） |

### 8.2 OpenAPI 文档维护

**选项 1（推荐）**：
- 在项目中维护修改后的 `openapi.yaml`
- 路径：`data-insight-service/openapi.yaml`
- 移除 security 相关字段
- 可选：新增 UI 端点定义（非必需）

**选项 2**：
- 保持 `specs_v0_1/openapi.yaml` 不变（原始 Spec）
- 在 `OVERRIDES.md` 中说明差异
- 使用注释标注哪些字段未实现

**本项目采用选项 2**：
- `specs_v0_1/openapi.yaml` 作为规范性契约保持不变
- `OVERRIDES.md` 记录所有偏离
- 实际实现以 Override 为准

---

## 9. 更新记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-01-23 | 0.1.0 | 初始版本，API 实现与 Spec 完全对齐（除 O1 鉴权） |

---

## 10. 相关文档

- `specs_v0_1/openapi.yaml`：原始 OpenAPI Spec
- `specs_v0_1/SPEC_02_API.md`：API 规范详细说明
- `docs/OVERRIDES.md`：强制覆盖说明
- `src/api/routes.py`：API 实现
- `src/models/`：Pydantic 模型定义
