import asyncio
import time
from pathlib import Path
from typing import Optional
import typer
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from growx_crawl import __version__
from growx_crawl.core.config import settings
from growx_crawl.enrichment.bde_brief import BDEBriefGenerator
from growx_crawl.exporters import CSVExporter, JSONExporter, XLSXExporter
from growx_crawl.normalization.normalizer import Normalizer
from growx_crawl.integrations import GrowXLabsClient
from growx_crawl.jobs import CrawlJobEngine
from growx_crawl.models import Company, CrawlJob
from growx_crawl.scoring.scorer import LeadScorer
from growx_crawl.storage import ErrorRepository, JobRepository, LeadRepository
from growx_crawl.utils import console, log_error, log_info, log_success, log_warning, render_table

app = typer.Typer(
    name="growx-crawl",
    help="GrowX Crawl - High-performance lead intelligence crawler, extraction, normalization, deduplication & scoring.",
    add_completion=False,
)

agent_app = typer.Typer(help="Autonomous GrowX Crawl AI Agent Runtime commands")
app.add_typer(agent_app, name="agent")


@agent_app.command("run")
def agent_run_command(
    prompt: str = typer.Argument(..., help="Natural language goal prompt (e.g. 'Find 100 jewellery prospects in Hyderabad')"),
    provider: Optional[str] = typer.Option(None, "--provider", help="Agent provider (openrouter|ollama)"),
    model: Optional[str] = typer.Option(None, "--model", help="Model ID"),
):
    """
    Run the autonomous target-seeking AI agent.
    """
    from growx_crawl.agent import AgentRuntime
    log_info(f"Initiating GrowX Crawl AI Agent for prompt: [bold yellow]'{prompt}'[/bold yellow]")
    runtime = AgentRuntime(provider=provider, model=model)
    res = runtime.execute_goal(prompt)
    log_success(f"Agent run [bold yellow]{res['run_id']}[/bold yellow] finished! Leads: [bold green]{res['leads']}[/bold green] | Export: [bold cyan]{res['export_file']}[/bold cyan]")


@agent_app.command("status")
def agent_status_command(run_id: str = typer.Argument(..., help="Agent Run ID to inspect")):
    """
    Inspect the progress, actions, and status of an agent run.
    """
    from growx_crawl.storage import AgentRunRepository
    repo = AgentRunRepository()
    run = repo.get_run(run_id)
    if not run:
        log_error(f"Agent run not found: {run_id}")
        return

    console.print(Panel.fit(
        f"[bold cyan]Run ID:[/bold cyan] {run['id']}\n"
        f"[bold cyan]Goal:[/bold cyan] {run['goal']}\n"
        f"[bold cyan]Status:[/bold cyan] [bold green]{run['status']}[/bold green]\n"
        f"Provider: {run['provider']} | Model: {run['model']}\n"
        f"Valid Leads: [bold green]{run['current_valid_leads']}[/bold green] / {run['target_leads']}\n"
        f"Last Action: {run['last_action'] or 'N/A'}",
        title="[bold green]AGENT RUN STATUS[/bold green]"
    ))


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-v", help="Show GrowX Crawl version and exit."
    ),
):
    if version:
        console.print(f"[bold cyan]GrowX Crawl[/bold cyan] v{__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        console.print("[bold cyan]GrowX Crawl CLI[/bold cyan]")
        console.print("Run [bold yellow]growx-crawl --help[/bold yellow] for commands.")


@app.command("crawl")
def crawl_command(
    query: Optional[str] = typer.Argument(None, help="Optional search query or industry (e.g. 'sheet metal fabricators Pune')"),
    industry: Optional[str] = typer.Option(None, "--industry", "-i", help="Target industry sector (e.g. jewellery, manufacturing, saas)"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Target city or location (e.g. Hyderabad, Mumbai)"),
    locations: Optional[str] = typer.Option(None, "--locations", help="Comma-separated multi-city list (e.g. Hyderabad,Vijayawada,Bengaluru)"),
    state: Optional[str] = typer.Option(None, "--state", help="Target state for state-wide crawl (e.g. Telangana)"),
    country: Optional[str] = typer.Option(None, "--country", help="Target country (e.g. India)"),
    top_cities: Optional[int] = typer.Option(None, "--top-cities", help="Crawl top N cities in country"),
    target_leads: int = typer.Option(50, "--target-leads", help="Target count of unique valid leads"),
    limit: int = typer.Option(100, "--limit", help="Discovery candidate limit per task"),
    workers: int = typer.Option(10, "--workers", "-w", help="Number of async worker tasks"),
    depth: int = typer.Option(2, "--depth", "-d", help="Max crawl depth"),
    provider: str = typer.Option("auto", "--provider", "-p", help="Provider (auto|maps|search|directory|seeds)"),
    seed_file: Optional[str] = typer.Option(None, "--seed-file", "-s", help="Optional CSV/TXT seed file path"),
    scoring_profile: str = typer.Option("general", "--scoring-profile", help="Scoring profile name"),
    discover_only: bool = typer.Option(False, "--discover-only", help="Run candidate discovery without crawling pages"),
):
    """
    Run multi-industry, multi-location lead discovery and structured web crawling.
    """
    import uuid
    from growx_crawl.core.location import LocationPlanner
    from growx_crawl.storage import CampaignRepository

    loc_tasks = LocationPlanner.plan_locations(
        location=location,
        locations=locations,
        state=state,
        country=country,
        top_cities=top_cities,
    )

    log_info(f"Targeting {len(loc_tasks)} location task(s) for industry: [bold green]{industry or query or 'general'}[/bold green] (Target Leads: {target_leads})")

    engine = CrawlJobEngine()
    camp_repo = CampaignRepository()
    camp_id = f"cmpg_{uuid.uuid4().hex[:12]}"
    camp_repo.create_campaign(camp_id, f"{industry or 'General'} Campaign", industry or "general", "multi_location", target_leads)

    for loc in loc_tasks:
        log_info(f"Starting discovery task for location: [bold yellow]{loc.to_display_string()}[/bold yellow]...")
        job = asyncio.run(engine.start_job(
            query=query,
            industry=industry,
            location=loc.city,
            limit=limit,
            target_leads=target_leads,
            workers=workers,
            depth=depth,
            provider_type=provider,
            seed_file=seed_file,
            scoring_profile=scoring_profile or industry or "general",
            discover_only=discover_only,
            campaign_id=camp_id,
        ))
        log_success(f"Task finished for {loc.city} | Job ID: [bold yellow]{job.id}[/bold yellow] | Discovered: [bold cyan]{job.discovered_count}[/bold cyan] | Valid Leads: [bold green]{job.lead_count}[/bold green]")


@app.command("discover")
def discover_command(
    query: Optional[str] = typer.Argument(None, help="Discovery query string"),
    limit: int = typer.Option(50, "--limit", "-l", help="Number of prospects to discover"),
    location: Optional[str] = typer.Option("Hyderabad", "--location", help="Location filter"),
    industry: Optional[str] = typer.Option("Jewellery", "--industry", help="Industry vertical filter"),
    provider: str = typer.Option("auto", "--provider", "-p", help="Provider mode: auto, maps, search, directory, seeds"),
    seed_file: Optional[str] = typer.Option(None, "--seed-file", "-s", help="Path to seed file"),
):
    """
    Discover company candidates without crawling website pages.
    """
    query_display = query or f"{industry or 'Jewellery'} stores {location or 'Hyderabad'}"
    console.print(Panel.fit(
        f"[bold cyan]GrowX Candidate Discovery Engine[/bold cyan]\n"
        f"Query: [bold yellow]{query_display}[/bold yellow]\n"
        f"Location: {location} | Industry: {industry} | Provider: {provider} | Limit: {limit}",
        title="[bold green]DISCOVERY INITIATED[/bold green]"
    ))

    engine = CrawlJobEngine()
    final_job = asyncio.run(
        engine.start_job(
            query=query,
            limit=limit,
            location=location,
            industry=industry,
            provider_type=provider,
            seed_file=seed_file,
            discover_only=True,
        )
    )

    log_success(f"Discovery job [bold yellow]{final_job.id}[/bold yellow] completed! Found [bold green]{final_job.discovered_count}[/bold green] candidates.")
    log_info(f"Use 'growx-crawl export {final_job.id} --stage discovery' to export discovery results.")


@app.command("providers")
def providers_command():
    """
    Display discovery provider health and configuration status.
    """
    from growx_crawl.discovery.registry import ProviderRegistry
    registry = ProviderRegistry()
    health_list = registry.get_provider_health()

    headers = ["Provider", "Status", "API Key Set", "Details"]
    rows = [
        [
            h.get("name"),
            h.get("status"),
            "YES" if h.get("api_key_set") else "NO / Fallback",
            str({k: v for k, v in h.items() if k not in ["name", "status", "api_key_set"]}),
        ]
        for h in health_list
    ]
    render_table("GrowX Crawl - Discovery Provider Status", headers, rows)


@app.command("jobs")
def list_jobs_command(limit: int = typer.Option(20, "--limit", "-l", help="Number of recent jobs to show")):
    """
    List recent crawl jobs and their status.
    """
    repo = JobRepository()
    jobs = repo.list_jobs(limit=limit)
    if not jobs:
        log_warning("No crawl jobs found in database.")
        return

    headers = ["Job ID", "Query", "Status", "Discovered", "Processed", "Leads", "Dups", "Failures", "Created At"]
    rows = [
        [
            j.id,
            j.query[:30],
            j.status.value,
            j.discovered_count,
            j.processed_count,
            j.lead_count,
            j.duplicate_count,
            j.failure_count,
            j.created_at[:19].replace("T", " "),
        ]
        for j in jobs
    ]
    render_table("GrowX Crawl - Recent Jobs", headers, rows)


@app.command("status")
def status_command(job_id: str = typer.Argument(..., help="Job ID to check")):
    """
    Check the status, progress counters, and push eligibility for a crawl job.
    """
    job_repo = JobRepository()
    lead_repo = LeadRepository()
    job = job_repo.get_job(job_id)
    if not job:
        log_error(f"Job not found: {job_id}")
        return

    push_counts = lead_repo.get_job_push_counters(job_id)

    console.print(Panel.fit(
        f"[bold cyan]Job ID:[/bold cyan] {job.id}\n"
        f"[bold cyan]Query:[/bold cyan] {job.query}\n"
        f"[bold cyan]Status:[/bold cyan] [bold green]{job.status.value}[/bold green]\n"
        f"Started: {job.started_at} | Finished: {job.finished_at or 'N/A'}\n"
        f"Discovered: {job.discovered_count} | Processed: {job.processed_count}\n"
        f"Valid Leads: [bold green]{job.lead_count}[/bold green] | Duplicates: {job.duplicate_count} | Failures: {job.failure_count}\n"
        f"[bold yellow]Approved locally:[/bold yellow] {push_counts['approved_locally']} | "
        f"[bold green]Push eligible:[/bold green] {push_counts['push_eligible']} | "
        f"[bold cyan]Submitted:[/bold cyan] {push_counts['submitted']}",
        title="[bold green]CRAWL JOB STATUS[/bold green]"
    ))


@app.command("resume")
def resume_job_command(
    job_id: str = typer.Argument(..., help="Job ID to resume"),
    workers: int = typer.Option(10, "--workers", "-w", help="Number of worker tasks"),
):
    """
    Resume an interrupted crawl job.
    """
    engine = CrawlJobEngine()
    final_job = asyncio.run(engine.resume_job(job_id, workers=workers))
    log_success(f"Job [bold yellow]{final_job.id}[/bold yellow] resume finished with status: [bold green]{final_job.status.value}[/bold green]")


@app.command("push")
def push_command(
    job_id: str = typer.Argument(..., help="Job ID to push approved leads for"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate and build payload without submitting"),
    preview: bool = typer.Option(False, "--preview", help="Show sample JSON payload preview"),
    batch_size: int = typer.Option(100, "--batch-size", help="Maximum leads per batch"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Optional path to write raw JSON payload"),
):
    """
    Validate and push locally approved lead candidates to GrowXLabs API.
    """
    from growx_crawl.integrations import GrowXLabsClient, GrowXLabsContactPayload, GrowXLabsLeadPayload, PayloadValidator

    lead_repo = LeadRepository()
    approved_records = lead_repo.get_push_eligible_leads(job_id)

    if not approved_records:
        log_warning(f"No locally approved leads found for job: {job_id}. Mark leads as 'approved' in dashboard first.")
        return

    # Convert records into integration DTOs
    dtos: List[GrowXLabsLeadPayload] = []
    for r in approved_records:
        company = Company(**r)
        brief = BDEBriefGenerator.generate_brief(company)
        primary_cnt = None
        if company.contacts:
            top_c = company.contacts[0]
            primary_cnt = GrowXLabsContactPayload(
                name=top_c.name,
                title=top_c.title,
                decision_maker_tier=top_c.decision_maker_tier,
                email=top_c.email,
                phone=top_c.phone,
                linkedin_url=top_c.linkedin_url,
            )

        dto = GrowXLabsLeadPayload(
            external_reference=company.id,
            company_name=company.name,
            industry=company.industry,
            category=company.category,
            website=company.website if not company.website_missing else None,
            domain=company.domain if not company.website_missing else None,
            address=company.address,
            city=company.city,
            state=company.state,
            country=company.country,
            phone=brief.primary_phone,
            email=brief.primary_email,
            whatsapp=brief.whatsapp,
            instagram=brief.instagram,
            linkedin=brief.linkedin,
            primary_contact=primary_cnt,
            products_services=brief.products_services,
            research_summary=brief.research_summary,
            lead_score=r.get("score", 0),
            priority=r.get("priority", "Low"),
            score_reasons=brief.score_reasons,
            source=company.source,
            source_url=company.source_url,
            collected_at=company.created_at,
        )
        dtos.append(dto)

    valid_dtos, invalid_dtos = PayloadValidator.validate_batch(dtos)

    batch_count = (len(valid_dtos) + batch_size - 1) // batch_size if valid_dtos else 1

    client = GrowXLabsClient()
    sample_env = client.build_envelope(job_id, 1, batch_count, valid_dtos[:batch_size])

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(sample_env.model_dump_json(indent=2))
        log_success(f"Exported integration payload to: [bold green]{out_path}[/bold green]")

    if dry_run:
        console.print(Panel.fit(
            f"[bold cyan]Dry Run Validation Summary[/bold cyan]\n"
            f"Approved Leads Found: {len(approved_records)}\n"
            f"Valid DTOs: [bold green]{len(valid_dtos)}[/bold green] | Invalid DTOs: [bold red]{len(invalid_dtos)}[/bold red]\n"
            f"Estimated Batches: [bold yellow]{batch_count}[/bold yellow] (Batch Size: {batch_size})",
            title="[bold green]GROWXLABS PUSH DRY RUN[/bold green]"
        ))

        if preview and valid_dtos:
            console.print("\n[bold yellow]Sample Integration Payload Preview (Envelope Schema v1):[/bold yellow]")
            console.print(sample_env.model_dump_json(indent=2)[:1000] + "\n...")
        return

    if not client.is_configured():
        log_error("GrowXLabs integration is not configured. Set GROWXLABS_API_BASE_URL and GROWXLABS_INGESTION_TOKEN.")
        log_info("Use 'growx-crawl push <job-id> --dry-run' to validate payloads offline.")
        return

    # Submit live batches
    submitted_count = 0
    for idx in range(0, len(valid_dtos), batch_size):
        batch = valid_dtos[idx : idx + batch_size]
        env = client.build_envelope(job_id, (idx // batch_size) + 1, batch_count, batch)
        res = client.submit_batch(env)
        if res.get("success"):
            submitted_count += len(batch)
            lead_repo.save_push_history(job_id, f"Batch {env.batch_index}/{batch_count}", "submitted", "OK")
        else:
            lead_repo.save_push_history(job_id, f"Batch {env.batch_index}/{batch_count}", "failed", res.get("error", ""))
            log_error(f"Batch {env.batch_index} failed: {res.get('error')}")

    log_success(f"Successfully pushed {submitted_count}/{len(valid_dtos)} leads to GrowXLabs!")
    engine = CrawlJobEngine()
    final_job = asyncio.run(engine.resume_job(job_id, workers=workers))
    log_success(f"Job [bold yellow]{final_job.id}[/bold yellow] resume finished with status: [bold green]{final_job.status.value}[/bold green]")


@app.command("retry")
def retry_job_command(
    job_id: str = typer.Argument(..., help="Job ID to retry failed targets for"),
    workers: int = typer.Option(10, "--workers", "-w", help="Number of worker tasks"),
):
    """
    Retry failed targets for a specific crawl job.
    """
    log_info(f"Retrying failed targets for job: {job_id}")
    engine = CrawlJobEngine()
    final_job = asyncio.run(engine.retry_failed_job(job_id, workers=workers))
    log_success(f"Job [bold yellow]{final_job.id}[/bold yellow] retry finished with status: [bold green]{final_job.status.value}[/bold green]")


@app.command("enrich")
def enrich_command(
    job_id: Optional[str] = typer.Argument(None, help="Job ID to enrich"),
    profile: str = typer.Option("jewellery", "--profile", "-p", help="Enrichment profile name"),
    url: Optional[str] = typer.Option(None, "--url", help="Single URL to debug and enrich"),
):
    """
    Re-run deep enrichment and BDE brief generation on a job or single URL.
    """
    repo = LeadRepository()
    if url:
        log_info(f"Enriching single website URL: {url}")
        domain = Normalizer.normalize_domain(url)
        comp = Company(job_id="job_debug", name=domain.split(".")[0].capitalize(), normalized_name=domain.split(".")[0].lower(), domain=domain, website=url, source_url=url)
        brief = BDEBriefGenerator.generate_brief(comp)
        console.print(Panel.fit(
            f"[bold yellow]Company:[/bold yellow] {brief.company_name}\n"
            f"[bold yellow]Website:[/bold yellow] {brief.website}\n"
            f"[bold yellow]Research Summary:[/bold yellow] {brief.research_summary}\n"
            f"Flags: {brief.prospect_flags}",
            title="[bold green]SINGLE URL ENRICHED[/bold green]"
        ))
        return

    if not job_id:
        log_error("Please specify a Job ID or --url to enrich.")
        return

    leads = repo.get_job_lead_candidates(job_id)
    if not leads:
        log_error(f"No leads found for job: {job_id}")
        return

    scorer = LeadScorer(profile_name=profile)
    for l in leads:
        company = Company(**l)
        cand = scorer.score_lead(company)
        repo.save_lead_candidate(cand)

    log_success(f"Enriched {len(leads)} leads for job [bold yellow]{job_id}[/bold yellow] using profile [bold cyan]{profile}[/bold cyan]!")


@app.command("quality")
def quality_command(job_id: str = typer.Argument(..., help="Job ID to inspect quality for")):
    """
    Display a Data Quality & Completeness Report for a job.
    """
    repo = LeadRepository()
    leads = repo.get_job_lead_candidates(job_id)
    if not leads:
        log_error(f"No leads found for job: {job_id}")
        return

    total = len(leads)
    with_phone = sum(1 for l in leads if l.get("phones"))
    with_email = sum(1 for l in leads if l.get("emails"))
    with_ig = sum(1 for l in leads if any(s.get("platform") == "instagram" for s in l.get("social_profiles", [])))
    with_dm = sum(1 for l in leads if l.get("contacts"))
    no_website = sum(1 for l in leads if l.get("website_missing"))
    high_priority = sum(1 for l in leads if l.get("priority") == "High")
    medium_priority = sum(1 for l in leads if l.get("priority") == "Medium")

    headers = ["Metric", "Count", "Percentage"]
    rows = [
        ["Total Prospects", total, "100%"],
        ["High Priority Leads", high_priority, f"{int((high_priority/total)*100)}%"],
        ["Medium Priority Leads", medium_priority, f"{int((medium_priority/total)*100)}%"],
        ["With Public Phone", with_phone, f"{int((with_phone/total)*100)}%"],
        ["With Public Email", with_email, f"{int((with_email/total)*100)}%"],
        ["With Instagram", with_ig, f"{int((with_ig/total)*100)}%"],
        ["With Decision Maker", with_dm, f"{int((with_dm/total)*100)}%"],
        ["No Website (Directory/Maps)", no_website, f"{int((no_website/total)*100)}%"],
    ]
    render_table(f"Data Quality Report - Job {job_id}", headers, rows)


@app.command("export")
def export_command(
    job_id: str = typer.Argument(..., help="Job ID to export"),
    format_type: str = typer.Option("xlsx", "--format", "-f", help="Format: xlsx, csv, json, jsonl"),
    stage: str = typer.Option("all", "--stage", help="Stage: all, discovery"),
    priority: Optional[str] = typer.Option(None, "--priority", help="Filter by priority: high, medium, low"),
    min_score: Optional[int] = typer.Option(None, "--min-score", help="Filter by minimum lead score"),
    has_phone: bool = typer.Option(False, "--has-phone", help="Filter leads with public phone"),
    has_decision_maker: bool = typer.Option(False, "--has-decision-maker", help="Filter leads with identified decision maker"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Custom output file path"),
):
    """
    Export collected leads for a job to XLSX, CSV, or JSON format.
    """
    out_path = output or f"exports/{job_id}_{stage}_leads.{format_type}"
    if format_type.lower() == "xlsx":
        exporter = XLSXExporter()
        res = exporter.export_job(job_id, out_path, stage=stage)
    elif format_type.lower() == "csv":
        exporter = CSVExporter()
        res = exporter.export_job(job_id, out_path)
    else:
        exporter = JSONExporter()
        res = exporter.export_job(job_id, out_path, format_type=format_type)

    log_success(f"Exported job {job_id} leads ({format_type.upper()}) to: [bold green]{res}[/bold green]")


@app.command("dashboard")
def dashboard_command(
    port: int = typer.Option(7411, "--port", "-p", help="Port to bind dashboard server"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host binding (defaults to 127.0.0.1)"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open default web browser"),
):
    """
    Launch the local Lead Intelligence Dashboard web application.
    """
    import uvicorn
    url = f"http://{host}:{port}"
    console.print(Panel.fit(
        f"[bold cyan]GrowX Crawl - Local Lead Intelligence Dashboard[/bold cyan]\n"
        f"Server running at: [bold green]{url}[/bold green]\n"
        f"Bound to: [bold yellow]{host}[/bold yellow] | Port: [bold yellow]{port}[/bold yellow]",
        title="[bold green]DASHBOARD ACTIVE[/bold green]"
    ))

    if open_browser:
        import webbrowser
        webbrowser.open(url)

    uvicorn.run("growx_crawl.web.app:app", host=host, port=port, log_level="info")


@app.command("review")
def review_command(
    port: int = typer.Option(7411, "--port", "-p", help="Port to bind dashboard server"),
):
    """
    Alias for 'growx-crawl dashboard'. Open local review interface.
    """
    dashboard_command(port=port, host="127.0.0.1", open_browser=True)


@app.command("config")
def config_command():
    """
    View active configuration settings.
    """
    headers = ["Setting", "Value"]
    rows = [
        ["Database Path", settings.db_path],
        ["Default Workers", settings.workers],
        ["Max Depth", settings.max_depth],
        ["Max Pages per Domain", settings.max_pages_per_domain],
        ["Timeout (s)", settings.timeout_seconds],
        ["Requests/sec", settings.requests_per_second],
        ["Scoring Profile", settings.scoring_profile],
        ["GrowXLabs API Base URL", settings.growxlabs_api_base_url],
    ]
    render_table("GrowX Crawl Configuration", headers, rows)


@app.command("push")
def push_command(
    job_id: str = typer.Argument(..., help="Job ID to push approved leads for"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate and build payload without submitting"),
    preview: bool = typer.Option(False, "--preview", help="Show sample JSON payload preview"),
    batch_size: int = typer.Option(100, "--batch-size", help="Maximum leads per batch"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Optional path to write raw JSON payload"),
):
    """
    Validate and push locally approved lead candidates to GrowXLabs API.
    """
    from growx_crawl.integrations import GrowXLabsClient, GrowXLabsContactPayload, GrowXLabsLeadPayload, PayloadValidator

    lead_repo = LeadRepository()
    approved_records = lead_repo.get_push_eligible_leads(job_id)

    if not approved_records:
        log_warning(f"No locally approved leads found for job: {job_id}. Mark leads as 'approved' in dashboard first.")
        return

    # Convert records into integration DTOs
    dtos: List[GrowXLabsLeadPayload] = []
    for r in approved_records:
        company = Company(**r)
        brief = BDEBriefGenerator.generate_brief(company)
        primary_cnt = None
        if company.contacts:
            top_c = company.contacts[0]
            primary_cnt = GrowXLabsContactPayload(
                name=top_c.name,
                title=top_c.title,
                decision_maker_tier=top_c.decision_maker_tier,
                email=top_c.email,
                phone=top_c.phone,
                linkedin_url=top_c.linkedin_url,
            )

        dto = GrowXLabsLeadPayload(
            external_reference=company.id,
            company_name=company.name,
            industry=company.industry,
            category=company.category,
            website=company.website if not company.website_missing else None,
            domain=company.domain if not company.website_missing else None,
            address=company.address,
            city=company.city,
            state=company.state,
            country=company.country,
            phone=brief.primary_phone,
            email=brief.primary_email,
            whatsapp=brief.whatsapp,
            instagram=brief.instagram,
            linkedin=brief.linkedin,
            primary_contact=primary_cnt,
            products_services=brief.products_services,
            research_summary=brief.research_summary,
            lead_score=r.get("score", 0),
            priority=r.get("priority", "Low"),
            score_reasons=brief.score_reasons,
            source=company.source,
            source_url=company.source_url,
            collected_at=company.created_at,
        )
        dtos.append(dto)

    valid_dtos, invalid_dtos = PayloadValidator.validate_batch(dtos)

    batch_count = (len(valid_dtos) + batch_size - 1) // batch_size if valid_dtos else 1

    client = GrowXLabsClient()
    sample_env = client.build_envelope(job_id, 1, batch_count, valid_dtos[:batch_size])

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(sample_env.model_dump_json(indent=2))
        log_success(f"Exported integration payload to: [bold green]{out_path}[/bold green]")

    if dry_run:
        console.print(Panel.fit(
            f"[bold cyan]Dry Run Validation Summary[/bold cyan]\n"
            f"Approved Leads Found: {len(approved_records)}\n"
            f"Valid DTOs: [bold green]{len(valid_dtos)}[/bold green] | Invalid DTOs: [bold red]{len(invalid_dtos)}[/bold red]\n"
            f"Estimated Batches: [bold yellow]{batch_count}[/bold yellow] (Batch Size: {batch_size})",
            title="[bold green]GROWXLABS PUSH DRY RUN[/bold green]"
        ))

        if preview and valid_dtos:
            console.print("\n[bold yellow]Sample Integration Payload Preview (Envelope Schema v1):[/bold yellow]")
            console.print(sample_env.model_dump_json(indent=2)[:1000] + "\n...")
        return

    if not client.is_configured():
        log_error("GrowXLabs integration is not configured. Set GROWXLABS_API_BASE_URL and GROWXLABS_INGESTION_TOKEN.")
        log_info("Use 'growx-crawl push <job-id> --dry-run' to validate payloads offline.")
        return

    # Submit live batches
    submitted_count = 0
    for idx in range(0, len(valid_dtos), batch_size):
        batch = valid_dtos[idx : idx + batch_size]
        env = client.build_envelope(job_id, (idx // batch_size) + 1, batch_count, batch)
        res = client.submit_batch(env)
        if res.get("success"):
            submitted_count += len(batch)
            lead_repo.save_push_history(job_id, f"Batch {env.batch_index}/{batch_count}", "submitted", "OK")
        else:
            lead_repo.save_push_history(job_id, f"Batch {env.batch_index}/{batch_count}", "failed", res.get("error", ""))
            log_error(f"Batch {env.batch_index} failed: {res.get('error')}")

    log_success(f"Successfully pushed {submitted_count}/{len(valid_dtos)} leads to GrowXLabs!")


if __name__ == "__main__":
    app()
