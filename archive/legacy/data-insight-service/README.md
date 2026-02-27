# Data Insight Service

**Version**: 0.1.0
**Status**: Phase 0 (Task Skeleton)

---

## Overview

Data Insight Service is a **spec-driven** data analysis platform built with:
- **Python Skills**: Pluggable analysis capabilities
- **FastAPI**: High-performance async API
- **Single-threaded FIFO**: Simplified orchestration
- **Web UI + CLI**: User-friendly interfaces

**Core Workflow**:
```
User submits Job → API receives → Queue → Worker FIFO processes → Outputs HTML Report + Bundle
```

**Status Machine**: `queued → fetching → preprocessing → analyzing → reporting → done` (or `failed`)

---

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### 2. Initialize Database

```bash
# Create jobs.db (SQLite)
python -c "from src.db.connection import init_db; init_db()"
```

### 3. Start Service

```bash
# Option 1: Start API + Worker together
insight-cli server start

# Option 2: Start separately
# Terminal 1: API Server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Worker
insight-cli worker start
```

### 4. Access Web UI

Open browser: http://localhost:8000/ui

### 5. Create a Job (CLI)

```bash
insight-cli job create test.csv --params '{
  "package_name": "com.example.app",
  "skills": {"enabled": ["basic_stats"]}
}'
```

### 6. Check Job Status

```bash
insight-cli job get <job_id>
# Or watch in real-time
insight-cli job get <job_id> --watch
```

---

## Project Structure

```
data-insight-service/
├── docs/                       # Documentation (Phase 0 deliverable)
│   ├── ARCHITECTURE.md         # System architecture
│   ├── OVERRIDES.md            # Spec overrides
│   ├── CONFIG.md               # Configuration guide
│   ├── API_MAPPING.md          # API consistency
│   └── CLI_USAGE.md            # CLI reference
├── config/                     # Configuration
│   ├── config.yaml             # Default config
│   └── config.schema.json      # JSON Schema
├── src/
│   ├── api/                    # FastAPI application
│   ├── worker/                 # Worker + orchestration
│   ├── db/                     # Database models
│   ├── models/                 # Pydantic models
│   ├── ui/                     # Web UI (Jinja2)
│   ├── cli/                    # CLI tool (Click)
│   └── config.py               # Config loader
├── analysis_skills/            # Skills plugins
│   └── plugins/
│       └── basic_stats/        # MVP skill
├── jobs/                       # Runtime (gitignored)
├── tests/                      # Tests
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Phase 0 Status

**Implemented** (Task Skeleton):
- ✅ Complete documentation (D1-D5)
- ✅ Configuration system (YAML + ENV + CLI)
- ✅ Project structure
- ✅ Database models
- ✅ FastAPI API endpoints (contract-compliant)
- ✅ Worker state machine skeleton (mock execution)
- ✅ Minimal Web UI (create + list + detail)
- ✅ CLI tool (job + worker + server commands)
- ✅ Basic tests

**NOT Implemented** (Phase 1+):
- ❌ Real fetch (mock: sleep 0.5s)
- ❌ Real preprocess (mock: sleep 0.8s)
- ❌ Real skills execution (mock: sleep 1s)
- ❌ Real report generation (mock HTML)
- ❌ Bundle.zip creation (empty file)

**Phase 0 Goal**: Prove state machine flow works end-to-end (FIFO, status updates, logs)

---

## Key Design Decisions (Overrides)

1. **O1: No Authentication** - Internal network deployment, trust boundary
2. **O2: Dynamic Schema** - No hardcoded Excel field names
3. **O3: Single-threaded FIFO** - Global concurrency=1, simplifies orchestration
4. **O4: Web UI + CLI Required** - Complete product experience

See `docs/OVERRIDES.md` for details.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/jobs` | Create a job |
| GET | `/jobs/{id}` | Get job status |
| GET | `/jobs/{id}/report` | Download HTML report (when done) |
| GET | `/jobs/{id}/bundle` | Download bundle.zip (when done) |
| GET | `/ui` | Web UI - Create job form |
| GET | `/ui/jobs` | Web UI - Job list |
| GET | `/ui/jobs/{id}` | Web UI - Job detail (with polling) |

**OpenAPI Docs**: http://localhost:8000/docs

---

## CLI Commands

```bash
# Job management
insight-cli job create <file> --params <json>
insight-cli job list [--status queued|done|failed]
insight-cli job get <job_id>
insight-cli job delete <job_id>

# Worker management
insight-cli worker start [--poll-interval 5]
insight-cli worker stop
insight-cli worker status

# Server management
insight-cli server start [--host 0.0.0.0 --port 8000]
insight-cli server stop

# Configuration
insight-cli config show
insight-cli config validate
```

See `docs/CLI_USAGE.md` for full reference.

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_api.py::test_create_job
```

---

## Configuration

Configuration priority: **CLI > ENV > YAML**

**Environment variables**:
```bash
export DIS_API_PORT=9000
export DIS_DATABASE_URL="postgresql://user:pass@localhost/db"
export DIS_LOGGING_LEVEL=DEBUG
```

See `docs/CONFIG.md` for full guide.

---

## Development

```bash
# Enable hot reload
export DIS_API_RELOAD=true
export DIS_LOGGING_LEVEL=DEBUG
insight-cli server start

# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

---

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
ENV DIS_API_HOST=0.0.0.0
ENV DIS_API_PORT=8000
CMD ["insight-cli", "server", "start"]
```

```bash
docker build -t data-insight-service .
docker run -d -p 8000:8000 \
  -v $(pwd)/jobs:/app/jobs \
  --name dis-service \
  data-insight-service
```

### Systemd

See `docs/CLI_USAGE.md` → "Production Deployment" section.

---

## Roadmap

- **Phase 0 (Current)**: Task skeleton + documentation ✅
- **Phase 1**: Real fetch + preprocess implementation
- **Phase 2**: Real skills execution (basic_stats)
- **Phase 3**: Real HTML report generation
- **Phase 4**: Optimizations (PostgreSQL, parallel skills)

---

## Spec Compliance

This project strictly follows `specs_v0_1/`:
- `SPEC_01_SYSTEM.md`: System overview
- `SPEC_02_API.md`: API contract (100% aligned)
- `SPEC_03_DATASET.md`: Dataset structure (Phase 1)
- `SPEC_04_SKILLS.md`: Skills interface (Phase 2)
- `SPEC_05_ORCHESTRATION.md`: State machine (Phase 0 skeleton)
- `SPEC_06_REPORTING.md`: HTML reports (Phase 3)
- `SPEC_07_OBSERVABILITY_SECURITY.md`: Logging (basic)
- `SPEC_08_TESTING_ACCEPTANCE.md`: Tests (Phase 0 basic)

See `docs/API_MAPPING.md` for consistency details.

---

## License

MIT

---

## Contributing

1. Read `docs/ARCHITECTURE.md` first
2. Check `docs/OVERRIDES.md` for design constraints
3. Follow code style (black + ruff)
4. Add tests for new features
5. Update docs when changing behavior

---

## Contact

**Project**: Internal Data Insight Service
**Version**: 0.1.0 (MVP)
**Status**: Phase 0 Complete - Awaiting Review
