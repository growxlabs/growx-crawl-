import asyncio
import traceback
from datetime import datetime, timezone
from typing import Callable, Optional
from growx_crawl.core.enums import JobStatus, TargetStatus
from growx_crawl.core.industry import IndustryProfileRegistry
from growx_crawl.core.location import LocationInfo, LocationPlanner, LocationRegistry
from growx_crawl.crawler import HttpCrawler, PageDiscoverer
from growx_crawl.dedupe import DeduplicationEngine
from growx_crawl.discovery import ProviderRegistry, SearchProvider, SeedFileDiscoveryProvider
from growx_crawl.events import CrawlEvent, CrawlEventBroadcaster
from growx_crawl.extractors import (
    AddressExtractor,
    CompanyExtractor,
    ContactExtractor,
    EmailExtractor,
    PhoneExtractor,
    SocialExtractor,
)
from growx_crawl.models import Company, CrawlJob, CrawlTarget, FetchedPage
from growx_crawl.normalization import Normalizer
from growx_crawl.scoring import LeadScorer
from growx_crawl.storage import (
    ErrorRepository,
    JobRepository,
    LeadRepository,
    TargetRepository,
    init_db,
)
from growx_crawl.workers import AsyncWorkerPool


class CrawlJobEngine:
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        init_db(db_path)
        self.job_repo = JobRepository(db_path)
        self.target_repo = TargetRepository(db_path)
        self.lead_repo = LeadRepository(db_path)
        self.error_repo = ErrorRepository(db_path)
        self.dedupe_engine = DeduplicationEngine(self.lead_repo)

    async def start_job(
        self,
        query: Optional[str] = None,
        limit: int = 100,
        target_leads: int = 50,
        workers: int = 10,
        depth: int = 2,
        location: Optional[str] = None,
        industry: Optional[str] = None,
        provider_type: str = "auto",
        seed_file: Optional[str] = None,
        scoring_profile: str = "general",
        discover_only: bool = False,
        campaign_id: Optional[str] = None,
        on_progress: Optional[Callable[[CrawlJob], None]] = None,
    ) -> CrawlJob:
        ind_profile = IndustryProfileRegistry.get_profile(industry or query or "general")
        loc_info = LocationRegistry.resolve_location(location or "Hyderabad")
        query_text = query or f"{ind_profile.name} {loc_info.city}"

        job = CrawlJob(
            query=query_text,
            industry=ind_profile.name,
            location=loc_info.to_display_string(),
            status=JobStatus.RUNNING,
            started_at=datetime.now(timezone.utc).isoformat(),
            configuration={
                "limit": limit,
                "target_leads": target_leads,
                "workers": workers,
                "depth": depth,
                "provider": provider_type,
                "seed_file": seed_file,
                "scoring_profile": scoring_profile,
                "discover_only": discover_only,
                "campaign_id": campaign_id,
            },
        )
        self.job_repo.create_job(job)

        # 1. Multi-Query & Multi-Provider Candidate Discovery Phase
        self.job_repo.update_job_status(job.id, JobStatus.RUNNING)
        CrawlEventBroadcaster.publish(CrawlEvent(event="job_started", job_id=job.id, data={"query": query_text, "industry": ind_profile.name, "location": loc_info.city}))
        CrawlEventBroadcaster.publish(CrawlEvent(event="job_progress", job_id=job.id, data={"status": "running", "discovered": 0, "processed": 0, "leads": 0, "failures": 0}))

        # Generate query variants
        query_variants = [query_text]
        for term in ind_profile.search_terms[:5]:
            var = f"{term} {loc_info.city}"
            if var not in query_variants:
                query_variants.append(var)

        candidates = []
        registry = ProviderRegistry(seed_file=seed_file)

        for q_var in query_variants:
            cands = await registry.discover_candidates(
                query=q_var,
                location=loc_info.city,
                industry=ind_profile.name,
                provider_type=provider_type,
                limit=limit,
                job_id=job.id,
                seed_file=seed_file,
            )
            candidates.extend(cands)
            current_job_check = self.job_repo.get_job(job.id)
            if current_job_check and current_job_check.lead_count >= target_leads:
                break

        # 2. Persist Candidates & Targets
        targets_to_add: List[CrawlTarget] = []
        scorer = LeadScorer(profile_name=scoring_profile)

        for cand in candidates:
            CrawlEventBroadcaster.publish(CrawlEvent(
                event="company_discovered",
                job_id=job.id,
                data={"company_name": cand.company_name, "source": cand.source, "location": cand.city or location}
            ))

            if cand.website:
                domain = Normalizer.normalize_domain(cand.website)
                targets_to_add.append(
                    CrawlTarget(
                        job_id=job.id,
                        url=cand.website,
                        domain=domain or "unknown.com",
                        source=cand.source,
                        depth=0,
                    )
                )

            # Persist company record directly (handling no-website prospects cleanly)
            company = Company(
                job_id=job.id,
                name=cand.company_name or "Unknown Company",
                normalized_name=Normalizer.clean_company_name(cand.company_name or "Unknown Company"),
                domain=cand.domain or "",
                website=cand.website or "",
                industry=industry or cand.category or "Jewellery",
                category=cand.category,
                address=cand.address,
                city=cand.city or location,
                state=cand.state,
                country=cand.country or "India",
                source=cand.source,
                source_url=cand.source_url or cand.website or "discovery",
                discovered_from=cand.discovered_from,
                query_variant=cand.query_variant,
                rating=cand.rating,
                review_count=cand.review_count,
                website_missing=cand.website_missing,
                phones=[Phone(company_id="", phone=cand.phone, normalized_phone=Normalizer.normalize_phone(cand.phone), raw_phone=cand.phone, source_url=cand.source_url or "discovery")] if cand.phone else [],
            )

            # Evaluate deduplication
            is_dup, dedupe_rec, canonical_id = self.dedupe_engine.evaluate(company)
            if is_dup and dedupe_rec and canonical_id:
                company.id = dedupe_rec.duplicate_company_id
                self.lead_repo.save_company(company)
                self.lead_repo.save_dedupe_record(dedupe_rec)
                self.job_repo.update_job_counters(job.id, duplicates=1)
            else:
                c_id = self.lead_repo.save_company(company)
                lead_candidate = scorer.score_lead(company, target_location=location)
                self.lead_repo.save_lead_candidate(lead_candidate)
                self.job_repo.update_job_counters(job.id, leads=1)
                CrawlEventBroadcaster.publish(CrawlEvent(
                    event="lead_qualified",
                    job_id=job.id,
                    data={"company_name": company.name, "score": lead_candidate.score, "priority": lead_candidate.priority.value}
                ))

        added_count = self.target_repo.add_targets(targets_to_add)
        self.job_repo.update_job_counters(job.id, discovered=len(candidates))
        job.discovered_count = len(candidates)

        current_job = self.job_repo.get_job(job.id) or job
        CrawlEventBroadcaster.publish(CrawlEvent(
            event="job_progress",
            job_id=job.id,
            data={"status": current_job.status.value, "discovered": current_job.discovered_count, "processed": current_job.processed_count, "leads": current_job.lead_count, "failures": current_job.failure_count}
        ))

        if on_progress:
            on_progress(job)

        if discover_only:
            finished_at = datetime.now(timezone.utc).isoformat()
            self.job_repo.update_job_status(job.id, JobStatus.COMPLETED, finished_at=finished_at)
            CrawlEventBroadcaster.publish(CrawlEvent(event="job_completed", job_id=job.id, data={"status": "completed"}))
            return self.job_repo.get_job(job.id) or job

        # 3. Crawl Websites if discover_only is False
        await self._process_job_targets(job, workers, depth, scoring_profile, on_progress)
        finished_at = datetime.now(timezone.utc).isoformat()
        self.job_repo.update_job_status(job.id, JobStatus.COMPLETED, finished_at=finished_at)
        CrawlEventBroadcaster.publish(CrawlEvent(event="job_completed", job_id=job.id, data={"status": "completed"}))
        return self.job_repo.get_job(job.id) or job

    async def resume_job(
        self,
        job_id: str,
        workers: int = 10,
        on_progress: Optional[Callable[[CrawlJob], None]] = None,
    ) -> CrawlJob:
        job = self.job_repo.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        self.job_repo.update_job_status(job_id, JobStatus.RUNNING)
        job.status = JobStatus.RUNNING

        depth = job.configuration.get("depth", 2)
        scoring_profile = job.configuration.get("scoring_profile", "jewellery")

        await self._process_job_targets(job, workers, depth, scoring_profile, on_progress)
        return self.job_repo.get_job(job_id) or job

    async def retry_failed_job(
        self,
        job_id: str,
        workers: int = 10,
        on_progress: Optional[Callable[[CrawlJob], None]] = None,
    ) -> CrawlJob:
        job = self.job_repo.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        reset_count = self.target_repo.reset_failed_targets(job_id)
        self.job_repo.update_job_status(job_id, JobStatus.RUNNING)
        job.status = JobStatus.RUNNING

        depth = job.configuration.get("depth", 2)
        scoring_profile = job.configuration.get("scoring_profile", "jewellery")

        await self._process_job_targets(job, workers, depth, scoring_profile, on_progress)
        return self.job_repo.get_job(job_id) or job

    async def _process_job_targets(
        self,
        job: CrawlJob,
        workers: int,
        max_depth: int,
        scoring_profile: str,
        on_progress: Optional[Callable[[CrawlJob], None]],
    ):
        crawler = HttpCrawler(timeout_seconds=12.0)
        company_extractor = CompanyExtractor()
        email_extractor = EmailExtractor()
        phone_extractor = PhoneExtractor()
        social_extractor = SocialExtractor()
        address_extractor = AddressExtractor()
        contact_extractor = ContactExtractor()
        scorer = LeadScorer(profile_name=scoring_profile)
        pool = AsyncWorkerPool(max_workers=workers)

        while not pool.is_cancelled:
            pending_targets = self.target_repo.get_pending_targets(job.id, limit=workers * 2)
            if not pending_targets:
                break

            async def process_target(target: CrawlTarget):
                if pool.is_cancelled:
                    return

                self.target_repo.update_target_status(
                    target.id,
                    TargetStatus.FETCHING,
                    started_at=datetime.now(timezone.utc).isoformat(),
                )

                try:
                    page = await crawler.fetch(target)
                    now_str = datetime.now(timezone.utc).isoformat()

                    if not page or not page.html_content:
                        self.target_repo.update_target_status(
                            target.id,
                            TargetStatus.FAILED,
                            error=target.last_error or "Empty page or fetch error",
                            completed_at=now_str,
                        )
                        self.error_repo.log_error(
                            job.id,
                            target.url,
                            "FETCH_ERROR",
                            target.last_error or "Failed to fetch page content",
                            target_id=target.id,
                        )
                        self.job_repo.update_job_counters(job.id, processed=1, failures=1)
                        CrawlEventBroadcaster.publish(CrawlEvent(
                            event="crawler_error",
                            job_id=job.id,
                            data={"url": target.url, "error": target.last_error or "Failed to fetch page content"}
                        ))
                        return

                    self.target_repo.update_target_status(
                        target.id, TargetStatus.PARSED, completed_at=now_str
                    )

                    # Subpage discovery at depth 0
                    if target.depth == 0:
                        subpages = PageDiscoverer.generate_seed_subpages(target, max_depth=max_depth)
                        added = self.target_repo.add_targets(subpages)
                        if added > 0:
                            self.job_repo.update_job_counters(job.id, discovered=added)

                    # Entity Extraction
                    comp_data = company_extractor.extract(page)
                    emails = email_extractor.extract(page)
                    phones = phone_extractor.extract(page)
                    socials = social_extractor.extract(page)
                    addr_data = address_extractor.extract(page)
                    contacts = contact_extractor.extract(page)

                    domain = comp_data.get("domain") or target.domain
                    company_name = comp_data.get("name") or Normalizer.clean_company_name(domain.split(".")[0].capitalize())

                    company = Company(
                        job_id=job.id,
                        name=company_name,
                        normalized_name=Normalizer.clean_company_name(company_name),
                        domain=domain,
                        website=target.url,
                        industry=job.industry or comp_data.get("industry") or "Jewellery",
                        description=comp_data.get("description"),
                        address=addr_data.get("address"),
                        city=addr_data.get("city") or job.location,
                        state=addr_data.get("state"),
                        country=addr_data.get("country") or "India",
                        source_url=target.url,
                        emails=emails,
                        phones=phones,
                        social_profiles=socials,
                        contacts=contacts,
                    )

                    # Deduplication
                    is_dup, dedupe_rec, canonical_id = self.dedupe_engine.evaluate(company)
                    if is_dup and dedupe_rec and canonical_id:
                        company.id = dedupe_rec.duplicate_company_id
                        self.lead_repo.save_company(company)
                        self.lead_repo.save_dedupe_record(dedupe_rec)
                        self.job_repo.update_job_counters(job.id, processed=1, duplicates=1)
                    else:
                        # Save new canonical company lead
                        company_id = self.lead_repo.save_company(company)

                        # Score Lead
                        lead_candidate = scorer.score_lead(company, target_location=job.location)
                        self.lead_repo.save_lead_candidate(lead_candidate)
                        self.job_repo.update_job_counters(job.id, processed=1, leads=1)
                        CrawlEventBroadcaster.publish(CrawlEvent(
                            event="lead_qualified",
                            job_id=job.id,
                            data={"company_name": company.name, "score": lead_candidate.score, "priority": lead_candidate.priority.value}
                        ))

                    CrawlEventBroadcaster.publish(CrawlEvent(
                        event="company_processed",
                        job_id=job.id,
                        data={"company_name": company_name, "url": target.url, "emails_count": len(emails), "phones_count": len(phones)}
                    ))

                    current_job = self.job_repo.get_job(job.id) or job
                    CrawlEventBroadcaster.publish(CrawlEvent(
                        event="job_progress",
                        job_id=job.id,
                        data={"status": current_job.status.value, "discovered": current_job.discovered_count, "processed": current_job.processed_count, "leads": current_job.lead_count, "failures": current_job.failure_count}
                    ))

                except Exception as e:
                    st = traceback.format_exc()
                    now_str = datetime.now(timezone.utc).isoformat()
                    self.target_repo.update_target_status(
                        target.id, TargetStatus.FAILED, error=str(e), completed_at=now_str
                    )
                    self.error_repo.log_error(
                        job.id, target.url, "PIPELINE_ERROR", str(e), target_id=target.id, stack_trace=st
                    )
                    self.job_repo.update_job_counters(job.id, processed=1, failures=1)

                if on_progress:
                    updated_job = self.job_repo.get_job(job.id)
                    if updated_job:
                        on_progress(updated_job)

            await pool.map(process_target, pending_targets)

        finished_at = datetime.now(timezone.utc).isoformat()
        if pool.is_cancelled:
            self.job_repo.update_job_status(job.id, JobStatus.PAUSED, finished_at=finished_at)
        else:
            self.job_repo.update_job_status(job.id, JobStatus.COMPLETED, finished_at=finished_at)
