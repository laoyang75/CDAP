# CDID 数据分析平台 - 实施计划

**版本**: v1.0.0
**日期**: 2026-01-23
**基于**: 方案设计 v1.1

---

## 计划概述

本计划按照 **执行批次** 组织，每个批次包含 2-3 个相关任务。每批次完成后需要验证并报告，等待反馈后继续下一批次。

**总任务数**: 12 个任务
**预估总时长**: 4-6 小时（纯开发时间）

---

## 批次 1：基础设施（任务 1-3）

### 任务 1：创建项目结构和配置

**目标**：搭建完整的项目目录结构，创建配置文件

**步骤**：

1. 创建目录结构
   ```bash
   mkdir -p cdid-analysis-platform/{src/{api,worker,db,ui/{templates,static},models},config,skills/duofa-panduan,jobs,logs,tests}
   ```

2. 创建 `requirements.txt`
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
   ```

3. 创建 `pyproject.toml`
   ```toml
   [project]
   name = "cdid-analysis-platform"
   version = "0.1.0"
   description = "CDID 数据分析平台 - Web 化的 Gemini CLI Skills"
   requires-python = ">=3.11"

   [project.scripts]
   cdid-server = "src.api.main:start_server"
   cdid-worker = "src.worker.main:start_worker"
   ```

4. 创建 `config/config.yaml`（参考方案设计 v1.1 第 10 节）

5. 创建 `.gitignore`
   ```
   __pycache__/
   *.pyc
   .pytest_cache/
   jobs/
   logs/
   *.db
   .env
   ```

**验证**：
```bash
# 1. 检查目录结构
tree -L 2 cdid-analysis-platform/

# 2. 验证 Python 依赖语法
python -c "import toml; toml.load(open('pyproject.toml'))"

# 3. 验证 YAML 配置语法
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"
```

**预期输出**：
- 目录结构完整
- 配置文件语法正确
- 无错误信息

---

### 任务 2：创建配置加载模块

**目标**：实现配置加载器，支持 YAML + 环境变量

**步骤**：

1. 创建 `src/config.py`（参考 data-insight-service 的实现，但简化）

2. 关键配置项：
   ```python
   class Config(BaseSettings):
       # Gemini CLI
       gemini_cli_path: str = "gemini"
       gemini_skill_name: str = "duofa-panduan"
       gemini_timeout: int = 300

       # 多发检测
       duofa_threshold: float = 2.0

       # 内网 API
       upstream_base_url: str = "http://172.17.129.204:6829"
       upstream_timeout: int = 30
       upstream_poll_interval: int = 30
       upstream_max_poll_time: int = 1800

       # 数据库
       database_url: str = "sqlite:///./jobs.db"

       # Worker
       worker_poll_interval: int = 5

       # API Server
       api_host: str = "0.0.0.0"
       api_port: int = 8000
   ```

3. 支持环境变量覆盖（`CDID_*` 前缀）

**验证**：
```python
# tests/test_config.py
def test_config_load():
    config = Config.load_from_yaml("config/config.yaml")
    assert config.gemini_cli_path == "gemini"
    assert config.duofa_threshold == 2.0

def test_config_env_override():
    import os
    os.environ["CDID_GEMINI_CLI_PATH"] = "/custom/gemini"
    config = Config.load_from_yaml()
    assert config.gemini_cli_path == "/custom/gemini"
```

**预期输出**：
```
tests/test_config.py::test_config_load PASSED
tests/test_config.py::test_config_env_override PASSED
```

---

### 任务 3：创建数据库模型

**目标**：定义 SQLAlchemy ORM 模型

**步骤**：

1. 创建 `src/db/models.py`
   ```python
   from sqlalchemy import Column, String, Integer, DateTime, JSON, Text
   from sqlalchemy.ext.declarative import declarative_base
   from datetime import datetime, timezone

   Base = declarative_base()

   class Job(Base):
       __tablename__ = "jobs"

       id = Column(String(26), primary_key=True)  # ULID
       name = Column(String(255), nullable=False)
       package_name = Column(String(255), nullable=False)
       start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
       end_date = Column(String(10), nullable=False)
       message_types = Column(JSON, nullable=False)  # ["dna", "daa"]

       status = Column(String(20), nullable=False, default="queued")
       progress = Column(Integer, default=0)
       progress_message = Column(String(255), default="")

       input_file_path = Column(String(500))
       raw_data_path = Column(String(500))
       report_path = Column(String(500))

       error = Column(Text)
       insight_task_id = Column(String(50))

       created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
       updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
   ```

2. 创建 `src/db/connection.py`
   ```python
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   from src.db.models import Base
   from src.config import Config

   def init_db(config: Config):
       engine = create_engine(config.database_url)
       Base.metadata.create_all(engine)
       return engine

   def get_session(engine):
       Session = sessionmaker(bind=engine)
       return Session()
   ```

**验证**：
```python
# tests/test_db.py
def test_init_db():
    config = Config(database_url="sqlite:///./test.db")
    engine = init_db(config)

    session = get_session(engine)
    assert session is not None

    # 清理
    import os
    os.remove("test.db")

def test_job_create():
    config = Config(database_url="sqlite:///./test.db")
    engine = init_db(config)
    session = get_session(engine)

    job = Job(
        id="01J1A2B3C4D5E6F7G8H9K0M1",
        name="测试任务",
        package_name="com.test",
        start_date="2026-01-01",
        end_date="2026-01-07",
        message_types=["dna"]
    )
    session.add(job)
    session.commit()

    fetched = session.query(Job).filter_by(id=job.id).first()
    assert fetched.name == "测试任务"

    # 清理
    session.close()
    os.remove("test.db")
```

**预期输出**：
```
tests/test_db.py::test_init_db PASSED
tests/test_db.py::test_job_create PASSED
```

---

## 批次 1 完成检查点

**完成标志**：
- ✅ 项目结构完整
- ✅ 配置加载正常
- ✅ 数据库模型创建成功
- ✅ 所有测试通过

**报告内容**：
- 目录树截图
- `pytest tests/` 输出
- 配置文件内容

---

## 批次 2：内网 API 客户端（任务 4-5）

### 任务 4：实现内网 API 客户端

**目标**：封装调用 `172.17.129.204:6829` 的三个接口

**步骤**：

1. 创建 `src/worker/insight_client.py`（参考 `xuqiu/gemini/insight/SKILL.md`）

2. 实现三个方法：
   ```python
   class InsightClient:
       async def create_task(self, name, package_name, file_path, start_date, end_date, message_types):
           """创建任务，返回 task_id"""

       async def query_task_status(self, task_id):
           """查询任务状态，返回 {status, oss_url}"""

       async def download_result(self, oss_url, save_path):
           """下载结果文件"""
   ```

3. 错误处理：
   - 网络错误：重试 3 次
   - HTTP 错误：抛出异常
   - 超时：使用配置的 timeout

**验证**：
```python
# tests/test_insight_client.py
@pytest.mark.asyncio
async def test_create_task(mocker):
    # Mock httpx.AsyncClient
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"code": 0, "data": {"task_id": "123456"}}
    mock_client = mocker.patch("httpx.AsyncClient.post", return_value=mock_response)

    client = InsightClient(config)
    task_id = await client.create_task(
        name="测试",
        package_name="com.test",
        file_path="test.csv",
        start_date="2026-01-01",
        end_date="2026-01-07",
        message_types=["dna"]
    )

    assert task_id == "123456"
    assert mock_client.called

# 注意：真实 API 测试需要内网环境，这里使用 mock
```

**预期输出**：
```
tests/test_insight_client.py::test_create_task PASSED
tests/test_insight_client.py::test_query_task_status PASSED
tests/test_insight_client.py::test_download_result PASSED
```

---

### 任务 5：实现多发检测分析器

**目标**：实现 `did去重数 / oaid去重数 > 2` 的判定逻辑

**步骤**：

1. 创建 `src/worker/duofa_analyzer.py`（参考方案设计 v1.1 第 4.2 节）

2. 核心逻辑：
   ```python
   class DuofaAnalyzer:
       def analyze(self, input_file: str, job_info: dict) -> dict:
           df = pd.read_excel(input_file)

           unique_did_count = df['did'].nunique()
           unique_oaid_count = df['oaid'].nunique()
           ratio = unique_did_count / unique_oaid_count if unique_oaid_count > 0 else 0
           is_duofa = ratio > self.config.duofa_threshold

           # 构建数据包（含背景知识）
           return {
               "task_info": {...},
               "processing": {...},
               "statistics": {
                   "unique_did_count": int(unique_did_count),
                   "unique_oaid_count": int(unique_oaid_count),
                   "ratio": round(ratio, 2),
                   "is_duofa": is_duofa
               },
               "background": {...},
               "raw_data_summary": {...}
           }
   ```

**验证**：
```python
# tests/test_duofa_analyzer.py
def test_duofa_detection_positive():
    """测试多发检测（正例）"""
    # 创建测试数据：10 个 did，3 个 oaid（ratio = 3.33 > 2）
    df = pd.DataFrame({
        'did': [f'did_{i}' for i in range(10)],
        'oaid': ['oaid_1'] * 4 + ['oaid_2'] * 3 + ['oaid_3'] * 3
    })
    df.to_excel("test_duofa.xlsx", index=False)

    analyzer = DuofaAnalyzer(config)
    result = analyzer.analyze("test_duofa.xlsx", {"name": "测试"})

    assert result['statistics']['unique_did_count'] == 10
    assert result['statistics']['unique_oaid_count'] == 3
    assert result['statistics']['ratio'] == 3.33
    assert result['statistics']['is_duofa'] is True

    os.remove("test_duofa.xlsx")

def test_duofa_detection_negative():
    """测试多发检测（负例）"""
    # 创建测试数据：10 个 did，10 个 oaid（ratio = 1.0 <= 2）
    df = pd.DataFrame({
        'did': [f'did_{i}' for i in range(10)],
        'oaid': [f'oaid_{i}' for i in range(10)]
    })
    df.to_excel("test_normal.xlsx", index=False)

    analyzer = DuofaAnalyzer(config)
    result = analyzer.analyze("test_normal.xlsx", {"name": "测试"})

    assert result['statistics']['ratio'] == 1.0
    assert result['statistics']['is_duofa'] is False

    os.remove("test_normal.xlsx")

def test_analyze_with_real_data():
    """使用真实测试数据"""
    analyzer = DuofaAnalyzer(config)

    # 使用 xuqiu/demo/波克问题数据.csv
    # 注意：需要先通过内网 API 获取 did/oaid 数据，这里暂时跳过
    pass
```

**预期输出**：
```
tests/test_duofa_analyzer.py::test_duofa_detection_positive PASSED
tests/test_duofa_analyzer.py::test_duofa_detection_negative PASSED
```

---

## 批次 2 完成检查点

**完成标志**：
- ✅ 内网 API 客户端实现（带 mock 测试）
- ✅ 多发检测分析器实现
- ✅ 测试覆盖核心逻辑

**报告内容**：
- `pytest tests/test_insight_client.py -v` 输出
- `pytest tests/test_duofa_analyzer.py -v` 输出
- 分析器输出的数据包示例（JSON）

---

## 批次 3：Gemini CLI Skill + 报告生成（任务 6-7）

### 任务 6：创建 Gemini CLI Skill

**目标**：在 `~/.gemini/skills/duofa-panduan/` 创建 Skill 文件

**步骤**：

1. 创建目录
   ```bash
   mkdir -p ~/.gemini/skills/duofa-panduan
   ```

2. 复制 Skill 文件
   ```bash
   cp skills/duofa-panduan/SKILL.md ~/.gemini/skills/duofa-panduan/SKILL.md
   ```

3. 编写 `skills/duofa-panduan/SKILL.md`（参考方案设计 v1.1 第 4.3 节）

**验证**：
```bash
# 1. 检查文件存在
ls -la ~/.gemini/skills/duofa-panduan/SKILL.md

# 2. 验证 Gemini CLI 能否识别 Skill
gemini skills list | grep duofa-panduan

# 3. 手动测试 Skill（创建测试数据包）
cat > test_data.json <<EOF
{
  "task_info": {"task_name": "测试", "package_name": "com.test"},
  "statistics": {"unique_did_count": 100, "unique_oaid_count": 30, "ratio": 3.33, "is_duofa": true},
  "background": {"duofa_definition": "...", "threshold": 2.0}
}
EOF

cat test_data.json | gemini -p "使用 duofa-panduan skill 生成报告" > test_report.html

# 4. 检查生成的 HTML
grep "<html" test_report.html
grep "多发" test_report.html
```

**预期输出**：
- Skill 文件存在
- `gemini skills list` 显示 duofa-panduan
- 生成的 HTML 包含完整标签和多发相关内容

---

### 任务 7：实现 Gemini CLI 调用器

**目标**：封装 Gemini CLI 调用逻辑

**步骤**：

1. 创建 `src/worker/gemini_reporter.py`（参考方案设计 v1.1 第 4.4 节）

2. 关键实现：
   ```python
   class GeminiReporter:
       def __init__(self, config):
           self.gemini_cli_path = config.gemini_cli_path
           self.skill_name = config.gemini_skill_name
           self.timeout = config.gemini_timeout

       def generate_report(self, analysis_result: dict) -> str:
           result_json = json.dumps(analysis_result, ensure_ascii=False, indent=2)
           prompt = f"使用 {self.skill_name} skill 根据以下数据生成多发检测报告"

           cmd = [self.gemini_cli_path, "-p", prompt]

           process = subprocess.Popen(
               cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
               stderr=subprocess.PIPE, text=True, timeout=self.timeout
           )

           stdout, stderr = process.communicate(input=result_json)

           if process.returncode != 0:
               raise RuntimeError(f"Gemini CLI 失败: {stderr}")

           return stdout
   ```

**验证**：
```python
# tests/test_gemini_reporter.py
def test_generate_report():
    config = Config(gemini_cli_path="gemini")
    reporter = GeminiReporter(config)

    # 使用测试数据包
    analysis_result = {
        "task_info": {"task_name": "测试", "package_name": "com.test"},
        "statistics": {"unique_did_count": 100, "unique_oaid_count": 30, "ratio": 3.33, "is_duofa": True},
        "background": {"duofa_definition": "多发定义", "threshold": 2.0}
    }

    html = reporter.generate_report(analysis_result)

    assert "<html" in html
    assert "多发" in html or "Duofa" in html.lower()
    assert "3.33" in html

    # 保存到文件检查
    with open("test_report_output.html", "w") as f:
        f.write(html)

    print("报告已保存到 test_report_output.html，请手动检查")
```

**预期输出**：
```
tests/test_gemini_reporter.py::test_generate_report PASSED
报告已保存到 test_report_output.html，请手动检查
```

**手动检查**：
- 在浏览器中打开 `test_report_output.html`
- 确认报告格式美观、内容完整

---

## 批次 3 完成检查点

**完成标志**：
- ✅ Gemini CLI Skill 创建成功
- ✅ Gemini CLI 能识别 Skill
- ✅ 报告生成器实现完成
- ✅ 生成的 HTML 报告格式正确

**报告内容**：
- `gemini skills list` 输出截图
- 生成的测试报告（test_report_output.html）截图
- pytest 测试结果

---

## 批次 4：Worker 主循环（任务 8-9）

### 任务 8：实现 Worker 主循环

**目标**：实现 FIFO 单线程任务处理器

**步骤**：

1. 创建 `src/worker/main.py`（参考方案设计 v1.1 第 4.5 节）

2. 核心逻辑：
   ```python
   class Worker:
       def __init__(self, config, db_session):
           self.config = config
           self.db = db_session
           self.insight_client = InsightClient(config)
           self.analyzer = DuofaAnalyzer(config)
           self.reporter = GeminiReporter(config)

       async def run_forever(self):
           while True:
               job = self.get_next_job()  # SELECT ... WHERE status='queued' ORDER BY created_at LIMIT 1

               if not job:
                   await asyncio.sleep(self.config.worker_poll_interval)
                   continue

               try:
                   await self.process_job(job)
               except Exception as e:
                   self.mark_failed(job.id, str(e))

       async def process_job(self, job):
           # 阶段 1: Fetching
           # 阶段 2: Analyzing
           # 阶段 3: Reporting
   ```

3. 状态更新函数：
   ```python
   def update_status(self, job_id, status, progress=None, progress_message=None):
       job = self.db.query(Job).filter_by(id=job_id).first()
       job.status = status
       if progress is not None:
           job.progress = progress
       if progress_message:
           job.progress_message = progress_message
       job.updated_at = datetime.now(timezone.utc)
       self.db.commit()
   ```

**验证**：
```python
# tests/test_worker.py
@pytest.mark.asyncio
async def test_worker_fifo():
    """测试 FIFO 队列"""
    # 创建 3 个任务
    job1 = Job(id="job1", name="任务1", ...)
    job2 = Job(id="job2", name="任务2", ...)
    job3 = Job(id="job3", name="任务3", ...)

    db.add_all([job1, job2, job3])
    db.commit()

    # Worker 应该按顺序取出 job1
    worker = Worker(config, db)
    next_job = worker.get_next_job()

    assert next_job.id == "job1"

@pytest.mark.asyncio
async def test_worker_process_job(mocker):
    """测试任务处理流程（使用 mock）"""
    # Mock 所有外部依赖
    mocker.patch.object(InsightClient, 'create_task', return_value="task123")
    mocker.patch.object(InsightClient, 'query_task_status', return_value={"status": "success", "oss_url": "http://..."})
    mocker.patch.object(InsightClient, 'download_result')
    mocker.patch.object(DuofaAnalyzer, 'analyze', return_value={"statistics": {...}})
    mocker.patch.object(GeminiReporter, 'generate_report', return_value="<html>...</html>")

    job = Job(id="test_job", ...)
    db.add(job)
    db.commit()

    worker = Worker(config, db)
    await worker.process_job(job)

    # 验证状态变化
    updated_job = db.query(Job).filter_by(id="test_job").first()
    assert updated_job.status == "done"
    assert updated_job.report_path.endswith("report.html")
```

**预期输出**：
```
tests/test_worker.py::test_worker_fifo PASSED
tests/test_worker.py::test_worker_process_job PASSED
```

---

### 任务 9：实现启动脚本

**目标**：提供 Worker 启动入口

**步骤**：

1. 在 `src/worker/main.py` 添加：
   ```python
   def start_worker():
       """Worker 启动函数（供 pyproject.toml scripts 调用）"""
       config = Config.load_from_yaml()
       engine = init_db(config)
       db_session = get_session(engine)

       worker = Worker(config, db_session)

       try:
           asyncio.run(worker.run_forever())
       except KeyboardInterrupt:
           print("Worker stopped")

   if __name__ == "__main__":
       start_worker()
   ```

**验证**：
```bash
# 1. 直接运行
python src/worker/main.py
# 应该输出：Waiting for jobs...

# 2. 通过 pip 安装后运行
pip install -e .
cdid-worker
# 应该输出：Waiting for jobs...

# 3. 创建测试任务，观察 Worker 是否处理
# （需要在另一个终端创建任务）
```

**预期输出**：
```
Worker started (PID: 12345)
Polling for jobs every 5 seconds...
Waiting for jobs...
```

---

## 批次 4 完成检查点

**完成标志**：
- ✅ Worker 主循环实现完成
- ✅ FIFO 队列逻辑正确
- ✅ 启动脚本可用
- ✅ Mock 测试通过

**报告内容**：
- pytest 测试结果
- Worker 启动日志截图

---

## 批次 5：API Server + Web UI（任务 10-11）

### 任务 10：实现 FastAPI 应用

**目标**：实现 3 个核心 API 端点

**步骤**：

1. 创建 `src/api/main.py`
   ```python
   from fastapi import FastAPI, UploadFile, File, Form, HTTPException
   from fastapi.responses import FileResponse

   app = FastAPI(title="CDID 数据分析平台")

   @app.post("/jobs", status_code=201)
   async def create_job(
       file: UploadFile = File(...),
       name: str = Form(...),
       package_name: str = Form(...),
       start_date: str = Form(...),
       end_date: str = Form(...),
       message_types: str = Form(...)  # JSON string
   ):
       # 1. 生成 job_id (ULID)
       # 2. 保存文件
       # 3. 插入数据库
       # 4. 返回 job_id
       pass

   @app.get("/jobs/{job_id}")
   async def get_job(job_id: str):
       # 查询数据库，返回 JobStatus
       pass

   @app.get("/jobs/{job_id}/report")
   async def get_report(job_id: str):
       # 检查状态，返回 HTML 文件
       pass
   ```

2. 实现 ULID 生成（使用 `ulid-py` 库或自定义）

3. 实现文件上传处理

**验证**：
```python
# tests/test_api.py
from fastapi.testclient import TestClient

def test_create_job():
    client = TestClient(app)

    response = client.post(
        "/jobs",
        files={"file": ("test.csv", b"cdid\n123\n456")},
        data={
            "name": "测试任务",
            "package_name": "com.test",
            "start_date": "2026-01-01",
            "end_date": "2026-01-07",
            "message_types": '["dna"]'
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"

def test_get_job():
    client = TestClient(app)

    # 先创建任务
    create_resp = client.post("/jobs", ...)
    job_id = create_resp.json()["job_id"]

    # 查询任务
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert "status" in data

def test_get_report_not_ready():
    client = TestClient(app)

    # 创建任务（status=queued）
    create_resp = client.post("/jobs", ...)
    job_id = create_resp.json()["job_id"]

    # 尝试获取报告（应该返回 409）
    response = client.get(f"/jobs/{job_id}/report")
    assert response.status_code == 409
```

**预期输出**：
```
tests/test_api.py::test_create_job PASSED
tests/test_api.py::test_get_job PASSED
tests/test_api.py::test_get_report_not_ready PASSED
```

---

### 任务 11：实现最小 Web UI

**目标**：创建 3 个 UI 页面

**步骤**：

1. 创建 `src/ui/templates/index.html`（创建任务表单）
   - 包含：文件上传、任务名称、包名、日期范围、数据类型
   - 使用 Bootstrap 5

2. 创建 `src/ui/templates/jobs.html`（任务列表）
   - 表格显示所有任务
   - 状态标记（queued/进行中/done/failed）

3. 创建 `src/ui/templates/job_detail.html`（任务详情）
   - 实时状态（轮询）
   - 进度条
   - 报告嵌入（iframe）

4. 创建 `src/ui/static/js/app.js`（轮询逻辑）
   ```javascript
   function pollJobStatus(jobId) {
       setInterval(async () => {
           const response = await fetch(`/jobs/${jobId}`);
           const data = await response.json();

           // 更新进度条
           document.getElementById('progress').style.width = data.progress + '%';
           document.getElementById('status').textContent = data.status;

           // 如果完成，停止轮询并显示报告
           if (data.status === 'done') {
               showReport(jobId);
               clearInterval(this);
           }
       }, 3000);  // 每 3 秒轮询
   }
   ```

5. 在 `src/api/main.py` 添加 UI 路由：
   ```python
   from fastapi.templating import Jinja2Templates
   from fastapi.staticfiles import StaticFiles

   app.mount("/static", StaticFiles(directory="src/ui/static"), name="static")
   templates = Jinja2Templates(directory="src/ui/templates")

   @app.get("/ui")
   async def ui_index(request: Request):
       return templates.TemplateResponse("index.html", {"request": request})

   @app.get("/ui/jobs")
   async def ui_jobs_list(request: Request):
       jobs = db.query(Job).order_by(Job.created_at.desc()).limit(50).all()
       return templates.TemplateResponse("jobs.html", {"request": request, "jobs": jobs})

   @app.get("/ui/jobs/{job_id}")
   async def ui_job_detail(job_id: str, request: Request):
       job = db.query(Job).filter_by(id=job_id).first()
       if not job:
           raise HTTPException(404)
       return templates.TemplateResponse("job_detail.html", {"request": request, "job": job})
   ```

**验证**：
```bash
# 1. 启动 API Server
uvicorn src.api.main:app --reload

# 2. 在浏览器中访问
open http://localhost:8000/ui

# 3. 手动测试
# - 上传文件，创建任务
# - 检查任务列表
# - 查看任务详情（观察轮询）
```

**预期输出**：
- UI 页面正常显示
- 表单可提交
- 任务列表显示正确
- 详情页轮询更新

---

## 批次 5 完成检查点

**完成标志**：
- ✅ API 端点实现完成
- ✅ Web UI 三个页面完成
- ✅ 前端轮询正常
- ✅ 端到端手动测试通过

**报告内容**：
- API 测试结果
- UI 页面截图
- 手动测试视频或 GIF

---

## 批次 6：端到端测试与部署（任务 12）

### 任务 12：端到端测试与 Docker 部署

**目标**：使用真实数据进行完整流程测试，创建 Docker 镜像

**步骤**：

1. 端到端测试（使用 `xuqiu/demo/波克问题数据.csv`）
   ```bash
   # 1. 启动 Worker（终端 1）
   cdid-worker

   # 2. 启动 API Server（终端 2）
   uvicorn src.api.main:app --reload

   # 3. 在浏览器中创建任务
   open http://localhost:8000/ui
   # 上传 xuqiu/demo/波克问题数据.csv
   # 填写参数：
   #   - 任务名称：波克数据测试
   #   - 包名：com.test.app
   #   - 开始日期：2026-01-01
   #   - 结束日期：2026-01-07
   #   - 数据类型：dna

   # 4. 观察 Worker 日志
   # 应该看到：Fetching → Analyzing → Reporting → Done

   # 5. 查看生成的报告
   open http://localhost:8000/ui/jobs/{job_id}
   ```

2. 验证报告内容
   - 检查 did/oaid 统计是否正确
   - 检查多发判定是否准确
   - 检查 HTML 格式是否美观

3. 创建 Dockerfile（参考方案设计 v1.1 第 13 节）

4. 创建 docker-compose.yml

5. 测试 Docker 部署
   ```bash
   docker-compose up --build
   open http://localhost:8000/ui
   ```

**验证**：
- 完整流程无报错
- 报告生成成功
- Docker 容器正常运行

**预期输出**：
- 端到端测试通过
- Docker 镜像构建成功
- 容器内服务正常运行

---

## 批次 6 完成检查点

**完成标志**：
- ✅ 端到端测试通过（使用真实数据）
- ✅ Docker 部署成功
- ✅ 所有功能验证完成

**最终交付物**：
1. 完整代码仓库
2. 端到端测试视频/截图
3. 生成的报告示例
4. Docker 部署文档
5. README.md（使用说明）

---

## 风险与应对

| 风险 | 应对措施 |
|------|---------|
| 内网 API 不可用 | 使用 mock 数据测试，标记为"需要内网环境" |
| Gemini CLI 调用失败 | 检查版本、Skill 文件、权限；提供详细错误日志 |
| 测试数据缺失 did/oaid | 先用构造数据测试逻辑，后续用真实数据验证 |
| 报告格式不符合预期 | 调整 Skill 的 prompt，迭代优化 |

---

## 总结

**总任务数**：12 个任务
**批次数**：6 个批次
**关键里程碑**：
- 批次 1-2：基础设施 + 数据处理
- 批次 3：Skill + 报告生成（核心）
- 批次 4：Worker 主循环
- 批次 5：API + UI
- 批次 6：集成测试 + 部署

**执行原则**：
- 每批次完成后暂停，等待反馈
- 遇到阻塞立即停止，不要猜测
- 所有验证必须通过才能进入下一批次

---

**准备就绪！等待执行指令。**
