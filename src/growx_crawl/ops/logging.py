"""
Structured JSON logging and request correlation for GrowX.
"""

from contextvars import ContextVar
from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, Optional

# Request & execution correlation context variables
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
job_id_var: ContextVar[Optional[str]] = ContextVar("job_id", default=None)
run_id_var: ContextVar[Optional[str]] = ContextVar("run_id", default=None)
company_id_var: ContextVar[Optional[str]] = ContextVar("company_id", default=None)


def set_correlation_context(
    request_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    job_id: Optional[str] = None,
    run_id: Optional[str] = None,
    company_id: Optional[str] = None,
):
    if request_id:
        request_id_var.set(request_id)
    if trace_id:
        trace_id_var.set(trace_id)
    if job_id:
        job_id_var.set(job_id)
    if run_id:
        run_id_var.set(run_id)
    if company_id:
        company_id_var.set(company_id)


def get_correlation_context() -> Dict[str, Optional[str]]:
    return {
        "request_id": request_id_var.get(),
        "trace_id": trace_id_var.get(),
        "job_id": job_id_var.get(),
        "run_id": run_id_var.get(),
        "company_id": company_id_var.get(),
    }


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as JSON lines with correlation IDs and timestamps."""

    def format(self, record: logging.LogRecord) -> str:
        ctx = get_correlation_context()
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation": {k: v for k, v in ctx.items() if v is not None},
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_entry["data"] = record.extra_data

        return json.dumps(log_entry)


def configure_logging(structured: bool = False, level: str = "INFO"):
    """Configures root logging with either human-readable or structured JSON formatter."""
    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler()
    if structured:
        handler.setFormatter(StructuredJsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )

    root.handlers = [handler]
