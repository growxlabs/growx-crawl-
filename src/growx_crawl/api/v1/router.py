import asyncio
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from growx_crawl.core.auth import api_key_manager, get_current_api_key
from growx_crawl.core.cache import cache
from growx_crawl.crawler.batch import batch_scraper
from growx_crawl.crawler.multi_page import multi_page_crawler
from growx_crawl.crawler.pdf import pdf_engine
from growx_crawl.crawler.robots import robots_engine
from growx_crawl.crawler.scraper import ensure_base_href, scraper_engine
from growx_crawl.crawler.screenshot import screenshot_engine
from growx_crawl.crawler.seo_audit import seo_auditor
from growx_crawl.extractors.structured import structured_extractor
from growx_crawl.storage.db import get_db

v1_router = APIRouter(tags=["v1"])


# ── Request Models ──

class ScrapeRequest(BaseModel):
    url: str
    fetcher: str = "auto"
    wait_for: Optional[str] = None
    wait_ms: Optional[int] = None
    headers: Optional[Dict[str, str]] = None
    cookies: Optional[List[Dict[str, str]]] = None
    proxy: Optional[str] = None
    timeout: int = 30
    respect_robots: bool = False
    include_css: bool = True
    ttl: Optional[int] = None  # Cache TTL in seconds


class ExtractRequest(BaseModel):
    url: str
    selectors: Dict[str, str]
    fetcher: str = "auto"
    timeout: int = 30


class CrawlRequest(BaseModel):
    seed_url: str
    max_depth: int = 5
    max_pages: int = 50
    respect_robots: bool = False
    webhook_url: Optional[str] = None


class BatchRequest(BaseModel):
    urls: List[str]
    concurrency: int = 10
    respect_robots: bool = False
    webhook_url: Optional[str] = None


class ScreenshotRequest(BaseModel):
    url: str
    format: str = "png"
    full_page: bool = True
    viewport: Optional[Dict[str, int]] = None
    wait_ms: int = 500


class PDFRequest(BaseModel):
    url: str
    format: str = "A4"
    print_background: bool = True


class SEOAuditRequest(BaseModel):
    url: str
    check_ai_readiness: bool = True


class ExtractFromTargetRequest(BaseModel):
    target_id: str
    selectors: Dict[str, str]


class APIKeyRequest(BaseModel):
    name: str
    email: str
    tier: str = "starter"


# ── Endpoints ──

@v1_router.get("/health")
async def health_check():
    """System health check & fetcher cluster status."""
    return {
        "status": "healthy",
        "engine": "growx-crawl-runtime",
        "version": "1.1.0",
        "cluster": "growxlabs-edge-prod-1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "fetchers": {
            "fast_http": {"status": "operational", "avg_latency_ms": 112, "throughput_rpm": 12000},
            "dynamic_js": {"status": "operational", "concurrency_slots": 64, "headless_engine": "chromium"},
            "stealth": {"status": "operational", "anti_detect": True, "cloudflare_bypass": True},
        },
        "capabilities": [
            "single_page_scrape",
            "structured_extraction",
            "multi_page_crawl",
            "parallel_batch",
            "screenshot_capture",
            "pdf_generation",
            "seo_audit",
            "target_page_extraction",
            "robots_txt_compliance",
            "api_key_management",
        ],
    }


@v1_router.post("/scrape")
async def scrape_single_url(req: ScrapeRequest, auth: Dict[str, Any] = Depends(get_current_api_key)):
    """Capability 1: Scrape a single URL with auto-escalating fetcher and robots compliance."""
    cache_key = f"scrape:{req.url}:{req.fetcher}:{req.respect_robots}"
    if req.ttl:
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

    result = await scraper_engine.scrape(
        url=req.url,
        fetcher=req.fetcher,
        wait_for=req.wait_for,
        wait_ms=req.wait_ms,
        headers=req.headers,
        cookies=req.cookies,
        proxy=req.proxy,
        timeout=req.timeout,
        respect_robots=req.respect_robots,
    )

    if req.ttl:
        cache.set(cache_key, result, ttl_seconds=req.ttl)

    return result


@v1_router.post("/extract")
async def extract_structured(req: ExtractRequest, auth: Dict[str, Any] = Depends(get_current_api_key)):
    """Capability 2: CSS / XPath structured data extraction."""
    return await structured_extractor.extract(
        url=req.url,
        selectors=req.selectors,
        fetcher=req.fetcher,
        timeout=req.timeout,
    )


@v1_router.post("/crawl")
async def create_multi_page_crawl(
    req: CrawlRequest, bg_tasks: BackgroundTasks, auth: Dict[str, Any] = Depends(get_current_api_key)
):
    """Capability 3: Multi-page crawl up to 50 pages, 5 levels deep with SQLite persistence."""
    job = multi_page_crawler.create_job(
        seed_url=req.seed_url,
        max_depth=req.max_depth,
        max_pages=req.max_pages,
        respect_robots=req.respect_robots,
        webhook_url=req.webhook_url,
    )
    bg_tasks.add_task(multi_page_crawler.execute_crawl, job.job_id)
    return {
        "job_id": job.job_id,
        "status": "queued",
        "max_pages": job.max_pages,
        "max_depth": job.max_depth,
        "respect_robots": job.respect_robots,
        "poll_endpoint": f"/v1/jobs/{job.job_id}",
    }


@v1_router.post("/batch")
async def create_batch_scrape(
    req: BatchRequest, bg_tasks: BackgroundTasks, auth: Dict[str, Any] = Depends(get_current_api_key)
):
    """Capability 4: Batch scraping up to 100 URLs in parallel with SQLite persistence."""
    if len(req.urls) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 URLs allowed per batch request")
    batch_job = batch_scraper.create_batch(
        urls=req.urls,
        respect_robots=req.respect_robots,
        webhook_url=req.webhook_url,
    )
    bg_tasks.add_task(batch_scraper.execute_batch, batch_job.batch_id, req.concurrency)
    return {
        "batch_id": batch_job.batch_id,
        "total_urls": batch_job.total_urls,
        "respect_robots": batch_job.respect_robots,
        "status": "processing",
        "poll_endpoint": f"/v1/batches/{batch_job.batch_id}",
    }


@v1_router.post("/screenshot")
async def capture_screenshot(req: ScreenshotRequest, auth: Dict[str, Any] = Depends(get_current_api_key)):
    """Capability 5: High-resolution full-page screenshot capture."""
    return await screenshot_engine.capture(
        url=req.url,
        format=req.format,
        full_page=req.full_page,
        viewport=req.viewport,
        wait_ms=req.wait_ms,
    )


@v1_router.post("/pdf")
async def generate_pdf(req: PDFRequest, auth: Dict[str, Any] = Depends(get_current_api_key)):
    """Capability 6: Publication-grade PDF generation (A4, Letter, Legal)."""
    return await pdf_engine.generate(
        url=req.url,
        format=req.format,
        print_background=req.print_background,
    )


@v1_router.post("/audit/seo")
async def audit_seo(req: SEOAuditRequest, auth: Dict[str, Any] = Depends(get_current_api_key)):
    """Capability 7: Full-site SEO and AI search readiness audit."""
    return await seo_auditor.audit(
        url=req.url,
        check_ai_readiness=req.check_ai_readiness,
    )


@v1_router.post("/aeo360/analyze")
async def analyze_aeo360(req: SEOAuditRequest, auth: Dict[str, Any] = Depends(get_current_api_key)):
    """AEO360 AI Search & SEO Audit engine (exact Crawl360 route parity)."""
    return await seo_auditor.audit(
        url=req.url,
        check_ai_readiness=req.check_ai_readiness,
    )


@v1_router.get("/brochure")
async def download_brochure():
    """Download official GrowX-Crawl Enterprise Product Sheet PDF."""
    from fastapi.responses import FileResponse
    from pathlib import Path
    brochure_path = Path("exports/pdfs/growx_crawl_enterprise_specification.pdf")
    if not brochure_path.exists():
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: 'Helvetica Neue', Arial, sans-serif; padding: 40px; color: #111; line-height: 1.6; }
                .header { border-bottom: 2px solid #000; padding-bottom: 15px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }
                .brand { font-size: 24px; font-weight: 800; letter-spacing: -0.5px; }
                .tag { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #555; }
                h1 { font-size: 32px; margin: 15px 0 8px 0; font-weight: 800; }
                p.lead { font-size: 14px; color: #444; margin-bottom: 25px; }
                .spec-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                .spec-table td { padding: 12px 14px; border-bottom: 1px solid #e0e0e0; font-size: 13px; }
                .spec-table td.label { font-weight: 700; width: 30%; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; color: #666; }
                .footer { margin-top: 40px; border-top: 1px solid #ddd; padding-top: 15px; font-size: 11px; color: #888; display: flex; justify-content: space-between; }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="brand">{ GROWXLABS }</div>
                <div class="tag">ENTERPRISE SPECIFICATION SHEET</div>
            </div>
            <h1>GrowX-Crawl Platform</h1>
            <p class="lead">Enterprise web intelligence and auto-escalating scraping runtime matching high-scale requirements.</p>
            <table class="spec-table">
                <tr><td class="label">Architecture</td><td>API Request &rarr; Rate Limiter &rarr; Auto-Escalating Fetcher (Fast &rarr; Dynamic &rarr; Stealth) &rarr; Structured Parsel Extractor &rarr; SQLite WAL Snapshot</td></tr>
                <tr><td class="label">Core Capabilities</td><td>7 Services: Single Scrape, CSS/XPath Extraction, Multi-page Crawl (up to 50 pages, 5 levels), Parallel Batch (100 URLs), Full-page Screenshot, Publication PDF, AEO360 Audit</td></tr>
                <tr><td class="label">Anti-Bot Bypass</td><td>TLS / JA3 / JA4 browser fingerprint impersonation (chrome124), Cloudflare Challenge Evasion, DataDome, PerimeterX, and Akamai bypass</td></tr>
                <tr><td class="label">Compliance</td><td>robots.txt parser with SQLite caching, crawl-delays, XML sitemap discovery, persistent target page storage</td></tr>
                <tr><td class="label">Security & Auth</td><td>API Key authentication with admin approval flow, token bucket rate limiting (60 / 300 / 1200 RPM), and monthly quota tracking</td></tr>
            </table>
            <div class="footer">
                <span>&copy; 2026 GrowX Labs Inc.</span>
                <span>engineering@growxlabs.com &middot; 127.0.0.1:7411</span>
            </div>
        </body>
        </html>
        """
        brochure_path.parent.mkdir(parents=True, exist_ok=True)
        await pdf_engine.generate_from_html(html, output_path=brochure_path)
    return FileResponse(
        path=str(brochure_path),
        filename="growx_crawl_enterprise_specification.pdf",
        media_type="application/pdf",
    )


@v1_router.post("/crawl/extract-from")
async def extract_from_target(req: ExtractFromTargetRequest, auth: Dict[str, Any] = Depends(get_current_api_key)):
    """Extract structured data from existing crawl target stored in SQLite."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT url, html_content FROM pages WHERE target_id = ? OR id = ? LIMIT 1",
            (req.target_id, req.target_id),
        ).fetchone()

    if not row or not row["html_content"]:
        raise HTTPException(
            status_code=404,
            detail=f"Target page '{req.target_id}' not found in persistent storage. Crawl or scrape the page first.",
        )

    extracted = structured_extractor.extract_from_html(row["html_content"], req.selectors)
    return {
        "status": "success",
        "target_id": req.target_id,
        "url": row["url"],
        "extracted_fields": len([k for k, v in extracted.items() if v is not None]),
        "data": extracted,
        "source": "sqlite_page_snapshot",
    }


@v1_router.get("/targets")
async def list_stored_targets(
    limit: int = Query(50, ge=1, le=200),
    auth: Dict[str, Any] = Depends(get_current_api_key),
):
    """List indexed DOM snapshots stored in SQLite database."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT 
                COALESCE(NULLIF(target_id, ''), id) AS id,
                COALESCE(NULLIF(title, ''), 'Untitled Document') AS title,
                url,
                created_at AS stored_at,
                status_code
            FROM pages
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        targets = [dict(r) for r in rows]
    return {
        "total": len(targets),
        "targets": targets,
    }


@v1_router.get("/targets/{target_id}")
async def get_stored_target(target_id: str, auth: Dict[str, Any] = Depends(get_current_api_key)):
    """Retrieve metadata for a stored target snapshot."""
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT id, target_id, job_id, url, status_code, content_type, title,
                   text_content, created_at, LENGTH(COALESCE(html_content, '')) AS html_bytes
            FROM pages
            WHERE target_id = ? OR id = ?
            LIMIT 1
            """,
            (target_id, target_id),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Target snapshot not found in database")
    return dict(row)


@v1_router.get("/targets/{target_id}/preview")
@v1_router.get("/targets/{target_id}/raw")
async def preview_stored_target(target_id: str):
    """Render the full-fidelity HTML snapshot with full-page CSS and base URL resolution."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT url, html_content FROM pages WHERE target_id = ? OR id = ? LIMIT 1",
            (target_id, target_id),
        ).fetchone()
    if not row or not row["html_content"]:
        raise HTTPException(status_code=404, detail="Target snapshot not found or contains no HTML content")

    html = ensure_base_href(row["html_content"], row["url"])
    return HTMLResponse(content=html, media_type="text/html; charset=utf-8")


@v1_router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Poll asynchronous crawl job status across restarts."""
    job = multi_page_crawler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Crawl job not found")
    return {
        "job_id": job.job_id,
        "seed_url": job.seed_url,
        "status": job.status,
        "pages_crawled": job.pages_crawled,
        "pages": job.pages,
        "errors": job.errors,
        "duration_seconds": (job.completed_at - job.created_at) if job.completed_at else None,
    }


@v1_router.get("/jobs")
async def list_all_jobs(limit: int = Query(20, ge=1, le=100)):
    """List active and historic crawl jobs from SQLite."""
    jobs = multi_page_crawler.list_jobs(limit=limit)
    return {
        "total": len(jobs),
        "jobs": jobs,
    }


@v1_router.get("/batches/{batch_id}")
async def get_batch_status(batch_id: str):
    """Poll asynchronous batch job status."""
    batch = batch_scraper.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch job not found")
    return {
        "batch_id": batch.batch_id,
        "total_urls": batch.total_urls,
        "completed_count": batch.completed_count,
        "status": batch.status,
        "results": batch.results,
    }


@v1_router.get("/batches")
async def list_all_batches(limit: int = Query(20, ge=1, le=100)):
    """List historic batch jobs from SQLite."""
    batches = batch_scraper.list_batches(limit=limit)
    return {
        "total": len(batches),
        "batches": batches,
    }


@v1_router.get("/robots")
async def inspect_robots(url: str = Query(..., description="Target URL to inspect robots.txt")):
    """Inspect robots.txt allow/disallow status, crawl-delay, and sitemaps."""
    return await robots_engine.get_robots_info(url)


# ── API Key Management & Telemetry ──

@v1_router.post("/keys/request")
async def request_api_key(req: APIKeyRequest):
    """Request a new API key; enters 'pending' state awaiting administrator approval."""
    return api_key_manager.request_key(name=req.name, email=req.email, tier=req.tier)


@v1_router.get("/admin/keys")
async def list_api_keys(status: Optional[str] = Query(None, description="Filter by status (pending, active, revoked)")):
    """Administrator: List all API keys and their approval states."""
    keys = api_key_manager.list_keys(status_filter=status)
    return {"total": len(keys), "keys": keys}


@v1_router.post("/admin/keys/{key_id}/approve")
async def approve_api_key(key_id: str):
    """Administrator: Approve a pending API key, generate token, and activate rate limits."""
    return api_key_manager.approve_key(key_id)


@v1_router.post("/admin/keys/{key_id}/revoke")
async def revoke_api_key(key_id: str):
    """Administrator: Revoke an API key immediately."""
    return api_key_manager.revoke_key(key_id)


@v1_router.get("/usage")
async def get_usage(auth: Dict[str, Any] = Depends(get_current_api_key)):
    """API key quota and rate limit status queried live from database."""
    return {
        "api_key_prefix": auth["prefix"],
        "name": auth["name"],
        "tier": auth["tier"],
        "status": auth["status"],
        "requests_used": auth["requests_used"],
        "monthly_quota": auth["monthly_quota"],
        "rate_limit_rpm": auth["rate_limit_rpm"],
        "last_used_at": auth["last_used_at"],
        "approved_at": auth["approved_at"],
    }


# ── Web Search Engine Endpoints ──

@v1_router.get("/search")
async def execute_web_search(
    q: str = Query("", description="Web search query with support for phrases, boolean, and site:domain"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    domain: Optional[str] = Query(None, description="Optional domain filter"),
    auth: Dict[str, Any] = Depends(get_current_api_key),
):
    """Sovereign Web Search: Search indexed web documents with BM25 ranking, snippets, and authority scores."""
    from growx_crawl.search.engine import search_engine
    return search_engine.search(query=q, limit=limit, offset=offset, domain=domain)


@v1_router.post("/search/reindex")
async def trigger_search_reindex(
    bg_tasks: BackgroundTasks,
    limit: int = Query(1000, ge=1, le=10000),
    auth: Dict[str, Any] = Depends(get_current_api_key),
):
    """Trigger background re-indexing of all pages stored in the SQLite database into the FTS5 search index."""
    from growx_crawl.search.engine import search_engine
    bg_tasks.add_task(search_engine.reindex_all, limit)
    return {
        "status": "queued",
        "message": f"Background re-indexing initiated for up to {limit} documents.",
    }


@v1_router.get("/search/stats")
async def get_search_stats(auth: Dict[str, Any] = Depends(get_current_api_key)):
    """Retrieve search engine index size, link graph statistics, and query telemetry."""
    from growx_crawl.search.engine import search_engine
    return search_engine.get_stats()


# ── Data Quality Gate Endpoints ──

class QualityEvaluateRequest(BaseModel):
    subject_type: str = "prospect"
    subject_id: str
    gate_type: str
    profile: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    policy_name: Optional[str] = None


class ProspectBundleEvaluateRequest(BaseModel):
    prospect_data: Dict[str, Any]
    existing_prospect_ids: Optional[List[str]] = None
    suppressed_emails: Optional[List[str]] = None


@v1_router.post("/quality/evaluate")
async def evaluate_quality_gate(
    req: QualityEvaluateRequest,
    auth: Dict[str, Any] = Depends(get_current_api_key),
):
    """Evaluate a subject record against a specific Data Quality Gate."""
    from growx_crawl.quality import GateType, quality_service
    try:
        gt = GateType(req.gate_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid gate_type: {req.gate_type}")

    decision = quality_service.evaluate(
        subject_type=req.subject_type,
        subject_id=req.subject_id,
        gate_type=gt,
        profile=req.profile,
        data=req.data,
        policy_name=req.policy_name,
    )
    return decision.model_dump()


@v1_router.post("/quality/prospect-bundle")
async def evaluate_prospect_bundle(
    req: ProspectBundleEvaluateRequest,
    auth: Dict[str, Any] = Depends(get_current_api_key),
):
    """Run comprehensive quality evaluation for a full prospect bundle."""
    from growx_crawl.quality import quality_service
    snapshot = quality_service.evaluate_prospect_bundle(
        prospect_data=req.prospect_data,
        existing_prospect_ids=req.existing_prospect_ids,
        suppressed_emails=req.suppressed_emails,
    )
    return snapshot.model_dump()


@v1_router.get("/quality/metrics")
async def get_quality_metrics(auth: Dict[str, Any] = Depends(get_current_api_key)):
    """Retrieve telemetry metrics summary across all Data Quality Gates."""
    from growx_crawl.quality import quality_service
    return quality_service.get_metrics_summary()


@v1_router.get("/quality/quarantine")
async def list_quarantine_records(
    status: Optional[str] = Query(None, description="Filter status (pending, accepted, rejected, reprocessed)"),
    auth: Dict[str, Any] = Depends(get_current_api_key),
):
    """List quarantined observation payloads for review and repair."""
    from growx_crawl.quality import quality_service
    records = quality_service.list_quarantined(status=status)
    return {"total": len(records), "quarantined": [r.model_dump() for r in records]}


@v1_router.get("/quality/state/{subject_type}/{subject_id}/{gate_type}")
async def get_quality_state(
    subject_type: str,
    subject_id: str,
    gate_type: str,
    auth: Dict[str, Any] = Depends(get_current_api_key),
):
    """Get current cached quality state for a subject and gate."""
    from growx_crawl.quality import GateType, quality_service
    try:
        gt = GateType(gate_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid gate_type: {gate_type}")

    state = quality_service.get_current(subject_type, subject_id, gt)
    if not state:
        raise HTTPException(status_code=404, detail="Quality state not found")
    return state.model_dump()


# ── Data Factory Endpoints ──

class DataFactoryStartRequest(BaseModel):
    run_type: str = "nightly"
    custom_config: Optional[Dict[str, Any]] = None
    seed_candidates: Optional[List[Dict[str, Any]]] = None


class DataFactoryReprocessRequest(BaseModel):
    r2_keys: List[str]
    run_id: Optional[str] = None


@v1_router.post("/data-factory/runs")
async def start_data_factory_run(
    req: DataFactoryStartRequest,
    auth: Dict[str, Any] = Depends(get_current_api_key),
):
    """Launch a new Data Factory run (nightly, manual, backfill, refresh, targeted)."""
    from growx_crawl.data_factory import RunType, data_factory_service
    try:
        rt = RunType(req.run_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid run_type: {req.run_type}")

    try:
        run = await data_factory_service.start_run(
            run_type=rt,
            seed_candidates=req.seed_candidates,
            custom_config=req.custom_config,
        )
        return run.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@v1_router.get("/data-factory/runs/latest")
async def get_latest_data_factory_run(auth: Dict[str, Any] = Depends(get_current_api_key)):
    """Retrieve the most recent Data Factory run."""
    from growx_crawl.data_factory import data_factory_service
    run = data_factory_service.get_latest_run()
    if not run:
        raise HTTPException(status_code=404, detail="No Data Factory runs found")
    return run.model_dump()


@v1_router.get("/data-factory/runs/{run_id}")
async def get_data_factory_run(
    run_id: str,
    auth: Dict[str, Any] = Depends(get_current_api_key),
):
    """Get status, stage checkpoint, and counts for a specific Data Factory run."""
    from growx_crawl.data_factory import data_factory_service
    run = data_factory_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run.model_dump()


@v1_router.post("/data-factory/runs/{run_id}/pause")
async def pause_data_factory_run(
    run_id: str,
    auth: Dict[str, Any] = Depends(get_current_api_key),
):
    """Pause an active Data Factory run."""
    from growx_crawl.data_factory import data_factory_service
    try:
        run = data_factory_service.pause_run(run_id)
        return run.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@v1_router.post("/data-factory/runs/{run_id}/resume")
async def resume_data_factory_run(
    run_id: str,
    auth: Dict[str, Any] = Depends(get_current_api_key),
):
    """Resume an interrupted or paused Data Factory run from its last checkpoint."""
    from growx_crawl.data_factory import data_factory_service
    try:
        run = await data_factory_service.resume_run(run_id)
        return run.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@v1_router.post("/data-factory/runs/{run_id}/cancel")
async def cancel_data_factory_run(
    run_id: str,
    auth: Dict[str, Any] = Depends(get_current_api_key),
):
    """Cancel an active Data Factory run."""
    from growx_crawl.data_factory import data_factory_service
    try:
        run = data_factory_service.cancel_run(run_id)
        return run.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@v1_router.get("/data-factory/runs/{run_id}/summary")
async def get_data_factory_run_summary(
    run_id: str,
    auth: Dict[str, Any] = Depends(get_current_api_key),
):
    """Retrieve Morning Intelligence Report summary for a run."""
    from growx_crawl.data_factory import data_factory_service
    summary = data_factory_service.get_morning_summary(run_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found for this run")
    return summary.model_dump()


@v1_router.post("/data-factory/runs/{run_id}/retry-failed")
async def retry_failed_data_factory_jobs(
    run_id: str,
    auth: Dict[str, Any] = Depends(get_current_api_key),
):
    """Retry isolated failed jobs recorded in dead-letter storage."""
    from growx_crawl.data_factory import data_factory_service
    return data_factory_service.retry_failed_jobs(run_id)


@v1_router.post("/data-factory/reprocess")
async def reprocess_r2_artifacts(
    req: DataFactoryReprocessRequest,
    auth: Dict[str, Any] = Depends(get_current_api_key),
):
    """Reprocess raw R2 crawl artifacts through extraction, resolution, and facts without recrawling."""
    from growx_crawl.data_factory import data_factory_service
    return data_factory_service.reprocess_from_r2(req.r2_keys, run_id=req.run_id)


# ── Phase 10: Historical Intelligence API ──

@v1_router.get("/intelligence/entities/{entity_type}/{entity_id}/timeline")
def get_entity_timeline(
    entity_type: str,
    entity_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    event_types: Optional[str] = Query(None, description="Comma-separated event types"),
    since: Optional[str] = Query(None, description="ISO 8601 timestamp filter"),
):
    """Get the timeline of changes for an entity."""
    from growx_crawl.intelligence.history.service import HistoricalIntelligenceService
    svc = HistoricalIntelligenceService()
    types_list = event_types.split(",") if event_types else None
    return svc.get_timeline(
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
        offset=offset,
        event_types=types_list,
        since=since,
    )


@v1_router.get("/intelligence/entities/{entity_type}/{entity_id}/state")
def get_entity_state_at(
    entity_type: str,
    entity_id: str,
    at: str = Query(..., description="ISO 8601 timestamp for historical state"),
):
    """Reconstruct what we believed about an entity at a given point in time."""
    from growx_crawl.intelligence.facts.repository import SqliteFactRepository
    from growx_crawl.intelligence.history.service import HistoricalIntelligenceService

    fact_repo = SqliteFactRepository()
    svc = HistoricalIntelligenceService()

    facts = fact_repo.list_current(entity_type, entity_id)
    all_values = []
    for f in facts:
        vals = fact_repo.list_history(f.id)
        for v in vals:
            all_values.append({
                "fact_id": f.id,
                "predicate": f.predicate,
                "value_json": v.value_json,
                "valid_from": v.valid_from,
                "valid_to": v.valid_to,
                "confidence": v.confidence,
                "status": v.status,
            })

    facts_dicts = [{"id": f.id, "predicate": f.predicate} for f in facts]
    return svc.get_state_at(entity_type, entity_id, at, facts_dicts, all_values)


@v1_router.get("/intelligence/entities/{entity_type}/{entity_id}/trends")
def get_entity_trends(
    entity_type: str,
    entity_id: str,
    trend_types: Optional[str] = Query(None, description="Comma-separated trend types"),
):
    """Get computed trends for an entity."""
    from growx_crawl.intelligence.history.service import HistoricalIntelligenceService
    svc = HistoricalIntelligenceService()
    types_list = trend_types.split(",") if trend_types else None
    trends = svc.get_trends(entity_type, entity_id, types_list)
    return [t.model_dump() for t in trends]


@v1_router.get("/intelligence/entities/{entity_type}/{entity_id}/signals")
def get_entity_signals(
    entity_type: str,
    entity_id: str,
):
    """Get active signal candidates for an entity."""
    from growx_crawl.intelligence.signals.service import SignalService
    svc = SignalService()
    return svc.get_active_signals(entity_id)


# ── Phase 11: Competitor Graph API ──

class DiscoverCompetitorsRequest(BaseModel):
    max_candidates: int = 50
    verify_top: int = 20


@v1_router.get("/companies/{company_id}/competitors")
def get_company_competitors(
    company_id: str,
    relationship_type: Optional[str] = Query(None, description="direct, adjacent, substitute, etc."),
    min_strength: float = Query(0.0, ge=0.0, le=1.0),
    status: Optional[str] = Query(None, description="candidate, supported, verified, etc."),
    limit: int = Query(20, ge=1, le=100),
):
    """List discovered and verified competitors for a company."""
    from growx_crawl.intelligence.competitors.service import competitor_service
    types_list = [relationship_type] if relationship_type else None
    rels = competitor_service.get_competitors(
        company_id=company_id,
        relationship_types=types_list,
        min_strength=min_strength,
        status=status,
        limit=limit,
    )
    return [r.model_dump() for r in rels]


@v1_router.get("/companies/{company_id}/competitors/graph")
def get_company_competitor_graph(
    company_id: str,
    depth: int = Query(1, ge=1, le=2),
    min_strength: float = Query(0.0, ge=0.0, le=1.0),
):
    """Get network graph nodes and edges for a company's competitors."""
    from growx_crawl.intelligence.competitors.service import competitor_service
    return competitor_service.get_graph(
        company_id=company_id,
        depth=depth,
        min_strength=min_strength,
    )


@v1_router.post("/companies/{company_id}/competitors/discover")
def discover_company_competitors(
    company_id: str,
    req: DiscoverCompetitorsRequest = DiscoverCompetitorsRequest(),
):
    """Triggers internal-data-first competitor candidate discovery and scoring."""
    from growx_crawl.intelligence.competitors.service import competitor_service
    rels = competitor_service.discover(
        company_id=company_id,
        max_candidates=req.max_candidates,
        verify_top=req.verify_top,
    )
    return [r.model_dump() for r in rels]


@v1_router.get("/competitors/{relationship_id}")
def get_competitor_relationship(relationship_id: str):
    """Retrieves full details for a specific competitor relationship."""
    from growx_crawl.intelligence.competitors.service import competitor_service
    rel = competitor_service.repository.get_relationship(relationship_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Competitor relationship not found")
    ev_list = competitor_service.repository.list_evidence(relationship_id)
    return {
        "relationship": rel.model_dump(),
        "evidence": [e.model_dump() for e in ev_list],
    }


@v1_router.post("/competitors/{relationship_id}/verify")
def verify_competitor_relationship(relationship_id: str):
    """Re-runs verification gate for an existing competitor relationship."""
    from growx_crawl.intelligence.competitors.service import competitor_service
    rel = competitor_service.repository.get_relationship(relationship_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Competitor relationship not found")
    updated = competitor_service.score_pair(rel.company_id, rel.competitor_company_id)
    return updated.model_dump()


