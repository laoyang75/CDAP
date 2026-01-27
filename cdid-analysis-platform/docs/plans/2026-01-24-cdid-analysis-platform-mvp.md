# CDID Analysis Platform MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Web-based CDID data analysis platform that wraps Gemini CLI workflows into an automated service with user-friendly UI.

**Architecture:** FastAPI backend with async worker processing, SQLite database for MVP, Python-based analysis scripts with standardized interface, Gemini CLI integration for HTML report generation, and Bootstrap 5 Web UI for user interactions.

**Tech Stack:**
- Backend: FastAPI, SQLAlchemy, httpx (async HTTP), Pydantic
- Frontend: Jinja2 templates, Bootstrap 5, vanilla JavaScript
- Database: SQLite (MVP) with migration path to PostgreSQL
- Analysis: Pandas, Python 3.11+
- Reporting: Gemini CLI (subprocess with stdin piping)
- Deployment: Docker + docker-compose

---

## Task 1: Project Setup and Database Schema

**Files:**
- Create: `src/db/models.py`
- Create: `src/db/connection.py`
- Create: `src/config.py`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`

**Step 1: Write test for database models**

```python
# tests/test_db_models.py
import pytest
from datetime import datetime
from src.db.models import Job, Pipeline, Client, User
from src.db.connection import get_db_session, init_db

def test_job_model_creation():
    """Test Job model can be created with required fields"""
    init_db()
    session = next(get_db_session())

    job = Job(
        id="01J1A2B3C4D5E6F7G8H9K0M1",
        name="Test Job",
        client_name="Test Client",
        package_name="com.test.app",
        pipeline_id="01J1A2B3C4D5E6F7G8H9K0M2",
        start_date=datetime(2026, 1, 1).date(),
        end_date=datetime(2026, 1, 7).date(),
        message_types=["dna", "daa"],
        status="queued",
        progress=0,
        user_id="test_user"
    )

    session.add(job)
    session.commit()

    retrieved = session.query(Job).filter_by(id=job.id).first()
    assert retrieved is not None
    assert retrieved.name == "Test Job"
    assert retrieved.status == "queued"
    session.close()

def test_pipeline_model_creation():
    """Test Pipeline model with script configuration"""
    init_db()
    session = next(get_db_session())

    pipeline = Pipeline(
        id="01J1A2B3C4D5E6F7G8H9K0M2",
        name="Duplicate Detection",
        description="Detects duplicate CDIDs",
        script_dir="src/scripts/duplicate_detection",
        script_file="analyzer.py",
        skill_name="cdid_report_generator",
        status="active"
    )

    session.add(pipeline)
    session.commit()

    retrieved = session.query(Pipeline).filter_by(id=pipeline.id).first()
    assert retrieved is not None
    assert retrieved.skill_name == "cdid_report_generator"
    session.close()

def test_client_model_with_package_mapping():
    """Test Client model for client-package mapping"""
    init_db()
    session = next(get_db_session())

    client = Client(
        id="01J1A2B3C4D5E6F7G8H9K0M3",
        client_name="Example Client A",
        company_name="Example Corp",
        package_name="com.example.clienta",
        status="active"
    )

    session.add(client)
    session.commit()

    retrieved = session.query(Client).filter_by(client_name="Example Client A").first()
    assert retrieved is not None
    assert retrieved.package_name == "com.example.clienta"
    session.close()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_db_models.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.db.models'"

**Step 3: Create requirements.txt**

```txt
# requirements.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
pydantic==2.5.3
pydantic-settings==2.1.0
httpx==0.26.0
pandas==2.2.0
openpyxl==3.1.2
python-multipart==0.0.6
jinja2==3.1.3
ulid-py==1.1.0
pytest==7.4.4
pytest-asyncio==0.23.3
```

**Step 4: Create database models**

```python
# src/db/models.py
from sqlalchemy import Column, String, Integer, Text, JSON, Date, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(26), primary_key=True)
    name = Column(String(255), nullable=False)
    client_name = Column(String(255), nullable=False)
    package_name = Column(String(255), nullable=False)
    pipeline_id = Column(String(26), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    message_types = Column(JSON, default=list)
    status = Column(String(20), default="queued", index=True)
    progress = Column(Integer, default=0)
    progress_message = Column(String(255), nullable=True)
    input_file_path = Column(String(500), nullable=True)
    raw_data_path = Column(String(500), nullable=True)
    report_path = Column(String(500), nullable=True)
    error = Column(Text, nullable=True)
    insight_task_id = Column(String(50), nullable=True)
    user_id = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Pipeline(Base):
    __tablename__ = "pipelines"

    id = Column(String(26), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    script_dir = Column(String(500), nullable=False)
    script_file = Column(String(255), nullable=False)
    skill_name = Column(String(255), nullable=False)
    status = Column(String(20), default="active")
    execution_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Client(Base):
    __tablename__ = "clients"

    id = Column(String(26), primary_key=True)
    client_name = Column(String(255), nullable=False, unique=True, index=True)
    company_name = Column(String(255), nullable=True)
    package_name = Column(String(255), nullable=False)
    status = Column(String(20), default="active")
    analysis_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class User(Base):
    __tablename__ = "users"

    id = Column(String(26), primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=func.now())
```

**Step 5: Create database connection module**

```python
# src/db/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.db.models import Base
from src.config import settings
import os

engine = None
SessionLocal = None

def init_db():
    """Initialize database connection and create tables"""
    global engine, SessionLocal

    # Ensure database directory exists
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)

    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)

def get_db_session() -> Session:
    """Get database session (dependency injection for FastAPI)"""
    if SessionLocal is None:
        init_db()

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 6: Create configuration module**

```python
# src/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./jobs.db"

    # Internal API
    INSIGHT_API_BASE_URL: str = "http://172.17.129.204:6829"
    INSIGHT_API_TIMEOUT: int = 600  # 10 minutes
    INSIGHT_POLL_INTERVAL: int = 60  # 60 seconds

    # Gemini CLI
    GEMINI_CLI_PATH: str = "gemini"
    GEMINI_CLI_TIMEOUT: int = 300  # 5 minutes

    # File Storage
    JOBS_DIR: str = "jobs"
    SCRIPTS_DIR: str = "src/scripts"

    # Worker
    WORKER_POLL_INTERVAL: int = 5  # 5 seconds
    WORKER_MAX_RETRIES: int = 3

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**Step 7: Create supporting files**

```python
# .env.example
DATABASE_URL=sqlite:///./jobs.db
INSIGHT_API_BASE_URL=http://172.17.129.204:6829
INSIGHT_API_TIMEOUT=600
INSIGHT_POLL_INTERVAL=60
GEMINI_CLI_PATH=gemini
GEMINI_CLI_TIMEOUT=300
JOBS_DIR=jobs
SCRIPTS_DIR=src/scripts
WORKER_POLL_INTERVAL=5
WORKER_MAX_RETRIES=3
API_HOST=0.0.0.0
API_PORT=8000
```

```
# .gitignore
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/
.env
jobs/
*.db
*.db-journal
.DS_Store
node_modules/
```

**Step 8: Run tests to verify they pass**

Run: `pytest tests/test_db_models.py -v`
Expected: PASS (all 3 tests)

**Step 9: Commit**

```bash
git add src/db/models.py src/db/connection.py src/config.py requirements.txt .env.example .gitignore tests/test_db_models.py
git commit -m "$(cat <<'EOF'
feat: add database schema and configuration

- Implement SQLAlchemy models for jobs, pipelines, clients, users
- Add database connection management with session factory
- Create configuration module with Pydantic settings
- Add requirements.txt with core dependencies
- Include tests for database model creation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Internal API Client Implementation

**Files:**
- Create: `src/worker/insight_client.py`
- Create: `tests/test_insight_client.py`

**Step 1: Write failing tests for insight client**

```python
# tests/test_insight_client.py
import pytest
import httpx
from unittest.mock import Mock, patch, AsyncMock
from src.worker.insight_client import InsightClient
import tempfile
import os

@pytest.mark.asyncio
async def test_create_task_success():
    """Test successful task creation"""
    client = InsightClient(base_url="http://test.api", timeout=60)

    with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"task_id": "test_task_123", "status": "created"}
        )

        task_id = await client.create_task(
            name="Test Task",
            package_name="com.test.app",
            file_path="test.csv",
            start="2026-01-01",
            end="2026-01-07",
            message_types=["dna", "daa"]
        )

        assert task_id == "test_task_123"
        assert mock_post.called

@pytest.mark.asyncio
async def test_query_task_status_success():
    """Test successful status query"""
    client = InsightClient(base_url="http://test.api", timeout=60)

    with patch.object(httpx.AsyncClient, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                "status": "success",
                "oss_url": "http://oss.example.com/result.xlsx"
            }
        )

        result = await client.query_task_status("test_task_123")

        assert result["status"] == "success"
        assert "oss_url" in result

@pytest.mark.asyncio
async def test_download_result_success():
    """Test successful file download"""
    client = InsightClient(base_url="http://test.api", timeout=60)

    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = os.path.join(tmpdir, "result.xlsx")

        with patch.object(httpx.AsyncClient, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                content=b"fake excel content"
            )

            await client.download_result("http://oss.example.com/result.xlsx", save_path)

            assert os.path.exists(save_path)
            with open(save_path, 'rb') as f:
                assert f.read() == b"fake excel content"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_insight_client.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.worker.insight_client'"

**Step 3: Implement InsightClient**

```python
# src/worker/insight_client.py
import httpx
from typing import Optional, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

class InsightClient:
    """Client for internal API at 172.17.129.204:6829"""

    def __init__(self, base_url: str, timeout: int = 600):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    async def create_task(
        self,
        name: str,
        package_name: str,
        file_path: str,
        start: str,
        end: str,
        message_types: Optional[list[str]] = None
    ) -> str:
        """
        Create analysis task

        Args:
            name: Task name
            package_name: Application package name
            file_path: Path to CDID file (CSV)
            start: Start date (YYYY-MM-DD, required)
            end: End date (YYYY-MM-DD, required)
            message_types: Message types (optional list: ["dna", "daa"])

        Returns:
            task_id: Created task ID
        """
        url = f"{self.base_url}/api/statistical-analysis/v1/task/create"

        # Prepare form data
        files = {
            'file': open(file_path, 'rb')
        }

        data = {
            'name': name,
            'package_name': package_name,
            'start': start,
            'end': end
        }

        # Add message types as repeated fields if provided
        if message_types:
            data['message'] = message_types

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, files=files, data=data)
                response.raise_for_status()

                result = response.json()
                task_id = result.get('task_id')

                if not task_id:
                    raise ValueError(f"No task_id in response: {result}")

                logger.info(f"Created task {task_id} for {package_name}")
                return task_id

        except httpx.HTTPError as e:
            logger.error(f"Failed to create task: {e}")
            raise
        finally:
            files['file'].close()

    async def query_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Query task status

        Args:
            task_id: Task ID from create_task

        Returns:
            dict with keys: status, oss_url (if success), etc.
        """
        url = f"{self.base_url}/api/statistical-analysis/v1/task/detail"
        params = {'task_id': task_id}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                result = response.json()
                logger.debug(f"Task {task_id} status: {result.get('status')}")
                return result

        except httpx.HTTPError as e:
            logger.error(f"Failed to query task {task_id}: {e}")
            raise

    async def download_result(self, oss_url: str, save_path: str):
        """
        Download result file from OSS URL

        Args:
            oss_url: OSS download URL from task detail
            save_path: Local path to save the file
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(oss_url)
                response.raise_for_status()

                with open(save_path, 'wb') as f:
                    f.write(response.content)

                logger.info(f"Downloaded result to {save_path}")

        except httpx.HTTPError as e:
            logger.error(f"Failed to download from {oss_url}: {e}")
            raise
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_insight_client.py -v`
Expected: PASS (all 3 tests)

**Step 5: Commit**

```bash
git add src/worker/insight_client.py tests/test_insight_client.py
git commit -m "$(cat <<'EOF'
feat: implement internal API client

- Add InsightClient for internal API communication
- Support task creation with multipart form data
- Implement task status polling and result download
- Include comprehensive unit tests with mocked HTTP calls

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Python Analysis Script Template and Executor

**Files:**
- Create: `src/scripts/duplicate_detection/analyzer.py`
- Create: `src/worker/pipeline_executor.py`
- Create: `tests/test_pipeline_executor.py`
- Create: `tests/fixtures/sample_raw_data.xlsx`

**Step 1: Write failing test for analyzer script**

```python
# tests/test_pipeline_executor.py
import pytest
import json
import os
import tempfile
import pandas as pd
from src.worker.pipeline_executor import PipelineExecutor
from datetime import datetime

def create_sample_excel():
    """Create sample Excel file for testing"""
    data = {
        'cdid': ['cdid1', 'cdid2', 'cdid3', 'cdid4'],
        'did': ['device1', 'device1', 'device2', 'device2'],
        'device_model': ['Model A', 'Model A', 'Model B', 'Model C'],
        'oaid': ['oaid1', 'oaid2', 'oaid3', 'oaid4'],
    }
    df = pd.DataFrame(data)

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xlsx') as f:
        temp_path = f.name

    df.to_excel(temp_path, index=False, engine='openpyxl')
    return temp_path

def test_load_and_execute_analyzer():
    """Test loading analyzer script and executing analyze function"""
    executor = PipelineExecutor()

    # Create temporary Excel
    input_file = create_sample_excel()

    try:
        # Load duplicate detection analyzer
        result = executor.execute_analysis(
            script_dir="src/scripts/duplicate_detection",
            script_file="analyzer.py",
            input_file=input_file,
            user_info={'user_id': 'test_user', 'task_id': 'test_task'},
            start_date="2026-01-01",
            end_date="2026-01-07"
        )

        # Verify result structure
        assert isinstance(result, dict)
        assert 'summary' in result
        assert 'duplicate' in result
        assert isinstance(result['duplicate'], list)

    finally:
        os.unlink(input_file)

def test_analysis_result_serializable():
    """Test that analysis result can be serialized to JSON"""
    executor = PipelineExecutor()
    input_file = create_sample_excel()

    try:
        result = executor.execute_analysis(
            script_dir="src/scripts/duplicate_detection",
            script_file="analyzer.py",
            input_file=input_file,
            user_info={'user_id': 'test_user', 'task_id': 'test_task'},
            start_date="2026-01-01",
            end_date="2026-01-07"
        )

        # Should be JSON serializable
        json_str = json.dumps(result, ensure_ascii=False)
        assert len(json_str) > 0

        # Should be deserializable
        restored = json.loads(json_str)
        assert restored == result

    finally:
        os.unlink(input_file)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline_executor.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.worker.pipeline_executor'"

**Step 3: Create analyzer script template**

```python
# src/scripts/duplicate_detection/analyzer.py
"""
Duplicate Detection Analyzer

Detects multiple CDIDs associated with the same device identifier
"""
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

def analyze(input_file: str, user_info: dict, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Standard analysis interface for duplicate detection

    Args:
        input_file: Path to raw data Excel file
        user_info: User context {'user_id': '...', 'task_id': '...'}
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        dict: Analysis result with structure:
            {
                "job_id": str,
                "analyzed_at": str (ISO format),
                "summary": {
                    "total_cdid": int,
                    "duplicate_count": int,
                    "impact_count": int,
                    "risk_count": int
                },
                "duplicate": [list of duplicate records],
                "impact": [list of collision records],
                "risk": [list of risk records]
            }
    """
    logger.info(f"Starting duplicate detection analysis for task {user_info.get('task_id')}")

    # Load data
    try:
        df = pd.read_excel(input_file, engine='openpyxl')
        logger.info(f"Loaded {len(df)} rows from {input_file}")
    except Exception as e:
        logger.error(f"Failed to load Excel: {e}")
        raise

    # Field mapping (handle different column names)
    field_map = {
        'cdid': ['cdid', 'CDID', 'device_id'],
        'did': ['did', 'DID', 'device_identifier'],
        'oaid': ['oaid', 'OAID'],
        'android_id': ['android_id', 'androidId', 'ANDROID_ID'],
        'imei': ['imei', 'IMEI'],
        'device_model': ['device_model', 'deviceModel', 'model']
    }

    # Normalize column names
    for standard_name, possible_names in field_map.items():
        for col in df.columns:
            if col in possible_names:
                df.rename(columns={col: standard_name}, inplace=True)
                break

    # Ensure required fields exist
    if 'cdid' not in df.columns:
        raise ValueError("Required field 'cdid' not found in data")

    # Duplicate detection (MVP logic)
    duplicate_results = detect_duplicates(df)

    # Collision detection
    collision_results = detect_collisions(df)

    # Risk detection (MVP placeholder)
    risk_results = detect_risks(df)

    # Build summary
    summary = {
        "total_cdid": len(df['cdid'].unique()) if 'cdid' in df.columns else 0,
        "duplicate_count": len(duplicate_results),
        "impact_count": len(collision_results),
        "risk_count": len(risk_results)
    }

    result = {
        "job_id": user_info.get('task_id', 'unknown'),
        "analyzed_at": datetime.utcnow().isoformat() + 'Z',
        "start_date": start_date,
        "end_date": end_date,
        "summary": summary,
        "duplicate": duplicate_results,
        "impact": collision_results,
        "risk": risk_results
    }

    logger.info(f"Analysis complete: {summary}")
    return result

def detect_duplicates(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Detect duplicates: same device identifier with multiple CDIDs

    MVP logic: Group by did/oaid/android_id/imei, count unique cdids
    """
    results = []

    # Priority: did > oaid > android_id > imei
    identifier_fields = ['did', 'oaid', 'android_id', 'imei']

    for field in identifier_fields:
        if field not in df.columns:
            continue

        # Group by identifier, get unique CDIDs
        grouped = df.groupby(field)['cdid'].apply(lambda x: x.unique().tolist()).reset_index()
        grouped['cdid_count'] = grouped['cdid'].apply(len)

        # Filter: multiple CDIDs per identifier
        duplicates = grouped[grouped['cdid_count'] > 1]

        for _, row in duplicates.iterrows():
            results.append({
                "type": field,
                "identifier": row[field],
                "cdid_list": row['cdid'],
                "cdid_count": row['cdid_count']
            })

    return results

def detect_collisions(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Detect collisions: same DID with different device models
    """
    results = []

    if 'did' not in df.columns or 'device_model' not in df.columns:
        return results

    # Group by did, get unique device models
    grouped = df.groupby('did').agg({
        'device_model': lambda x: x.unique().tolist(),
        'cdid': lambda x: x.unique().tolist()
    }).reset_index()

    grouped['model_count'] = grouped['device_model'].apply(len)

    # Filter: multiple device models per DID
    collisions = grouped[grouped['model_count'] > 1]

    for _, row in collisions.iterrows():
        results.append({
            "did": row['did'],
            "device_models": row['device_model'],
            "cdid_list": row['cdid'],
            "model_count": row['model_count']
        })

    return results

def detect_risks(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Detect risks: MVP placeholder with configurable rules

    TODO: Integrate with actual risk rules/scenes table
    """
    results = []

    # MVP fallback: if rc_rules or rc_scenes exists and is non-empty
    risk_fields = ['rc_rules', 'rc_scenes']

    for field in risk_fields:
        if field in df.columns:
            risky_records = df[df[field].notna() & (df[field] != '')]

            for _, row in risky_records.iterrows():
                results.append({
                    "cdid": row.get('cdid', 'unknown'),
                    "risk_type": field,
                    "risk_value": row[field],
                    "note": "MVP fallback rule - needs refinement"
                })

    return results
```

**Step 4: Create pipeline executor**

```python
# src/worker/pipeline_executor.py
"""
Pipeline Executor

Dynamically loads and executes Python analysis scripts
"""
import importlib.util
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PipelineExecutor:
    """Executes analysis pipelines by loading Python scripts dynamically"""

    def execute_analysis(
        self,
        script_dir: str,
        script_file: str,
        input_file: str,
        user_info: Dict[str, Any],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Execute analysis script

        Args:
            script_dir: Directory containing the script
            script_file: Script filename (e.g., "analyzer.py")
            input_file: Path to input data file (Excel)
            user_info: User context dict
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            dict: Analysis result
        """
        script_path = os.path.join(script_dir, script_file)

        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script not found: {script_path}")

        # Dynamically load module
        logger.info(f"Loading script: {script_path}")
        spec = importlib.util.spec_from_file_location("analyzer_module", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Verify analyze function exists
        if not hasattr(module, 'analyze'):
            raise AttributeError(f"Script {script_path} missing 'analyze' function")

        # Execute analysis
        logger.info(f"Executing analysis: {script_file}")
        result = module.analyze(input_file, user_info, start_date, end_date)

        # Validate result
        if not isinstance(result, dict):
            raise TypeError(f"analyze() must return dict, got {type(result)}")

        logger.info(f"Analysis complete: {script_file}")
        return result
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_pipeline_executor.py -v`
Expected: PASS (all 2 tests)

**Step 6: Commit**

```bash
git add src/scripts/duplicate_detection/analyzer.py src/worker/pipeline_executor.py tests/test_pipeline_executor.py
git commit -m "$(cat <<'EOF'
feat: implement analysis script template and executor

- Add duplicate_detection analyzer with standard interface
- Implement duplicate, collision, and risk detection (MVP logic)
- Add PipelineExecutor for dynamic script loading
- Include field mapping for flexible column names
- Add comprehensive tests with sample data

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Gemini CLI Reporter Integration

**Files:**
- Create: `src/worker/gemini_reporter.py`
- Create: `tests/test_gemini_reporter.py`

**Step 1: Write failing test for Gemini reporter**

```python
# tests/test_gemini_reporter.py
import pytest
from unittest.mock import Mock, patch
from src.worker.gemini_reporter import GeminiReporter
import subprocess

def test_generate_report_success():
    """Test successful HTML report generation via Gemini CLI"""
    reporter = GeminiReporter(cli_path="gemini", timeout=300)

    analysis_result = {
        "job_id": "test_job_123",
        "summary": {"total_cdid": 100, "duplicate_count": 5},
        "duplicate": [{"type": "did", "cdid_count": 3}]
    }

    mock_html = "<html><body><h1>Report</h1></body></html>"

    with patch('subprocess.Popen') as mock_popen:
        mock_process = Mock()
        mock_process.communicate.return_value = (mock_html, "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        html = reporter.generate_report(analysis_result, skill_name="test_skill")

        assert html == mock_html
        assert mock_popen.called

        # Verify command format
        call_args = mock_popen.call_args
        cmd = call_args[0][0]
        assert "gemini" in cmd[0]
        assert "@test_skill" in cmd[1]

def test_generate_report_failure():
    """Test error handling when Gemini CLI fails"""
    reporter = GeminiReporter(cli_path="gemini", timeout=300)

    analysis_result = {"job_id": "test_job_123"}

    with patch('subprocess.Popen') as mock_popen:
        mock_process = Mock()
        mock_process.communicate.return_value = ("", "Error: skill not found")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        with pytest.raises(RuntimeError) as exc_info:
            reporter.generate_report(analysis_result, skill_name="nonexistent_skill")

        assert "Gemini CLI failed" in str(exc_info.value)

def test_stdin_input_format():
    """Test that analysis result is passed via stdin as JSON"""
    reporter = GeminiReporter(cli_path="gemini", timeout=300)

    analysis_result = {"test": "data", "number": 123}

    with patch('subprocess.Popen') as mock_popen:
        mock_process = Mock()
        mock_process.communicate.return_value = ("<html></html>", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        reporter.generate_report(analysis_result, skill_name="test_skill")

        # Verify stdin was used
        call_kwargs = mock_popen.call_args[1]
        assert call_kwargs['stdin'] == subprocess.PIPE
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_gemini_reporter.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.worker.gemini_reporter'"

**Step 3: Implement Gemini reporter**

```python
# src/worker/gemini_reporter.py
"""
Gemini CLI Reporter

Generates HTML reports using Gemini CLI with skill invocation
"""
import subprocess
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class GeminiReporter:
    """Generates HTML reports via Gemini CLI headless mode"""

    def __init__(self, cli_path: str = "gemini", timeout: int = 300):
        """
        Initialize reporter

        Args:
            cli_path: Path to gemini CLI executable
            timeout: Command timeout in seconds
        """
        self.cli_path = cli_path
        self.timeout = timeout

    def generate_report(self, analysis_result: Dict[str, Any], skill_name: str) -> str:
        """
        Generate HTML report using Gemini CLI

        Args:
            analysis_result: Analysis result dict (will be JSON serialized)
            skill_name: Gemini skill/extension name (without @)

        Returns:
            HTML report string

        Raises:
            RuntimeError: If Gemini CLI fails
        """
        # Serialize analysis result to JSON
        result_json = json.dumps(analysis_result, ensure_ascii=False, indent=2)

        # Build command: gemini "@skill_name ..."
        prompt = f"@{skill_name} 根据以上JSON生成完整HTML报告，只输出HTML代码（包含<html><head><body>）"
        cmd = [self.cli_path, prompt]

        logger.info(f"Invoking Gemini CLI with skill: {skill_name}")
        logger.debug(f"Command: {' '.join(cmd)}")

        try:
            # Execute with stdin pipe
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Send JSON via stdin and wait for result
            stdout, stderr = process.communicate(input=result_json, timeout=self.timeout)

            if process.returncode != 0:
                error_msg = f"Gemini CLI failed (exit code {process.returncode}): {stderr}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            logger.info(f"Report generated successfully ({len(stdout)} chars)")
            return stdout

        except subprocess.TimeoutExpired:
            process.kill()
            error_msg = f"Gemini CLI timeout after {self.timeout}s"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_gemini_reporter.py -v`
Expected: PASS (all 3 tests)

**Step 5: Commit**

```bash
git add src/worker/gemini_reporter.py tests/test_gemini_reporter.py
git commit -m "$(cat <<'EOF'
feat: implement Gemini CLI reporter integration

- Add GeminiReporter for HTML report generation
- Use subprocess with stdin pipe for JSON input
- Support skill invocation via @skill_name syntax
- Include timeout handling and error logging
- Add comprehensive tests for success and failure cases

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Worker Main Loop Implementation

**Files:**
- Create: `src/worker/main.py`
- Create: `tests/test_worker_main.py`

**Step 1: Write failing test for worker**

```python
# tests/test_worker_main.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.worker.main import Worker
from src.db.models import Job, Pipeline
from datetime import datetime, date
import tempfile
import os

@pytest.mark.asyncio
async def test_worker_process_job_full_flow():
    """Test complete job processing flow"""
    # Create temporary job directory
    with tempfile.TemporaryDirectory() as tmpdir:
        worker = Worker(jobs_dir=tmpdir)

        # Mock job and pipeline
        job = Mock(spec=Job)
        job.id = "test_job_123"
        job.name = "Test Job"
        job.client_name = "Test Client"
        job.package_name = "com.test.app"
        job.pipeline_id = "pipeline_123"
        job.start_date = date(2026, 1, 1)
        job.end_date = date(2026, 1, 7)
        job.message_types = ["dna"]
        job.input_file_path = "input.csv"
        job.user_id = "test_user"

        pipeline = Mock(spec=Pipeline)
        pipeline.script_dir = "src/scripts/duplicate_detection"
        pipeline.script_file = "analyzer.py"
        pipeline.skill_name = "test_skill"

        # Mock dependencies
        with patch.object(worker, 'get_pipeline', return_value=pipeline):
            with patch.object(worker.insight_client, 'create_task', new_callable=AsyncMock) as mock_create:
                with patch.object(worker.insight_client, 'query_task_status', new_callable=AsyncMock) as mock_query:
                    with patch.object(worker.insight_client, 'download_result', new_callable=AsyncMock):
                        with patch.object(worker.executor, 'execute_analysis') as mock_analyze:
                            with patch.object(worker.reporter, 'generate_report') as mock_report:

                                mock_create.return_value = "insight_task_123"
                                mock_query.return_value = {"status": "success", "oss_url": "http://oss/file.xlsx"}
                                mock_analyze.return_value = {"summary": {}, "duplicate": []}
                                mock_report.return_value = "<html>Report</html>"

                                # Process job
                                await worker.process_job(job)

                                # Verify all stages called
                                assert mock_create.called
                                assert mock_query.called
                                assert mock_analyze.called
                                assert mock_report.called

@pytest.mark.asyncio
async def test_worker_handles_fetch_failure():
    """Test worker handles fetching stage failure gracefully"""
    with tempfile.TemporaryDirectory() as tmpdir:
        worker = Worker(jobs_dir=tmpdir)

        job = Mock(spec=Job)
        job.id = "test_job_123"
        job.status = "queued"

        with patch.object(worker.insight_client, 'create_task', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("Network error")

            with pytest.raises(Exception):
                await worker.process_job(job)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_worker_main.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.worker.main'"

**Step 3: Implement worker main loop**

```python
# src/worker/main.py
"""
Worker Main Loop

Processes jobs from queue: fetch data → analyze → generate report
"""
import asyncio
import logging
import os
import json
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from src.config import settings
from src.db.connection import init_db, get_db_session
from src.db.models import Job, Pipeline
from src.worker.insight_client import InsightClient
from src.worker.pipeline_executor import PipelineExecutor
from src.worker.gemini_reporter import GeminiReporter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Worker:
    """Background worker for processing analysis jobs"""

    def __init__(self, jobs_dir: Optional[str] = None):
        self.jobs_dir = jobs_dir or settings.JOBS_DIR
        self.insight_client = InsightClient(
            base_url=settings.INSIGHT_API_BASE_URL,
            timeout=settings.INSIGHT_API_TIMEOUT
        )
        self.executor = PipelineExecutor()
        self.reporter = GeminiReporter(
            cli_path=settings.GEMINI_CLI_PATH,
            timeout=settings.GEMINI_CLI_TIMEOUT
        )

        # Ensure jobs directory exists
        os.makedirs(self.jobs_dir, exist_ok=True)

    def get_job_dir(self, job_id: str) -> str:
        """Get job-specific directory"""
        job_dir = os.path.join(self.jobs_dir, job_id)
        os.makedirs(job_dir, exist_ok=True)
        return job_dir

    def get_pipeline(self, db: Session, pipeline_id: str) -> Pipeline:
        """Get pipeline configuration"""
        pipeline = db.query(Pipeline).filter_by(id=pipeline_id).first()
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        return pipeline

    def update_job_status(
        self,
        db: Session,
        job: Job,
        status: str,
        progress: int,
        progress_message: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Update job status in database"""
        job.status = status
        job.progress = progress
        if progress_message:
            job.progress_message = progress_message
        if error:
            job.error = error
        job.updated_at = datetime.utcnow()
        db.commit()
        logger.info(f"Job {job.id}: {status} ({progress}%) - {progress_message}")

    async def process_job(self, job: Job):
        """
        Process a single job through all stages

        Stages:
        1. fetching: Call internal API, wait for data
        2. analyzing: Run Python analysis script
        3. reporting: Generate HTML via Gemini CLI
        4. done: Complete
        """
        db = next(get_db_session())
        job_dir = self.get_job_dir(job.id)

        try:
            # Stage 1: Fetching
            self.update_job_status(
                db, job, "fetching", 10,
                "Creating internal API task"
            )

            input_file = os.path.join(job_dir, job.input_file_path)

            insight_task_id = await self.insight_client.create_task(
                name=job.name,
                package_name=job.package_name,
                file_path=input_file,
                start=job.start_date.strftime("%Y-%m-%d"),
                end=job.end_date.strftime("%Y-%m-%d"),
                message_types=job.message_types
            )

            job.insight_task_id = insight_task_id
            db.commit()

            # Poll for completion
            self.update_job_status(
                db, job, "fetching", 20,
                f"Waiting for internal API task {insight_task_id}"
            )

            max_polls = settings.INSIGHT_API_TIMEOUT // settings.INSIGHT_POLL_INTERVAL
            for poll_count in range(max_polls):
                await asyncio.sleep(settings.INSIGHT_POLL_INTERVAL)

                result = await self.insight_client.query_task_status(insight_task_id)
                status = result.get('status')

                if status == 'success':
                    break
                elif status == 'failed':
                    raise RuntimeError(f"Internal API task failed: {result}")

                progress = min(40, 20 + (poll_count * 20 // max_polls))
                self.update_job_status(
                    db, job, "fetching", progress,
                    f"Polling... ({poll_count + 1}/{max_polls})"
                )
            else:
                raise TimeoutError(f"Internal API task timeout after {settings.INSIGHT_API_TIMEOUT}s")

            # Download result
            self.update_job_status(
                db, job, "fetching", 45,
                "Downloading raw data"
            )

            raw_data_path = os.path.join(job_dir, "raw_data.xlsx")
            await self.insight_client.download_result(result['oss_url'], raw_data_path)

            job.raw_data_path = raw_data_path
            db.commit()

            # Stage 2: Analyzing
            self.update_job_status(
                db, job, "analyzing", 50,
                "Loading analysis pipeline"
            )

            pipeline = self.get_pipeline(db, job.pipeline_id)

            analysis_result = self.executor.execute_analysis(
                script_dir=pipeline.script_dir,
                script_file=pipeline.script_file,
                input_file=raw_data_path,
                user_info={'user_id': job.user_id, 'task_id': job.id},
                start_date=job.start_date.strftime("%Y-%m-%d"),
                end_date=job.end_date.strftime("%Y-%m-%d")
            )

            # Save analysis result
            analysis_result_path = os.path.join(job_dir, "analysis_result.json")
            with open(analysis_result_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)

            self.update_job_status(
                db, job, "analyzing", 70,
                "Analysis complete"
            )

            # Stage 3: Reporting
            self.update_job_status(
                db, job, "reporting", 80,
                "Generating HTML report"
            )

            html_report = self.reporter.generate_report(
                analysis_result,
                skill_name=pipeline.skill_name
            )

            # Save report
            report_path = os.path.join(job_dir, "report.html")
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_report)

            job.report_path = report_path
            db.commit()

            # Stage 4: Done
            self.update_job_status(
                db, job, "done", 100,
                "Complete"
            )

            logger.info(f"Job {job.id} completed successfully")

        except Exception as e:
            logger.error(f"Job {job.id} failed: {e}", exc_info=True)
            self.update_job_status(
                db, job, "failed", job.progress,
                f"Failed: {str(e)[:200]}",
                error=str(e)
            )

        finally:
            db.close()

    async def run_forever(self):
        """Main worker loop: poll for queued jobs and process them"""
        logger.info("Worker started")

        while True:
            try:
                db = next(get_db_session())

                # Get next queued job (FIFO)
                job = db.query(Job).filter_by(status='queued').order_by(Job.created_at).first()

                if job:
                    logger.info(f"Processing job {job.id}: {job.name}")
                    await self.process_job(job)
                else:
                    # No jobs, sleep
                    await asyncio.sleep(settings.WORKER_POLL_INTERVAL)

                db.close()

            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
                await asyncio.sleep(settings.WORKER_POLL_INTERVAL)

async def main():
    """Entry point"""
    init_db()
    worker = Worker()
    await worker.run_forever()

if __name__ == '__main__':
    asyncio.run(main())
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_worker_main.py -v`
Expected: PASS (all 2 tests)

**Step 5: Commit**

```bash
git add src/worker/main.py tests/test_worker_main.py
git commit -m "$(cat <<'EOF'
feat: implement worker main loop

- Add Worker class with full job processing flow
- Implement 4-stage pipeline: fetching, analyzing, reporting, done
- Add status tracking and progress updates
- Include polling logic for internal API task completion
- Add error handling and recovery for each stage
- Implement run_forever loop for continuous processing

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: FastAPI Server - Core Endpoints

**Files:**
- Create: `src/api/main.py`
- Create: `src/api/routes/jobs.py`
- Create: `src/api/dependencies.py`
- Create: `tests/test_api_jobs.py`

**Step 1: Write failing test for jobs API**

```python
# tests/test_api_jobs.py
import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.db.connection import init_db
import tempfile
import os

@pytest.fixture
def client():
    """Test client with test database"""
    init_db()
    return TestClient(app)

def test_create_job_success(client):
    """Test job creation with file upload"""
    # Create temporary CDID file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("cdid\ntest_cdid_1\ntest_cdid_2\n")
        temp_file = f.name

    try:
        with open(temp_file, 'rb') as f:
            response = client.post(
                "/jobs",
                files={"file": ("cdid.csv", f, "text/csv")},
                data={
                    "name": "Test Job",
                    "client_name": "Test Client",
                    "package_name": "com.test.app",
                    "pipeline_id": "01J1A2B3C4D5E6F7G8H9K0M2",
                    "start_date": "2026-01-01",
                    "end_date": "2026-01-07",
                    "message_types": '["dna"]'
                }
            )

        assert response.status_code == 201
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"

    finally:
        os.unlink(temp_file)

def test_get_jobs_list(client):
    """Test retrieving job list"""
    response = client.get("/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert isinstance(data["jobs"], list)

def test_get_job_detail(client):
    """Test retrieving single job details"""
    # First create a job
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("cdid\ntest_cdid\n")
        temp_file = f.name

    try:
        with open(temp_file, 'rb') as f:
            create_response = client.post(
                "/jobs",
                files={"file": ("cdid.csv", f, "text/csv")},
                data={
                    "name": "Test Job",
                    "client_name": "Test Client",
                    "package_name": "com.test.app",
                    "pipeline_id": "01J1A2B3C4D5E6F7G8H9K0M2",
                    "start_date": "2026-01-01",
                    "end_date": "2026-01-07"
                }
            )

        job_id = create_response.json()["job_id"]

        # Get job detail
        response = client.get(f"/jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
        assert data["name"] == "Test Job"

    finally:
        os.unlink(temp_file)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_jobs.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.api.main'"

**Step 3: Create API dependencies**

```python
# src/api/dependencies.py
"""
FastAPI Dependencies

Provides database sessions and other shared resources
"""
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from src.db.connection import get_db_session

def get_db() -> Session:
    """Dependency for database session"""
    return next(get_db_session())
```

**Step 4: Create jobs routes**

```python
# src/api/routes/jobs.py
"""
Jobs API Routes

Handles job creation, listing, and status queries
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import json
from datetime import datetime, date
from ulid import ULID

from src.api.dependencies import get_db
from src.db.models import Job
from src.config import settings

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("", status_code=201)
async def create_job(
    file: UploadFile = File(...),
    name: str = Form(...),
    client_name: str = Form(...),
    package_name: str = Form(...),
    pipeline_id: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    message_types: Optional[str] = Form(None),
    user_id: str = Form(default="default_user"),
    db: Session = Depends(get_db)
):
    """
    Create new analysis job

    Args:
        file: CDID CSV file upload
        name: Job name
        client_name: Client name
        package_name: Application package name
        pipeline_id: Pipeline ID to use
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        message_types: JSON array of message types (optional)
        user_id: User ID (optional)

    Returns:
        job_id, status, created_at
    """
    # Generate job ID
    job_id = str(ULID())

    # Create job directory
    job_dir = os.path.join(settings.JOBS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    # Save uploaded file
    input_file_path = os.path.join(job_dir, "input.csv")
    with open(input_file_path, 'wb') as f:
        content = await file.read()
        f.write(content)

    # Parse message_types
    msg_types = json.loads(message_types) if message_types else []

    # Parse dates
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    # Create job record
    job = Job(
        id=job_id,
        name=name,
        client_name=client_name,
        package_name=package_name,
        pipeline_id=pipeline_id,
        start_date=start,
        end_date=end,
        message_types=msg_types,
        status="queued",
        progress=0,
        input_file_path=input_file_path,
        user_id=user_id
    )

    db.add(job)
    db.commit()

    return {
        "job_id": job_id,
        "status": "queued",
        "created_at": job.created_at.isoformat()
    }

@router.get("")
async def list_jobs(
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List jobs with optional filtering

    Args:
        status: Filter by status (optional)
        user_id: Filter by user (optional)

    Returns:
        List of jobs
    """
    query = db.query(Job)

    if status:
        query = query.filter(Job.status == status)
    if user_id:
        query = query.filter(Job.user_id == user_id)

    jobs = query.order_by(Job.created_at.desc()).all()

    return {
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "client_name": job.client_name,
                "status": job.status,
                "progress": job.progress,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat()
            }
            for job in jobs
        ]
    }

@router.get("/{job_id}")
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """
    Get job details

    Args:
        job_id: Job ID

    Returns:
        Complete job information
    """
    job = db.query(Job).filter_by(id=job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": job.id,
        "name": job.name,
        "client_name": job.client_name,
        "package_name": job.package_name,
        "pipeline_id": job.pipeline_id,
        "start_date": job.start_date.isoformat(),
        "end_date": job.end_date.isoformat(),
        "message_types": job.message_types,
        "status": job.status,
        "progress": job.progress,
        "progress_message": job.progress_message,
        "error": job.error,
        "report_path": job.report_path,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat()
    }

@router.get("/{job_id}/report")
async def get_report(job_id: str, db: Session = Depends(get_db)):
    """
    Get HTML report

    Args:
        job_id: Job ID

    Returns:
        HTML report file
    """
    job = db.query(Job).filter_by(id=job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.report_path or not os.path.exists(job.report_path):
        raise HTTPException(status_code=404, detail="Report not available")

    return FileResponse(
        job.report_path,
        media_type="text/html",
        filename=f"report_{job_id}.html"
    )

@router.get("/{job_id}/raw-data")
async def get_raw_data(job_id: str, db: Session = Depends(get_db)):
    """
    Download raw data Excel file

    Args:
        job_id: Job ID

    Returns:
        Excel file
    """
    job = db.query(Job).filter_by(id=job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.raw_data_path or not os.path.exists(job.raw_data_path):
        raise HTTPException(status_code=404, detail="Raw data not available")

    return FileResponse(
        job.raw_data_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"raw_data_{job_id}.xlsx"
    )

@router.post("/{job_id}/retry")
async def retry_job(job_id: str, db: Session = Depends(get_db)):
    """
    Retry failed job

    Args:
        job_id: Job ID

    Returns:
        Updated job status
    """
    job = db.query(Job).filter_by(id=job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "failed":
        raise HTTPException(status_code=400, detail="Can only retry failed jobs")

    # Reset to queued
    job.status = "queued"
    job.progress = 0
    job.error = None
    job.updated_at = datetime.utcnow()
    db.commit()

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Job queued for retry"
    }

@router.delete("/{job_id}")
async def delete_job(job_id: str, db: Session = Depends(get_db)):
    """
    Delete job (soft delete - sets status to deleted)

    Args:
        job_id: Job ID

    Returns:
        Success message
    """
    job = db.query(Job).filter_by(id=job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Soft delete
    job.status = "deleted"
    job.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Job deleted successfully"}
```

**Step 5: Create main FastAPI app**

```python
# src/api/main.py
"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import jobs
from src.db.connection import init_db

app = FastAPI(
    title="CDID Analysis Platform API",
    description="Web service for CDID data analysis",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
@app.on_event("startup")
async def startup():
    init_db()

# Include routers
app.include_router(jobs.router)

@app.get("/")
async def root():
    return {
        "message": "CDID Analysis Platform API",
        "version": "0.1.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Step 6: Run tests to verify they pass**

Run: `pytest tests/test_api_jobs.py -v`
Expected: PASS (all 3 tests)

**Step 7: Commit**

```bash
git add src/api/main.py src/api/routes/jobs.py src/api/dependencies.py tests/test_api_jobs.py
git commit -m "$(cat <<'EOF'
feat: implement FastAPI server with jobs endpoints

- Add FastAPI app with CORS middleware
- Implement job creation with file upload handling
- Add job listing, detail, report, and raw data endpoints
- Support job retry for failed tasks
- Include soft delete for jobs
- Add comprehensive API tests

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Pipeline and Client Management APIs

**Files:**
- Create: `src/api/routes/pipelines.py`
- Create: `src/api/routes/clients.py`
- Create: `tests/test_api_pipelines.py`
- Create: `tests/test_api_clients.py`

**Step 1: Write failing tests**

```python
# tests/test_api_pipelines.py
import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.db.connection import init_db

@pytest.fixture
def client():
    init_db()
    return TestClient(app)

def test_create_pipeline(client):
    """Test pipeline creation"""
    response = client.post(
        "/pipelines",
        json={
            "name": "Test Pipeline",
            "description": "Test description",
            "script_dir": "src/scripts/test",
            "script_file": "analyzer.py",
            "skill_name": "test_skill"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Pipeline"
    assert "id" in data

def test_list_pipelines(client):
    """Test retrieving pipeline list"""
    response = client.get("/pipelines")
    assert response.status_code == 200
    data = response.json()
    assert "pipelines" in data
    assert isinstance(data["pipelines"], list)
```

```python
# tests/test_api_clients.py
import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.db.connection import init_db

@pytest.fixture
def client():
    init_db()
    return TestClient(app)

def test_create_client(client):
    """Test client creation"""
    response = client.post(
        "/clients",
        json={
            "client_name": "Test Client",
            "company_name": "Test Company",
            "package_name": "com.test.app"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["client_name"] == "Test Client"

def test_list_clients(client):
    """Test retrieving client list"""
    response = client.get("/clients")
    assert response.status_code == 200
    data = response.json()
    assert "clients" in data
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_pipelines.py tests/test_api_clients.py -v`
Expected: FAIL with import errors

**Step 3: Implement pipelines routes**

```python
# src/api/routes/pipelines.py
"""
Pipelines API Routes

Manages analysis pipeline configurations
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ulid import ULID
from datetime import datetime

from src.api.dependencies import get_db
from src.db.models import Pipeline

router = APIRouter(prefix="/pipelines", tags=["pipelines"])

class PipelineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    script_dir: str
    script_file: str
    skill_name: str

class PipelineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    script_dir: Optional[str] = None
    script_file: Optional[str] = None
    skill_name: Optional[str] = None
    status: Optional[str] = None

@router.post("", status_code=201)
async def create_pipeline(
    pipeline: PipelineCreate,
    db: Session = Depends(get_db)
):
    """Create new pipeline"""
    # Check for duplicate name
    existing = db.query(Pipeline).filter_by(name=pipeline.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Pipeline name already exists")

    new_pipeline = Pipeline(
        id=str(ULID()),
        name=pipeline.name,
        description=pipeline.description,
        script_dir=pipeline.script_dir,
        script_file=pipeline.script_file,
        skill_name=pipeline.skill_name,
        status="active"
    )

    db.add(new_pipeline)
    db.commit()
    db.refresh(new_pipeline)

    return {
        "id": new_pipeline.id,
        "name": new_pipeline.name,
        "description": new_pipeline.description,
        "script_dir": new_pipeline.script_dir,
        "script_file": new_pipeline.script_file,
        "skill_name": new_pipeline.skill_name,
        "status": new_pipeline.status
    }

@router.get("")
async def list_pipelines(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all pipelines"""
    query = db.query(Pipeline)

    if status:
        query = query.filter(Pipeline.status == status)

    pipelines = query.order_by(Pipeline.created_at.desc()).all()

    return {
        "pipelines": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "script_dir": p.script_dir,
                "script_file": p.script_file,
                "skill_name": p.skill_name,
                "status": p.status,
                "execution_count": p.execution_count
            }
            for p in pipelines
        ]
    }

@router.get("/{pipeline_id}")
async def get_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    """Get pipeline details"""
    pipeline = db.query(Pipeline).filter_by(id=pipeline_id).first()

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    return {
        "id": pipeline.id,
        "name": pipeline.name,
        "description": pipeline.description,
        "script_dir": pipeline.script_dir,
        "script_file": pipeline.script_file,
        "skill_name": pipeline.skill_name,
        "status": pipeline.status,
        "execution_count": pipeline.execution_count,
        "created_at": pipeline.created_at.isoformat(),
        "updated_at": pipeline.updated_at.isoformat()
    }

@router.put("/{pipeline_id}")
async def update_pipeline(
    pipeline_id: str,
    updates: PipelineUpdate,
    db: Session = Depends(get_db)
):
    """Update pipeline configuration"""
    pipeline = db.query(Pipeline).filter_by(id=pipeline_id).first()

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    # Update fields
    if updates.name:
        pipeline.name = updates.name
    if updates.description is not None:
        pipeline.description = updates.description
    if updates.script_dir:
        pipeline.script_dir = updates.script_dir
    if updates.script_file:
        pipeline.script_file = updates.script_file
    if updates.skill_name:
        pipeline.skill_name = updates.skill_name
    if updates.status:
        pipeline.status = updates.status

    pipeline.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Pipeline updated successfully"}
```

**Step 4: Implement clients routes**

```python
# src/api/routes/clients.py
"""
Clients API Routes

Manages client-package mapping configurations
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from ulid import ULID
from datetime import datetime
import csv
import io

from src.api.dependencies import get_db
from src.db.models import Client

router = APIRouter(prefix="/clients", tags=["clients"])

class ClientCreate(BaseModel):
    client_name: str
    company_name: Optional[str] = None
    package_name: str

class ClientUpdate(BaseModel):
    client_name: Optional[str] = None
    company_name: Optional[str] = None
    package_name: Optional[str] = None
    status: Optional[str] = None

@router.post("", status_code=201)
async def create_client(
    client: ClientCreate,
    db: Session = Depends(get_db)
):
    """Create new client"""
    # Check for duplicate
    existing = db.query(Client).filter_by(client_name=client.client_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Client already exists")

    new_client = Client(
        id=str(ULID()),
        client_name=client.client_name,
        company_name=client.company_name,
        package_name=client.package_name,
        status="active"
    )

    db.add(new_client)
    db.commit()
    db.refresh(new_client)

    return {
        "id": new_client.id,
        "client_name": new_client.client_name,
        "company_name": new_client.company_name,
        "package_name": new_client.package_name,
        "status": new_client.status
    }

@router.get("")
async def list_clients(
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all clients with optional filtering"""
    query = db.query(Client)

    if status:
        query = query.filter(Client.status == status)

    if search:
        query = query.filter(
            (Client.client_name.ilike(f"%{search}%")) |
            (Client.company_name.ilike(f"%{search}%")) |
            (Client.package_name.ilike(f"%{search}%"))
        )

    clients = query.order_by(Client.client_name).all()

    return {
        "clients": [
            {
                "id": c.id,
                "client_name": c.client_name,
                "company_name": c.company_name,
                "package_name": c.package_name,
                "status": c.status,
                "analysis_count": c.analysis_count
            }
            for c in clients
        ]
    }

@router.get("/{client_id}")
async def get_client(client_id: str, db: Session = Depends(get_db)):
    """Get client details"""
    client = db.query(Client).filter_by(id=client_id).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return {
        "id": client.id,
        "client_name": client.client_name,
        "company_name": client.company_name,
        "package_name": client.package_name,
        "status": client.status,
        "analysis_count": client.analysis_count,
        "created_at": client.created_at.isoformat()
    }

@router.put("/{client_id}")
async def update_client(
    client_id: str,
    updates: ClientUpdate,
    db: Session = Depends(get_db)
):
    """Update client information"""
    client = db.query(Client).filter_by(id=client_id).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if updates.client_name:
        client.client_name = updates.client_name
    if updates.company_name is not None:
        client.company_name = updates.company_name
    if updates.package_name:
        client.package_name = updates.package_name
    if updates.status:
        client.status = updates.status

    client.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Client updated successfully"}

@router.delete("/{client_id}")
async def delete_client(client_id: str, db: Session = Depends(get_db)):
    """Delete client (soft delete)"""
    client = db.query(Client).filter_by(id=client_id).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    client.status = "inactive"
    client.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Client deleted successfully"}

@router.post("/import")
async def import_clients(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Bulk import clients from CSV

    CSV format: client_name,company_name,package_name
    """
    content = await file.read()
    text = content.decode('utf-8')

    reader = csv.DictReader(io.StringIO(text))

    imported_count = 0
    skipped_count = 0

    for row in reader:
        client_name = row.get('client_name', '').strip()
        company_name = row.get('company_name', '').strip()
        package_name = row.get('package_name', '').strip()

        if not client_name or not package_name:
            skipped_count += 1
            continue

        # Check if exists
        existing = db.query(Client).filter_by(client_name=client_name).first()
        if existing:
            skipped_count += 1
            continue

        # Create new
        new_client = Client(
            id=str(ULID()),
            client_name=client_name,
            company_name=company_name if company_name else None,
            package_name=package_name,
            status="active"
        )
        db.add(new_client)
        imported_count += 1

    db.commit()

    return {
        "imported": imported_count,
        "skipped": skipped_count,
        "total": imported_count + skipped_count
    }
```

**Step 5: Update main app to include new routers**

```python
# Update src/api/main.py
from src.api.routes import jobs, pipelines, clients

# ... existing code ...

# Include routers
app.include_router(jobs.router)
app.include_router(pipelines.router)
app.include_router(clients.router)
```

**Step 6: Run tests to verify they pass**

Run: `pytest tests/test_api_pipelines.py tests/test_api_clients.py -v`
Expected: PASS (all tests)

**Step 7: Commit**

```bash
git add src/api/routes/pipelines.py src/api/routes/clients.py tests/test_api_pipelines.py tests/test_api_clients.py src/api/main.py
git commit -m "$(cat <<'EOF'
feat: add pipeline and client management APIs

- Implement pipeline CRUD operations
- Add client CRUD with search functionality
- Support bulk client import from CSV
- Include comprehensive tests for both resources
- Update main app to register new routers

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Web UI - Create Task Page

**Files:**
- Create: `src/ui/templates/base.html`
- Create: `src/ui/templates/create_task.html`
- Create: `src/ui/static/css/main.css`
- Create: `src/ui/static/js/create_task.js`
- Modify: `src/api/main.py`

**Step 1: Write test for UI route**

```python
# tests/test_ui_routes.py
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_ui_root_loads(client):
    """Test UI home page loads"""
    response = client.get("/ui")
    assert response.status_code == 200
    assert b"Create Task" in response.content or b"CDID" in response.content
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ui_routes.py -v`
Expected: FAIL with 404

**Step 3: Create base template**

```html
<!-- src/ui/templates/base.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}CDID Analysis Platform{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link href="/ui/static/css/main.css" rel="stylesheet">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container-fluid">
            <a class="navbar-brand" href="/ui">
                <i class="bi bi-graph-up"></i> CDID Analysis Platform
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="/ui">Create Task</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="/ui/jobs">Task List</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <main class="container my-4">
        {% block content %}{% endblock %}
    </main>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

**Step 4: Create task creation page**

```html
<!-- src/ui/templates/create_task.html -->
{% extends "base.html" %}

{% block title %}Create Task - CDID Analysis Platform{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-8 mx-auto">
        <h2 class="mb-4">Create Analysis Task</h2>

        <form id="createTaskForm" enctype="multipart/form-data">
            <div class="mb-3">
                <label for="name" class="form-label">Task Name *</label>
                <input type="text" class="form-control" id="name" name="name" required>
            </div>

            <div class="mb-3">
                <label for="clientName" class="form-label">Client Name *</label>
                <input type="text" class="form-control" id="clientName" name="client_name"
                       list="clientList" required autocomplete="off">
                <datalist id="clientList"></datalist>
                <small class="form-text text-muted">Start typing to search clients</small>
            </div>

            <div class="mb-3">
                <label for="packageName" class="form-label">Package Name *</label>
                <input type="text" class="form-control" id="packageName" name="package_name" required readonly>
                <small class="form-text text-muted">Auto-filled from client</small>
            </div>

            <div class="mb-3">
                <label for="pipeline" class="form-label">Pipeline *</label>
                <select class="form-select" id="pipeline" name="pipeline_id" required>
                    <option value="">Select pipeline...</option>
                </select>
            </div>

            <div class="row">
                <div class="col-md-6 mb-3">
                    <label for="startDate" class="form-label">Start Date *</label>
                    <input type="date" class="form-control" id="startDate" name="start_date" required>
                </div>
                <div class="col-md-6 mb-3">
                    <label for="endDate" class="form-label">End Date *</label>
                    <input type="date" class="form-control" id="endDate" name="end_date" required>
                </div>
            </div>

            <div class="mb-3">
                <label class="form-label">Message Types</label>
                <div>
                    <div class="form-check form-check-inline">
                        <input class="form-check-input" type="checkbox" id="msgDna" value="dna">
                        <label class="form-check-label" for="msgDna">DNA</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input class="form-check-input" type="checkbox" id="msgDaa" value="daa">
                        <label class="form-check-label" for="msgDaa">DAA</label>
                    </div>
                </div>
            </div>

            <div class="mb-3">
                <label for="file" class="form-label">CDID File *</label>
                <input type="file" class="form-control" id="file" name="file" accept=".csv,.txt" required>
                <small class="form-text text-muted">CSV format</small>
            </div>

            <div class="d-grid gap-2">
                <button type="submit" class="btn btn-primary btn-lg">
                    <i class="bi bi-play-circle"></i> Create Task
                </button>
            </div>
        </form>

        <div id="alertContainer" class="mt-3"></div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="/ui/static/js/create_task.js"></script>
{% endblock %}
```

**Step 5: Create JavaScript for interactivity**

```javascript
// src/ui/static/js/create_task.js
let clientPackageMap = {};

// Load clients on page load
async function loadClients() {
    try {
        const response = await fetch('/clients');
        const data = await response.json();

        const datalist = document.getElementById('clientList');
        data.clients.forEach(client => {
            const option = document.createElement('option');
            option.value = client.client_name;
            datalist.appendChild(option);

            clientPackageMap[client.client_name] = client.package_name;
        });
    } catch (error) {
        console.error('Failed to load clients:', error);
    }
}

// Load pipelines
async function loadPipelines() {
    try {
        const response = await fetch('/pipelines?status=active');
        const data = await response.json();

        const select = document.getElementById('pipeline');
        data.pipelines.forEach(pipeline => {
            const option = document.createElement('option');
            option.value = pipeline.id;
            option.textContent = `${pipeline.name} - ${pipeline.description || ''}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load pipelines:', error);
    }
}

// Auto-fill package name when client is selected
document.getElementById('clientName').addEventListener('input', function() {
    const clientName = this.value.trim();
    const packageNameInput = document.getElementById('packageName');

    if (clientPackageMap[clientName]) {
        packageNameInput.value = clientPackageMap[clientName];
        packageNameInput.readOnly = true;
    } else {
        packageNameInput.value = '';
        packageNameInput.readOnly = false;
    }
});

// Handle form submission
document.getElementById('createTaskForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData(this);

    // Add message types as JSON array
    const messageTypes = [];
    if (document.getElementById('msgDna').checked) messageTypes.push('dna');
    if (document.getElementById('msgDaa').checked) messageTypes.push('daa');
    formData.append('message_types', JSON.stringify(messageTypes));

    try {
        const response = await fetch('/jobs', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            showAlert('success', `Task created successfully! Job ID: ${data.job_id}`);

            // Redirect to task list after 2 seconds
            setTimeout(() => {
                window.location.href = '/ui/jobs';
            }, 2000);
        } else {
            const error = await response.json();
            showAlert('danger', `Failed to create task: ${error.detail}`);
        }
    } catch (error) {
        showAlert('danger', `Error: ${error.message}`);
    }
});

function showAlert(type, message) {
    const container = document.getElementById('alertContainer');
    container.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
}

// Initialize
loadClients();
loadPipelines();
```

**Step 6: Create basic CSS**

```css
/* src/ui/static/css/main.css */
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.navbar-brand {
    font-weight: 600;
}

.form-label {
    font-weight: 500;
}

.btn-lg {
    padding: 0.75rem 1.5rem;
}

.alert {
    animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

**Step 7: Add UI routes to FastAPI**

```python
# Update src/api/main.py
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

# Mount static files
app.mount("/ui/static", StaticFiles(directory="src/ui/static"), name="static")

# Templates
templates = Jinja2Templates(directory="src/ui/templates")

@app.get("/ui")
async def ui_home(request: Request):
    """Render create task page"""
    return templates.TemplateResponse("create_task.html", {"request": request})
```

**Step 8: Run test to verify it passes**

Run: `pytest tests/test_ui_routes.py -v`
Expected: PASS

**Step 9: Commit**

```bash
git add src/ui/ src/api/main.py tests/test_ui_routes.py
git commit -m "$(cat <<'EOF'
feat: add web UI for task creation

- Create base HTML template with Bootstrap 5
- Implement task creation form with file upload
- Add client auto-complete with package name auto-fill
- Load pipelines dynamically from API
- Include form validation and success/error alerts
- Mount static files and Jinja2 templates in FastAPI

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Docker Deployment Configuration

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`
- Create: `README.md`

**Step 1: Create Dockerfile**

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install Node.js for Gemini CLI
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Gemini CLI (adjust version as needed)
RUN npm install -g @google/generative-ai-cli

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p jobs && chmod 777 jobs

# Expose port
EXPOSE 8000

# Start script (both API server and worker)
CMD ["sh", "-c", "python -m src.worker.main & uvicorn src.api.main:app --host 0.0.0.0 --port 8000"]
```

**Step 2: Create docker-compose**

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./jobs:/app/jobs
      - ./src/scripts:/app/src/scripts
    environment:
      - DATABASE_URL=sqlite:///./jobs.db
      - INSIGHT_API_BASE_URL=http://172.17.129.204:6829
      - INSIGHT_API_TIMEOUT=600
      - INSIGHT_POLL_INTERVAL=60
      - GEMINI_CLI_PATH=gemini
      - GEMINI_CLI_TIMEOUT=300
      - JOBS_DIR=jobs
      - SCRIPTS_DIR=src/scripts
      - WORKER_POLL_INTERVAL=5
      - API_HOST=0.0.0.0
      - API_PORT=8000
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

**Step 3: Create .dockerignore**

```
# .dockerignore
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/
.env
jobs/
*.db
*.db-journal
.DS_Store
.git/
.gitignore
README.md
tests/
docs/
```

**Step 4: Create comprehensive README**

```markdown
# CDID Analysis Platform

Web-based platform for CDID data analysis, wrapping Gemini CLI workflows into an automated service.

## Features

- **Web UI**: Browser-based task creation and result viewing
- **Automated Pipeline**: Fetch data → Analyze → Generate reports
- **Client Management**: Map client names to package names
- **Pipeline Configuration**: Flexible analysis scripts and report templates
- **Retry Support**: Re-run failed tasks
- **Data Download**: Access raw data and HTML reports

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Access to internal API (172.17.129.204:6829)
- Gemini CLI credentials (configured in container)

### Installation

1. Clone repository:
```bash
git clone <repository-url>
cd cdid-analysis-platform
```

2. Create `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
# Edit .env as needed
```

3. Start services:
```bash
docker-compose up -d
```

4. Access Web UI:
```
http://localhost:8000/ui
```

5. API Documentation:
```
http://localhost:8000/docs
```

## Development Setup

### Local Development (without Docker)

1. Install Python 3.11+:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Install Gemini CLI:
```bash
npm install -g @google/generative-ai-cli
```

3. Initialize database:
```bash
python -c "from src.db.connection import init_db; init_db()"
```

4. Start API server:
```bash
uvicorn src.api.main:app --reload --port 8000
```

5. Start worker (in separate terminal):
```bash
python -m src.worker.main
```

### Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
cdid-analysis-platform/
├── src/
│   ├── api/                    # FastAPI application
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── jobs.py
│   │   │   ├── pipelines.py
│   │   │   └── clients.py
│   │   └── dependencies.py
│   ├── worker/                 # Background worker
│   │   ├── main.py
│   │   ├── insight_client.py
│   │   ├── pipeline_executor.py
│   │   └── gemini_reporter.py
│   ├── scripts/                # Analysis scripts
│   │   └── duplicate_detection/
│   │       └── analyzer.py
│   ├── db/                     # Database models
│   │   ├── models.py
│   │   └── connection.py
│   ├── ui/                     # Web UI
│   │   ├── templates/
│   │   └── static/
│   └── config.py
├── tests/                      # Test suite
├── jobs/                       # Runtime directory
├── docs/                       # Documentation
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Configuration

Key environment variables (see `.env.example`):

- `DATABASE_URL`: Database connection string
- `INSIGHT_API_BASE_URL`: Internal API endpoint
- `GEMINI_CLI_PATH`: Path to Gemini CLI executable
- `JOBS_DIR`: Directory for job files
- `SCRIPTS_DIR`: Directory for analysis scripts

## Adding New Pipelines

1. Create analysis script in `src/scripts/<pipeline-name>/analyzer.py`
2. Implement `analyze(input_file, user_info, start_date, end_date)` function
3. Create pipeline via API or Web UI:
   - Script directory: `src/scripts/<pipeline-name>`
   - Script file: `analyzer.py`
   - Skill name: `<your-gemini-skill>`

## API Endpoints

### Jobs
- `POST /jobs` - Create task
- `GET /jobs` - List tasks
- `GET /jobs/{id}` - Get task details
- `GET /jobs/{id}/report` - Get HTML report
- `GET /jobs/{id}/raw-data` - Download raw data
- `POST /jobs/{id}/retry` - Retry failed task

### Pipelines
- `GET /pipelines` - List pipelines
- `POST /pipelines` - Create pipeline
- `PUT /pipelines/{id}` - Update pipeline

### Clients
- `GET /clients` - List clients
- `POST /clients` - Create client
- `POST /clients/import` - Bulk import from CSV

## Troubleshooting

### Worker not processing jobs
- Check worker logs: `docker-compose logs -f app`
- Verify database connection
- Check internal API accessibility

### Gemini CLI errors
- Verify Gemini CLI installation: `gemini --version`
- Check skill availability
- Review worker error logs

### Database errors
- Reset database: `rm jobs.db && python -c "from src.db.connection import init_db; init_db()"`

## License

[Add license information]

## Contributors

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml .dockerignore README.md
git commit -m "$(cat <<'EOF'
feat: add Docker deployment configuration

- Create Dockerfile with Python 3.11 and Node.js
- Add docker-compose for single-command deployment
- Include .dockerignore for efficient builds
- Write comprehensive README with setup instructions
- Document API endpoints and configuration options

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Summary

**Plan complete and saved to `docs/plans/2026-01-24-cdid-analysis-platform-mvp.md`.**

This implementation plan covers the complete MVP of the CDID Analysis Platform:

1. **Task 1**: Database schema and configuration (models, connection, settings)
2. **Task 2**: Internal API client (create task, poll status, download results)
3. **Task 3**: Analysis script template and executor (duplicate detection, dynamic loading)
4. **Task 4**: Gemini CLI reporter (HTML generation via stdin pipe)
5. **Task 5**: Worker main loop (4-stage pipeline: fetch, analyze, report, done)
6. **Task 6**: FastAPI server core (jobs CRUD, file upload, report serving)
7. **Task 7**: Pipeline and client management APIs (configuration endpoints)
8. **Task 8**: Web UI (task creation page with Bootstrap 5)
9. **Task 9**: Docker deployment (Dockerfile, docker-compose, README)

Each task follows TDD principles with:
- Test-first approach (write failing test → implement → verify passing)
- Specific file paths and complete code
- Clear commit messages with co-authorship
- Bite-sized steps (2-5 minutes each)

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach would you like?**
