"""API 任务相关测试"""

import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def _load_test_app(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("CDID_DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("CDID_STORAGE_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("CDID_STORAGE_OUTPUT_DIR", str(tmp_path / "outputs"))

    import src.config as config_module
    import src.db.connection as connection_module

    config_module.config = None
    connection_module._engine = None

    if "src.api.main" in sys.modules:
        importlib.reload(sys.modules["src.api.main"])
    else:
        import src.api.main  # noqa: F401

    return sys.modules["src.api.main"].app


def test_create_job_success(tmp_path, monkeypatch):
    app = _load_test_app(tmp_path, monkeypatch)

    with TestClient(app) as client:
        pipelines_response = client.get("/api/pipelines")
        assert pipelines_response.status_code == 200
        pipelines = pipelines_response.json()
        assert pipelines, "expected default pipeline"
        default_pipeline = next((p for p in pipelines if p.get("is_default")), pipelines[0])

        response = client.post(
            "/api/jobs",
            data={
                "name": "测试任务",
                "package_name": "com.test",
                "start_date": "2026-01-01",
                "end_date": "2026-01-07",
                "message_types": "dna",
                "pipeline_ids": str(default_pipeline["id"]),
            },
            files={"file": ("test.csv", b"oaid,did\n1,2\n", "text/csv")},
        )

        assert response.status_code == 201, response.text
        job = response.json()
        assert len(job["id"]) == 26
        assert job["status"] == "queued"
        assert job["message_types"] == ["dna"]
        assert job["pipeline_ids"] == [default_pipeline["id"]]
        assert Path(job["input_file_path"]).exists()

        list_response = client.get("/api/jobs")
        assert list_response.status_code == 200
        payload = list_response.json()
        assert payload["total"] == 1
        assert payload["jobs"][0]["id"] == job["id"]
