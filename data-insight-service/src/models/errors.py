"""
Error models (Pydantic) - Aligned with SPEC_02_API.md
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class Error(BaseModel):
    """
    Error object (MUST conform to SPEC_02).

    Fields:
    - code: Error code enum (e.g., "JOB_NOT_FOUND")
    - message: Human-readable message
    - details: Additional error context
    - retryable: Whether the operation can be retried
    """

    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    retryable: bool = False


class ErrorResponse(BaseModel):
    """
    Error response wrapper (top-level).

    Example:
    {
      "error": {
        "code": "JOB_NOT_FOUND",
        "message": "Job 01J... not found",
        "details": {},
        "retryable": false
      }
    }
    """

    error: Error


# Error code constants (from SPEC_02 Section 7)
ERROR_INVALID_REQUEST = "INVALID_REQUEST"
ERROR_JOB_NOT_FOUND = "JOB_NOT_FOUND"
ERROR_JOB_NOT_READY = "JOB_NOT_READY"
ERROR_UPLOAD_INVALID_FILE = "UPLOAD_INVALID_FILE"
ERROR_FETCH_UPSTREAM_FAILED = "FETCH_UPSTREAM_FAILED"
ERROR_FETCH_TIMEOUT = "FETCH_TIMEOUT"
ERROR_PREPROCESS_FAILED = "PREPROCESS_FAILED"
ERROR_SKILL_FAILED = "SKILL_FAILED"
ERROR_REPORT_FAILED = "REPORT_FAILED"
ERROR_INTERNAL_ERROR = "INTERNAL_ERROR"


# Error factory functions (for consistency)
def error_invalid_request(message: str, details: dict = None) -> ErrorResponse:
    """Invalid request (400)"""
    return ErrorResponse(
        error=Error(
            code=ERROR_INVALID_REQUEST,
            message=message,
            details=details or {},
            retryable=False,
        )
    )


def error_not_found(job_id: str) -> ErrorResponse:
    """Job not found (404)"""
    return ErrorResponse(
        error=Error(
            code=ERROR_JOB_NOT_FOUND,
            message=f"Job {job_id} not found",
            details={},
            retryable=False,
        )
    )


def error_not_ready(job_id: str, current_status: str) -> ErrorResponse:
    """Job not ready (409)"""
    return ErrorResponse(
        error=Error(
            code=ERROR_JOB_NOT_READY,
            message=f"Job {job_id} is not done (current status: {current_status})",
            details={"current_status": current_status},
            retryable=True,
        )
    )


def error_upload_invalid(message: str) -> ErrorResponse:
    """Invalid uploaded file (400)"""
    return ErrorResponse(
        error=Error(
            code=ERROR_UPLOAD_INVALID_FILE,
            message=message,
            details={},
            retryable=False,
        )
    )


def error_fetch_failed(details: dict) -> ErrorResponse:
    """Upstream fetch failed (500)"""
    return ErrorResponse(
        error=Error(
            code=ERROR_FETCH_UPSTREAM_FAILED,
            message="Failed to fetch data from upstream API",
            details=details,
            retryable=True,
        )
    )


def error_preprocess_failed(message: str) -> ErrorResponse:
    """Data preprocessing failed (500)"""
    return ErrorResponse(
        error=Error(
            code=ERROR_PREPROCESS_FAILED,
            message=message,
            details={},
            retryable=False,
        )
    )


def error_skill_failed(skill_name: str, message: str) -> ErrorResponse:
    """Skill execution failed (500)"""
    return ErrorResponse(
        error=Error(
            code=ERROR_SKILL_FAILED,
            message=f"Skill '{skill_name}' failed: {message}",
            details={"skill": skill_name},
            retryable=False,
        )
    )


def error_report_failed(message: str) -> ErrorResponse:
    """Report generation failed (500)"""
    return ErrorResponse(
        error=Error(
            code=ERROR_REPORT_FAILED,
            message=message,
            details={},
            retryable=True,
        )
    )


def error_internal(message: str = "Internal server error") -> ErrorResponse:
    """Internal error (500)"""
    return ErrorResponse(
        error=Error(
            code=ERROR_INTERNAL_ERROR,
            message=message,
            details={},
            retryable=False,
        )
    )
