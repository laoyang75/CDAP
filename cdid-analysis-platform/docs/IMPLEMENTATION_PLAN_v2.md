# CDID 数据分析平台 - 实施计划 v2.0（完整版）

**版本**: v2.0.0
**日期**: 2026-01-26
**变更**: 加入完整的管理后台（8 个 UI 页面）

---

## 计划概述

**实现范围**：完整版（用户端 + 管理端）
**UI Mockups**：基于 `docs/ui-mockups/` 中的 8 个完整页面

**总任务数**: 18 个任务（原 12 个 + 新增 6 个管理端任务）
**预估总时长**: 8-12 小时

---

## 批次 1：基础设施（任务 1-3）

### 任务 1：创建项目结构和配置

**目标**：搭建完整的项目目录结构，创建配置文件

**步骤**：

1. 创建目录结构
   ```bash
   mkdir -p cdid-analysis-platform/{src/{api,worker,db,ui/{templates/{user,admin},static/{css,js,images}},models,admin},config,skills/duofa-panduan,jobs,logs,tests}
   ```

2. 复制 UI mockups 到模板目录
   ```bash
   cp docs/ui-mockups/user-*.html src/ui/templates/user/
   cp docs/ui-mockups/admin-*.html src/ui/templates/admin/
   ```

3. 创建 `requirements.txt`
   ```txt
   fastapi==0.109.0
   uvicorn[standard]==0.27.0
   pydantic==2.5.0
   pydantic-settings==2.1.0
   sqlalchemy==2.0.25
   httpx==0.26.0
   pandas==2.1.4
   openpyxl==3.1.2
   jinja2==3.1.3
   python-multipart==0.0.6
   pytest==7.4.4
   pytest-asyncio==0.23.3
   bcrypt==4.1.2  # 密码加密（管理端需要）
   pyjwt==2.8.0   # JWT 认证（管理端需要）
   ```

4. 创建 `pyproject.toml`
   ```toml
   [project]
   name = "cdid-analysis-platform"
   version = "1.0.0"
   description = "CDID 数据分析平台 - 完整版（用户端 + 管理端）"
   requires-python = ">=3.11"

   [project.scripts]
   cdid-server = "src.api.main:start_server"
   cdid-worker = "src.worker.main:start_worker"
   cdid-admin = "src.admin.cli:main"
   ```

5. 创建 `config/config.yaml`
   ```yaml
   # 新增管理端配置
   admin:
     enabled: true
     secret_key: "your-secret-key-change-in-production"
     jwt_expire_hours: 24
     default_username: "admin"
     default_password: "admin123"  # 首次启动创建

   # 其他配置（同 v1.0）
   gemini: ...
   upstream: ...
   worker: ...
   ```

6. 创建 `.gitignore`

**验证**：
```bash
tree -L 3 cdid-analysis-platform/
python -c "import toml; toml.load(open('pyproject.toml'))"
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"
```

**预期输出**：目录结构完整，配置文件语法正确

---

### 任务 2：创建配置加载模块（同 v1.0）

**变更**：增加管理端配置项

```python
class Config(BaseSettings):
    # ... 原有配置

    # 管理端配置（新增）
    admin_enabled: bool = True
    admin_secret_key: str = "change-me-in-production"
    admin_jwt_expire_hours: int = 24
    admin_default_username: str = "admin"
    admin_default_password: str = "admin123"
```

**验证**：同 v1.0

---

### 任务 3：创建数据库模型

**变更**：增加管理端相关表

**新增模型**：

1. **User 表**（用户管理）
   ```python
   class User(Base):
       __tablename__ = "users"

       id = Column(Integer, primary_key=True)
       username = Column(String(50), unique=True, nullable=False)
       password_hash = Column(String(255), nullable=False)
       email = Column(String(100))
       role = Column(String(20), default="user")  # user | admin
       is_active = Column(Boolean, default=True)
       created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
       last_login = Column(DateTime)
   ```

2. **Pipeline 表**（流程配置）
   ```python
   class Pipeline(Base):
       __tablename__ = "pipelines"

       id = Column(Integer, primary_key=True)
       name = Column(String(100), nullable=False)
       description = Column(Text)
       config = Column(JSON)  # 流程配置（分析步骤、参数等）
       is_active = Column(Boolean, default=True)
       created_by = Column(Integer, ForeignKey("users.id"))
       created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
   ```

3. **Script 表**（自定义脚本）
   ```python
   class Script(Base):
       __tablename__ = "scripts"

       id = Column(Integer, primary_key=True)
       name = Column(String(100), nullable=False)
       description = Column(Text)
       script_type = Column(String(20))  # preprocessing | analysis | postprocessing
       code = Column(Text, nullable=False)  # Python 代码
       is_active = Column(Boolean, default=True)
       created_by = Column(Integer, ForeignKey("users.id"))
       created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
   ```

4. **ClientConfig 表**（客户端配置）
   ```python
   class ClientConfig(Base):
       __tablename__ = "client_configs"

       id = Column(Integer, primary_key=True)
       key = Column(String(100), unique=True, nullable=False)
       value = Column(Text)
       description = Column(String(255))
       updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
   ```

**验证**：同 v1.0，增加新表的测试

---

## 批次 1 完成检查点

**完成标志**：
- ✅ 项目结构完整（含 admin 目录）
- ✅ UI mockups 已复制到模板目录
- ✅ 数据库模型创建成功（4 个新表）
- ✅ 所有测试通过

---

## 批次 2：内网 API 客户端 + 分析器（任务 4-5）

（同 v1.0，无变化）

---

## 批次 3：Gemini CLI Skill + 报告生成（任务 6-7）

（同 v1.0，无变化）

---

## 批次 4：Worker 主循环（任务 8-9）

（同 v1.0，无变化）

---

## 批次 5：用户端 API + UI（任务 10-11）

### 任务 10：实现用户端 FastAPI 应用

**目标**：实现用户端 3 个核心 API 端点

（同 v1.0，无变化）

---

### 任务 11：实现用户端 Web UI

**目标**：集成 UI mockups，实现 3 个用户端页面

**步骤**：

1. 修改模板文件，使其成为 Jinja2 模板
   - `user-create-task.html` → 添加表单提交逻辑
   - `user-task-list.html` → 使用 `{% for job in jobs %}` 渲染任务列表
   - `user-task-detail.html` → 使用 `{{ job.status }}` 渲染任务状态

2. 创建 `src/ui/static/js/app.js`（轮询逻辑）
   ```javascript
   // 基于 mockups 中的 JS，提取轮询逻辑
   function pollJobStatus(jobId) {
       const interval = setInterval(async () => {
           const response = await fetch(`/api/jobs/${jobId}`);
           const data = await response.json();

           updateProgress(data.progress);
           updateStatus(data.status);

           if (data.status === 'done' || data.status === 'failed') {
               clearInterval(interval);
               if (data.status === 'done') {
                   loadReport(jobId);
               }
           }
       }, 3000);
   }
   ```

3. 在 `src/api/main.py` 添加 UI 路由
   ```python
   @app.get("/ui")
   async def ui_index(request: Request):
       return templates.TemplateResponse("user/user-create-task.html", {"request": request})

   @app.get("/ui/tasks")
   async def ui_task_list(request: Request, db: Session = Depends(get_db)):
       jobs = db.query(Job).order_by(Job.created_at.desc()).limit(50).all()
       return templates.TemplateResponse("user/user-task-list.html", {"request": request, "jobs": jobs})

   @app.get("/ui/tasks/{job_id}")
   async def ui_task_detail(job_id: str, request: Request, db: Session = Depends(get_db)):
       job = db.query(Job).filter_by(id=job_id).first()
       if not job:
           raise HTTPException(404)
       return templates.TemplateResponse("user/user-task-detail.html", {"request": request, "job": job})
   ```

**验证**：
- 手动测试：访问 http://localhost:8000/ui
- 检查表单提交、任务列表、详情页轮询

**预期输出**：
- UI 正常显示
- 表单可提交
- 任务列表渲染正确
- 详情页实时更新

---

## 批次 5 完成检查点

**完成标志**：
- ✅ 用户端 API 实现完成
- ✅ 用户端 3 个页面正常工作
- ✅ 端到端流程可用

---

## 批次 6：管理端后台 - 用户管理（任务 12-13）

### 任务 12：实现认证与用户管理 API

**目标**：实现 JWT 认证 + 用户管理接口

**步骤**：

1. 创建 `src/admin/auth.py`（认证中间件）
   ```python
   from fastapi import Depends, HTTPException, status
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
   import jwt

   security = HTTPBearer()

   def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
       """验证 JWT Token"""
       try:
           payload = jwt.decode(
               credentials.credentials,
               config.admin_secret_key,
               algorithms=["HS256"]
           )
           return payload
       except jwt.ExpiredSignatureError:
           raise HTTPException(status_code=401, detail="Token expired")
       except jwt.InvalidTokenError:
           raise HTTPException(status_code=401, detail="Invalid token")

   def require_admin(payload: dict = Depends(verify_token)):
       """要求管理员权限"""
       if payload.get("role") != "admin":
           raise HTTPException(status_code=403, detail="Admin required")
       return payload
   ```

2. 创建 `src/admin/routes.py`（管理端 API）
   ```python
   from fastapi import APIRouter, Depends
   from src.admin.auth import require_admin

   admin_router = APIRouter(prefix="/admin/api", tags=["Admin"])

   # 登录
   @admin_router.post("/login")
   async def admin_login(username: str, password: str):
       user = db.query(User).filter_by(username=username).first()
       if not user or not verify_password(password, user.password_hash):
           raise HTTPException(401, "Invalid credentials")

       token = jwt.encode({
           "user_id": user.id,
           "username": user.username,
           "role": user.role,
           "exp": datetime.now(timezone.utc) + timedelta(hours=config.admin_jwt_expire_hours)
       }, config.admin_secret_key, algorithm="HS256")

       return {"token": token, "user": {...}}

   # 用户管理
   @admin_router.get("/users")
   async def list_users(current_user: dict = Depends(require_admin)):
       users = db.query(User).all()
       return {"users": [u.to_dict() for u in users]}

   @admin_router.post("/users")
   async def create_user(user_data: UserCreate, current_user: dict = Depends(require_admin)):
       # 创建用户逻辑
       pass

   @admin_router.put("/users/{user_id}")
   async def update_user(user_id: int, user_data: UserUpdate, current_user: dict = Depends(require_admin)):
       # 更新用户逻辑
       pass

   @admin_router.delete("/users/{user_id}")
   async def delete_user(user_id: int, current_user: dict = Depends(require_admin)):
       # 删除用户逻辑
       pass
   ```

3. 在 `src/api/main.py` 注册管理端路由
   ```python
   from src.admin.routes import admin_router
   app.include_router(admin_router)
   ```

**验证**：
```python
# tests/test_admin_auth.py
def test_admin_login():
    response = client.post("/admin/api/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    assert "token" in response.json()

def test_list_users_without_token():
    response = client.get("/admin/api/users")
    assert response.status_code == 401

def test_list_users_with_token():
    # 先登录获取 token
    login_resp = client.post("/admin/api/login", ...)
    token = login_resp.json()["token"]

    # 使用 token 访问
    response = client.get("/admin/api/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
```

**预期输出**：
- 登录成功返回 JWT token
- 未认证访问返回 401
- 认证后可访问管理端 API

---

### 任务 13：实现用户管理 UI

**目标**：集成 `admin-user-management.html`

**步骤**：

1. 修改模板，添加 Jinja2 变量
   ```html
   <!-- admin-user-management.html -->
   <tbody>
   {% for user in users %}
   <tr>
       <td>{{ user.id }}</td>
       <td>{{ user.username }}</td>
       <td>{{ user.email }}</td>
       <td><span class="badge bg-{% if user.role == 'admin' %}danger{% else %}info{% endif %}">{{ user.role }}</span></td>
       <td><span class="badge bg-{% if user.is_active %}success{% else %}secondary{% endif %}">{% if user.is_active %}活跃{% else %}禁用{% endif %}</span></td>
       <td>{{ user.created_at }}</td>
       <td>
           <button class="btn btn-sm btn-primary" onclick="editUser({{ user.id }})">编辑</button>
           <button class="btn btn-sm btn-danger" onclick="deleteUser({{ user.id }})">删除</button>
       </td>
   </tr>
   {% endfor %}
   </tbody>
   ```

2. 创建 `src/ui/static/js/admin.js`（管理端 JS）
   ```javascript
   // JWT Token 管理
   function getToken() {
       return localStorage.getItem('admin_token');
   }

   function setToken(token) {
       localStorage.setItem('admin_token', token);
   }

   // 认证请求封装
   async function adminFetch(url, options = {}) {
       const token = getToken();
       if (!token) {
           window.location.href = '/admin/login';
           return;
       }

       options.headers = {
           ...options.headers,
           'Authorization': `Bearer ${token}`
       };

       const response = await fetch(url, options);
       if (response.status === 401) {
           localStorage.removeItem('admin_token');
           window.location.href = '/admin/login';
       }
       return response;
   }

   // 用户管理函数
   async function loadUsers() {
       const response = await adminFetch('/admin/api/users');
       const data = await response.json();
       renderUsersTable(data.users);
   }

   async function createUser(userData) {
       await adminFetch('/admin/api/users', {
           method: 'POST',
           headers: {'Content-Type': 'application/json'},
           body: JSON.stringify(userData)
       });
       loadUsers();
   }
   ```

3. 添加管理端 UI 路由
   ```python
   # src/api/main.py

   @app.get("/admin/login")
   async def admin_login_page(request: Request):
       return templates.TemplateResponse("admin/admin-login.html", {"request": request})

   @app.get("/admin/users")
   async def admin_users_page(request: Request):
       # 注意：这里不做认证检查，由前端 JS 处理
       return templates.TemplateResponse("admin/admin-user-management.html", {"request": request})
   ```

**验证**：
- 访问 http://localhost:8000/admin/login
- 登录后访问 http://localhost:8000/admin/users
- 测试增删改查功能

---

## 批次 6 完成检查点

**完成标志**：
- ✅ JWT 认证实现
- ✅ 用户管理 API 完成
- ✅ 用户管理 UI 正常工作

---

## 批次 7：管理端后台 - 配置与监控（任务 14-15）

### 任务 14：实现客户端配置 API + UI

**目标**：集成 `admin-client-config.html`，实现配置管理

**API**：
```python
@admin_router.get("/configs")
async def list_configs(current_user: dict = Depends(require_admin)):
    configs = db.query(ClientConfig).all()
    return {"configs": [c.to_dict() for c in configs]}

@admin_router.put("/configs/{key}")
async def update_config(key: str, value: str, current_user: dict = Depends(require_admin)):
    config = db.query(ClientConfig).filter_by(key=key).first()
    if not config:
        config = ClientConfig(key=key, value=value)
        db.add(config)
    else:
        config.value = value
        config.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True}
```

**UI**：修改 `admin-client-config.html`，加载配置并支持编辑

**验证**：
- 访问 http://localhost:8000/admin/config
- 修改配置（如 Gemini CLI 路径）
- 确认配置已保存

---

### 任务 15：实现任务监控 API + UI

**目标**：集成 `admin-task-monitoring.html`，实现实时任务监控

**API**：
```python
@admin_router.get("/tasks/stats")
async def get_task_stats(current_user: dict = Depends(require_admin)):
    """获取任务统计"""
    total = db.query(Job).count()
    queued = db.query(Job).filter_by(status="queued").count()
    running = db.query(Job).filter(Job.status.in_(["fetching", "analyzing", "reporting"])).count()
    done = db.query(Job).filter_by(status="done").count()
    failed = db.query(Job).filter_by(status="failed").count()

    return {
        "total": total,
        "queued": queued,
        "running": running,
        "done": done,
        "failed": failed
    }

@admin_router.get("/tasks/realtime")
async def get_realtime_tasks(current_user: dict = Depends(require_admin)):
    """获取实时任务列表（最近 50 个）"""
    tasks = db.query(Job).order_by(Job.updated_at.desc()).limit(50).all()
    return {"tasks": [t.to_dict() for t in tasks]}
```

**UI**：修改 `admin-task-monitoring.html`，实现实时刷新

**验证**：
- 访问 http://localhost:8000/admin/monitoring
- 查看任务统计图表
- 确认实时任务列表更新

---

## 批次 7 完成检查点

**完成标志**：
- ✅ 配置管理功能完成
- ✅ 任务监控大屏正常显示
- ✅ 实时数据刷新正常

---

## 批次 8：管理端后台 - 高级功能（任务 16-17）

### 任务 16：实现流程管理 API + UI

**目标**：集成 `admin-pipeline-management.html`，实现自定义分析流程

**API**：
```python
@admin_router.get("/pipelines")
async def list_pipelines(current_user: dict = Depends(require_admin)):
    pipelines = db.query(Pipeline).all()
    return {"pipelines": [p.to_dict() for p in pipelines]}

@admin_router.post("/pipelines")
async def create_pipeline(pipeline_data: PipelineCreate, current_user: dict = Depends(require_admin)):
    pipeline = Pipeline(**pipeline_data.dict(), created_by=current_user["user_id"])
    db.add(pipeline)
    db.commit()
    return {"success": True, "pipeline_id": pipeline.id}

@admin_router.put("/pipelines/{pipeline_id}")
async def update_pipeline(pipeline_id: int, pipeline_data: PipelineUpdate, current_user: dict = Depends(require_admin)):
    # 更新流程配置
    pass
```

**UI**：修改 `admin-pipeline-management.html`，支持可视化流程编辑

**验证**：
- 创建自定义流程
- 编辑流程配置
- 激活/停用流程

---

### 任务 17：实现脚本编辑器 API + UI

**目标**：集成 `admin-script-editor.html`，实现自定义 Python 脚本

**API**：
```python
@admin_router.get("/scripts")
async def list_scripts(current_user: dict = Depends(require_admin)):
    scripts = db.query(Script).all()
    return {"scripts": [s.to_dict() for s in scripts]}

@admin_router.post("/scripts")
async def create_script(script_data: ScriptCreate, current_user: dict = Depends(require_admin)):
    script = Script(**script_data.dict(), created_by=current_user["user_id"])
    db.add(script)
    db.commit()
    return {"success": True, "script_id": script.id}

@admin_router.post("/scripts/{script_id}/test")
async def test_script(script_id: int, test_data: dict, current_user: dict = Depends(require_admin)):
    """测试脚本执行"""
    script = db.query(Script).filter_by(id=script_id).first()
    # 在沙箱环境中执行脚本
    # 返回执行结果
    pass
```

**UI**：修改 `admin-script-editor.html`，集成代码编辑器（如 CodeMirror）

**验证**：
- 创建自定义脚本
- 在线编辑代码
- 测试脚本执行

---

## 批次 8 完成检查点

**完成标志**：
- ✅ 流程管理功能完成
- ✅ 脚本编辑器可用
- ✅ 自定义脚本可测试执行

---

## 批次 9：端到端测试与部署（任务 18）

### 任务 18：端到端测试与 Docker 部署

**目标**：完整测试所有功能，创建 Docker 镜像

**步骤**：

1. 用户端完整流程测试
   - 创建任务 → 监控进度 → 查看报告
   - 使用 `xuqiu/demo/波克问题数据.csv`

2. 管理端完整流程测试
   - 用户管理：创建/编辑/删除用户
   - 配置管理：修改 Gemini CLI 路径
   - 任务监控：查看实时任务状态
   - 流程管理：创建自定义流程
   - 脚本管理：编写自定义脚本

3. 创建 Dockerfile
   ```dockerfile
   FROM python:3.11-slim

   # 安装 Node.js（Gemini CLI 依赖）
   RUN apt-get update && apt-get install -y nodejs npm curl

   # 安装 Gemini CLI
   RUN npm install -g @google/generative-ai-cli@0.25.2

   # 创建 Gemini CLI Skills 目录
   RUN mkdir -p /root/.gemini/skills

   # 复制 Skill 文件
   COPY skills/duofa-panduan /root/.gemini/skills/duofa-panduan

   # 安装 Python 依赖
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt

   # 复制代码
   COPY . .

   # 初始化数据库
   RUN python -c "from src.db.connection import init_db; from src.config import Config; init_db(Config.load_from_yaml())"

   # 创建默认管理员账户
   RUN python -c "from src.admin.init import create_default_admin; create_default_admin()"

   # 暴露端口
   EXPOSE 8000

   # 启动命令（API + Worker）
   CMD ["sh", "-c", "python src/worker/main.py & uvicorn src.api.main:app --host 0.0.0.0 --port 8000"]
   ```

4. 创建 docker-compose.yml

5. 测试 Docker 部署

**验证**：
- 所有功能正常
- Docker 容器稳定运行
- 文档完整

---

## 批次 9 完成检查点

**完成标志**：
- ✅ 端到端测试通过
- ✅ Docker 部署成功
- ✅ 所有 8 个 UI 页面验证完成

---

## 最终交付物

### 代码
1. ✅ 完整项目代码
2. ✅ 8 个 UI 页面（用户端 3 + 管理端 5）
3. ✅ 完整的后端 API（用户端 + 管理端）
4. ✅ Worker + Gemini CLI Skill
5. ✅ 测试用例

### 文档
1. ✅ README.md（使用说明）
2. ✅ 用户手册（如何使用用户端）
3. ✅ 管理员手册（如何使用管理端）
4. ✅ API 文档（OpenAPI）
5. ✅ 部署文档（Docker）

### 演示
1. ✅ 端到端测试视频
2. ✅ 管理后台演示视频
3. ✅ 生成的报告示例

---

## 工作量评估

| 批次 | 任务数 | 预估时长 | 累计时长 |
|------|--------|---------|---------|
| 批次 1 | 3 | 1-1.5h | 1-1.5h |
| 批次 2 | 2 | 1-1.5h | 2-3h |
| 批次 3 | 2 | 1-1.5h | 3-4.5h |
| 批次 4 | 2 | 1-1.5h | 4-6h |
| 批次 5 | 2 | 1.5-2h | 5.5-8h |
| 批次 6 | 2 | 1.5-2h | 7-10h |
| 批次 7 | 2 | 1-1.5h | 8-11.5h |
| 批次 8 | 2 | 1-1.5h | 9-13h |
| 批次 9 | 1 | 1-1.5h | 10-14.5h |

**总计**：18 个任务，预估 10-15 小时

---

## 执行策略

1. **按批次执行**：每批次完成后报告，等待反馈
2. **MVP 优先**：先完成批次 1-5（用户端），确保核心流程可用
3. **管理端后置**：批次 6-8（管理端）可根据实际需求调整
4. **遇阻停止**：遇到技术问题立即停止，不猜测

---

**准备就绪！等待执行指令。** 🚀
