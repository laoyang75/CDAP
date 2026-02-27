"""
Job models (Pydantic) - API request/response schemas
Aligned with openapi.yaml and SPEC_02_API.md
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from src.models.errors import Error


class Progress(BaseModel):
    """Job progress (percent + message)"""

    percent: int = Field(ge=0, le=100, description="Progress percentage (0-100)")
    message: str = Field(description="Progress message")


class JobCreated(BaseModel):
    """Response for POST /jobs (201 Created)"""

    job_id: str
    status: str
    created_at: str  # ISO-8601 UTC
    links: Dict[str, str]


class JobStatus(BaseModel):
    """Response for GET /jobs/{id} (200 OK)"""

    job_id: str
    status: str
    stage: str
    progress: Progress
    created_at: str  # ISO-8601 UTC
    updated_at: str  # ISO-8601 UTC
    artifacts: Dict[str, Optional[str]]  # {report_html: str | None, bundle_zip: str | None}
    error: Optional[Error] = None


# Job creation request params (embedded in multipart form)
class JobParams(BaseModel):
    """Job parameters (passed as JSON string in multipart form)"""

    package_name: str
    time_range: Optional[Dict[str, str]] = None  # {start: "2026-01-01", end: "2026-01-07"}
    message_types: list[str] = Field(default_factory=lambda: ["dna", "daa"])
    skills: Dict[str, Any] = Field(
        default_factory=lambda: {"enabled": ["basic_stats"], "params": {}}
    )
    report: Dict[str, Any] = Field(
        default_factory=lambda: {"format": "html", "llm": {"enabled": False}}
    )
