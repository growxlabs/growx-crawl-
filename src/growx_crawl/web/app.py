import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from growx_crawl.discovery.registry import ProviderRegistry
from growx_crawl.enrichment.bde_brief import BDEBriefGenerator
from growx_crawl.events import CrawlEventBroadcaster
from growx_crawl.exporters import XLSXExporter
from growx_crawl.jobs.engine import CrawlJobEngine
from growx_crawl.models import Company
from growx_crawl.storage import ErrorRepository, JobRepository, LeadRepository, get_db
from growx_crawl.api.v1.router import v1_router
from growx_crawl.api.v1.ops_router import ops_router

app = FastAPI(title="GrowX Crawl - Web Intelligence & Crawling API")

app.include_router(v1_router, prefix="/v1")
app.include_router(v1_router, prefix="/api/v1")
app.include_router(ops_router, prefix="/api")

# Phase 15 Root Health Probes
@app.get("/health/live")
def root_health_live():
    from growx_crawl.ops.health import check_liveness
    return check_liveness()


@app.get("/health/ready")
def root_health_ready():
    from growx_crawl.ops.health import check_readiness
    res = check_readiness()
    if res["status"] != "ready":
        raise HTTPException(status_code=503, detail=res)
    return res


@app.get("/health/dependencies")
def root_health_dependencies():
    from growx_crawl.ops.health import check_dependencies
    return check_dependencies()


STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.middleware("http")
async def track_metrics_and_cache_middleware(request: Request, call_next):
    import time
    start = time.time()
    is_err = False
    try:
        response = await call_next(request)
        if response.status_code >= 500:
            is_err = True
        path = request.url.path
        if path.startswith("/static") or path == "/":
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response
    except Exception:
        is_err = True
        raise
    finally:
        dur = (time.time() - start) * 1000
        try:
            from growx_crawl.ops.metrics import metrics_collector
            metrics_collector.record_request(dur, is_error=is_err)
        except Exception:
            pass


class CreateJobRequest(BaseModel):
    query: Optional[str] = None
    industry: Optional[str] = "Jewellery"
    location: Optional[str] = "Hyderabad"
    limit: int = 50
    workers: int = 5
    depth: int = 2
    provider: str = "auto"
    seed_file: Optional[str] = None


class ReviewLeadRequest(BaseModel):
    company_id: str
    status: str  # approved, rejected, needs_review, pending


class BulkReviewRequest(BaseModel):
    company_ids: List[str]
    status: str


class ExportRequest(BaseModel):
    job_id: str
    format: str = "xlsx"
    stage: str = "all"
    priority: Optional[str] = None


@app.get("/")
@app.get("/console")
@app.get("/dashboard")
def read_root():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/home")
@app.get("/landing")
def read_landing():
    return FileResponse(str(STATIC_DIR / "landing.html"))


@app.get("/ops")
@app.get("/admin")
def read_ops():
    return FileResponse(str(STATIC_DIR / "ops.html"))


@app.get("/api/industries")
def list_industries():
    from growx_crawl.core.industry import IndustryProfileRegistry
    return IndustryProfileRegistry.list_industry_names()


class AgentRunRequest(BaseModel):
    prompt: str


@app.post("/api/agent/run")
def trigger_agent_run(req: AgentRunRequest, bg_tasks: BackgroundTasks):
    from growx_crawl.agent import AgentRuntime
    runtime = AgentRuntime()
    bg_tasks.add_task(runtime.execute_goal, req.prompt)
    return {"status": "started", "message": f"Agent task initiated for prompt: {req.prompt}"}


@app.get("/api/agent/status/{run_id}")
def get_agent_run_status(run_id: str):
    from growx_crawl.storage import AgentRunRepository
    repo = AgentRunRepository()
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return run


@app.get("/api/overview")
def get_overview():
    lead_repo = LeadRepository()
    return lead_repo.get_dashboard_overview()


@app.get("/api/jobs")
def list_jobs(limit: int = 50):
    job_repo = JobRepository()
    jobs = job_repo.list_jobs(limit=limit)
    return [j.model_dump(mode="json") for j in jobs]


@app.post("/api/jobs")
async def create_job(req: CreateJobRequest):
    engine = CrawlJobEngine()
    # Run crawl job asynchronously in background
    asyncio.create_task(
        engine.start_job(
            query=req.query,
            limit=req.limit,
            workers=req.workers,
            depth=req.depth,
            location=req.location,
            industry=req.industry,
            provider_type=req.provider,
            seed_file=req.seed_file,
        )
    )
    return {"status": "started", "message": "Job initiated in background"}


@app.get("/api/jobs/{job_id}/activity")
def get_job_activity(job_id: str):
    events = CrawlEventBroadcaster.get_recent_events(job_id)
    return [e.model_dump(mode="json") for e in events]


@app.get("/api/jobs/{job_id}/events")
async def stream_job_events(request: Request, job_id: str):
    async def event_generator():
        # First yield recent events history
        recent = CrawlEventBroadcaster.get_recent_events(job_id)
        for ev in recent:
            yield f"data: {ev.model_dump_json()}\n\n"

        queue = CrawlEventBroadcaster.subscribe(job_id)
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {event.model_dump_json()}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat comment to keep connection alive
                    yield ": heartbeat\n\n"
        finally:
            CrawlEventBroadcaster.unsubscribe(job_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/jobs/{job_id}")
def get_job_detail(job_id: str):
    job_repo = JobRepository()
    job = job_repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.model_dump(mode="json")


@app.get("/api/leads")
def list_leads(
    job_id: Optional[str] = None,
    priority: Optional[str] = None,
    review_status: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 50,
):
    lead_repo = LeadRepository()
    if job_id:
        leads = lead_repo.get_job_lead_candidates(job_id)
    else:
        # Load all recent leads
        with get_db(lead_repo.db_path) as conn:
            rows = conn.execute("SELECT id FROM crawl_jobs ORDER BY created_at DESC LIMIT 1").fetchone()
            if rows:
                leads = lead_repo.get_job_lead_candidates(rows["id"])
            else:
                leads = []

    # Filter in-memory for dashboard
    filtered = []
    for l in leads:
        company = Company(**l)
        brief = BDEBriefGenerator.generate_brief(company)
        item = {
            "id": company.id,
            "job_id": company.job_id,
            "company_name": brief.company_name,
            "industry": brief.industry,
            "city": brief.city,
            "website": brief.website,
            "website_missing": brief.website_missing,
            "primary_phone": brief.primary_phone,
            "primary_email": brief.primary_email,
            "whatsapp": brief.whatsapp,
            "primary_decision_maker": brief.primary_decision_maker,
            "decision_maker_role": brief.decision_maker_role,
            "decision_maker_tier": brief.decision_maker_tier,
            "score": l.get("score", 0),
            "priority": l.get("priority", "Low"),
            "review_status": company.review_status,
            "research_summary": brief.research_summary,
            "prospect_flags": brief.prospect_flags,
        }

        if priority and item["priority"].lower() != priority.lower():
            continue
        if review_status and item["review_status"].lower() != review_status.lower():
            continue
        if q and q.lower() not in item["company_name"].lower():
            continue

        filtered.append(item)

    return filtered[:limit]


@app.post("/api/leads/review")
def review_lead(req: ReviewLeadRequest):
    lead_repo = LeadRepository()
    lead_repo.update_company_review_status(req.company_id, req.status)
    return {"status": "success", "company_id": req.company_id, "review_status": req.status}


@app.post("/api/leads/bulk-review")
def bulk_review_leads(req: BulkReviewRequest):
    lead_repo = LeadRepository()
    lead_repo.bulk_update_review_status(req.company_ids, req.status)
    return {"status": "success", "count": len(req.company_ids), "review_status": req.status}


@app.get("/api/sources")
def get_sources():
    registry = ProviderRegistry()
    return registry.get_provider_health()


@app.get("/api/errors")
def list_errors(job_id: Optional[str] = None):
    err_repo = ErrorRepository()
    if job_id:
        return err_repo.list_job_errors(job_id)
    return []


@app.post("/api/export")
def trigger_export(req: ExportRequest):
    exporter = XLSXExporter()
    out_path = f"exports/{req.job_id}_{req.stage}_leads.xlsx"
    path = exporter.export_job(req.job_id, out_path, stage=req.stage)
    return {"status": "success", "file_path": path}
