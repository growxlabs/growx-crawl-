import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from growx_crawl.core.enums import JobStatus, MatchDecision, PriorityLevel, TargetStatus
from growx_crawl.models import (
    Company,
    Contact,
    CrawlJob,
    CrawlTarget,
    DedupeRecord,
    Email,
    FetchedPage,
    LeadCandidate,
    Location,
    ObservedFact,
    Phone,
    SocialProfile,
)
from growx_crawl.storage.db import get_db


class JobRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def create_job(self, job: CrawlJob) -> CrawlJob:
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO crawl_jobs (
                    id, query, industry, location, status, started_at, finished_at,
                    discovered_count, processed_count, lead_count, duplicate_count,
                    failure_count, configuration, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.query,
                    job.industry,
                    job.location,
                    job.status.value,
                    job.started_at,
                    job.finished_at,
                    job.discovered_count,
                    job.processed_count,
                    job.lead_count,
                    job.duplicate_count,
                    job.failure_count,
                    json.dumps(job.configuration),
                    job.created_at,
                ),
            )
        return job

    def get_job(self, job_id: str) -> Optional[CrawlJob]:
        with get_db(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM crawl_jobs WHERE id = ?", (job_id,)
            ).fetchone()
            if not row:
                return None
            return CrawlJob(
                id=row["id"],
                query=row["query"],
                industry=row["industry"],
                location=row["location"],
                status=JobStatus(row["status"]),
                started_at=row["started_at"],
                finished_at=row["finished_at"],
                discovered_count=row["discovered_count"],
                processed_count=row["processed_count"],
                lead_count=row["lead_count"],
                duplicate_count=row["duplicate_count"],
                failure_count=row["failure_count"],
                configuration=json.loads(row["configuration"] or "{}"),
                created_at=row["created_at"],
            )

    def list_jobs(self, limit: int = 50) -> List[CrawlJob]:
        with get_db(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM crawl_jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [
                CrawlJob(
                    id=row["id"],
                    query=row["query"],
                    industry=row["industry"],
                    location=row["location"],
                    status=JobStatus(row["status"]),
                    started_at=row["started_at"],
                    finished_at=row["finished_at"],
                    discovered_count=row["discovered_count"],
                    processed_count=row["processed_count"],
                    lead_count=row["lead_count"],
                    duplicate_count=row["duplicate_count"],
                    failure_count=row["failure_count"],
                    configuration=json.loads(row["configuration"] or "{}"),
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    def update_job_status(self, job_id: str, status: JobStatus, finished_at: Optional[str] = None):
        with get_db(self.db_path) as conn:
            if finished_at:
                conn.execute(
                    "UPDATE crawl_jobs SET status = ?, finished_at = ? WHERE id = ?",
                    (status.value, finished_at, job_id),
                )
            else:
                conn.execute(
                    "UPDATE crawl_jobs SET status = ? WHERE id = ?",
                    (status.value, job_id),
                )

    def update_job_counters(
        self,
        job_id: str,
        discovered: int = 0,
        processed: int = 0,
        leads: int = 0,
        duplicates: int = 0,
        failures: int = 0,
    ):
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                UPDATE crawl_jobs SET
                    discovered_count = discovered_count + ?,
                    processed_count = processed_count + ?,
                    lead_count = lead_count + ?,
                    duplicate_count = duplicate_count + ?,
                    failure_count = failure_count + ?
                WHERE id = ?
                """,
                (discovered, processed, leads, duplicates, failures, job_id),
            )


class TargetRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def add_targets(self, targets: List[CrawlTarget]) -> int:
        if not targets:
            return 0
        added = 0
        with get_db(self.db_path) as conn:
            for tgt in targets:
                # Check for existing target with same URL in job
                existing = conn.execute(
                    "SELECT id FROM crawl_targets WHERE job_id = ? AND url = ?",
                    (tgt.job_id, tgt.url),
                ).fetchone()
                if not existing:
                    conn.execute(
                        """
                        INSERT INTO crawl_targets (
                            id, job_id, url, domain, source, status, depth,
                            retry_count, last_error, discovered_at, started_at, completed_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            tgt.id,
                            tgt.job_id,
                            tgt.url,
                            tgt.domain,
                            tgt.source,
                            tgt.status.value,
                            tgt.depth,
                            tgt.retry_count,
                            tgt.last_error,
                            tgt.discovered_at,
                            tgt.started_at,
                            tgt.completed_at,
                        ),
                    )
                    added += 1
        return added

    def get_pending_targets(self, job_id: str, limit: int = 50) -> List[CrawlTarget]:
        with get_db(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM crawl_targets 
                WHERE job_id = ? AND status IN ('queued', 'fetching')
                ORDER BY depth ASC, discovered_at ASC
                LIMIT ?
                """,
                (job_id, limit),
            ).fetchall()
            return [self._row_to_target(row) for row in rows]

    def get_failed_targets(self, job_id: str) -> List[CrawlTarget]:
        with get_db(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM crawl_targets WHERE job_id = ? AND status = 'failed'",
                (job_id,),
            ).fetchall()
            return [self._row_to_target(row) for row in rows]

    def update_target_status(
        self,
        target_id: str,
        status: TargetStatus,
        error: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
    ):
        with get_db(self.db_path) as conn:
            sql = "UPDATE crawl_targets SET status = ?"
            params: list = [status.value]
            if error is not None:
                sql += ", last_error = ?, retry_count = retry_count + 1"
                params.append(error)
            if started_at is not None:
                sql += ", started_at = ?"
                params.append(started_at)
            if completed_at is not None:
                sql += ", completed_at = ?"
                params.append(completed_at)
            sql += " WHERE id = ?"
            params.append(target_id)
            conn.execute(sql, params)

    def reset_failed_targets(self, job_id: str) -> int:
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE crawl_targets SET status = 'queued', last_error = NULL WHERE job_id = ? AND status = 'failed'",
                (job_id,),
            )
            return cursor.rowcount

    def _row_to_target(self, row: sqlite3.Row) -> CrawlTarget:
        return CrawlTarget(
            id=row["id"],
            job_id=row["job_id"],
            url=row["url"],
            domain=row["domain"],
            source=row["source"],
            status=TargetStatus(row["status"]),
            depth=row["depth"],
            retry_count=row["retry_count"],
            last_error=row["last_error"],
            discovered_at=row["discovered_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
        )


class LeadRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def save_company(self, company: Company) -> str:
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO companies (
                    id, job_id, name, normalized_name, domain, website, industry,
                    category, description, address, city, state, country, source,
                    source_url, confidence, discovered_from, query_variant, rating,
                    review_count, website_missing, review_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    company.id,
                    company.job_id,
                    company.name,
                    company.normalized_name,
                    company.domain,
                    company.website,
                    company.industry,
                    company.category,
                    company.description,
                    company.address,
                    company.city,
                    company.state,
                    company.country,
                    company.source,
                    company.source_url,
                    company.confidence,
                    json.dumps(company.discovered_from),
                    company.query_variant,
                    company.rating,
                    company.review_count,
                    int(company.website_missing),
                    company.review_status,
                    company.created_at,
                    company.updated_at,
                ),
            )

            # Save child entities
            for eml in company.emails:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO emails (id, company_id, email, normalized_email, is_generic, source_url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (eml.id, company.id, eml.email, eml.normalized_email, int(eml.is_generic), eml.source_url, eml.created_at),
                )
            for phn in company.phones:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO phones (id, company_id, phone, normalized_phone, raw_phone, country_code, source_url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (phn.id, company.id, phn.phone, phn.normalized_phone, phn.raw_phone, phn.country_code, phn.source_url, phn.created_at),
                )
            for soc in company.social_profiles:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO social_profiles (id, company_id, platform, url, normalized_url, handle, source_url, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (soc.id, company.id, soc.platform, soc.url, soc.normalized_url, soc.handle, soc.source_url, soc.created_at),
                )
            for cnt in company.contacts:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO contacts (id, company_id, job_id, name, title, email, phone, linkedin_url, source_url, confidence, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (cnt.id, company.id, company.job_id, cnt.name, cnt.title, cnt.email, cnt.phone, cnt.linkedin_url, cnt.source_url, cnt.confidence, cnt.created_at),
                )
        return company.id

    def save_lead_candidate(self, candidate: LeadCandidate):
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO lead_candidates (
                    id, company_id, job_id, score, priority, score_reasons, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate.id,
                    candidate.company_id,
                    candidate.job_id,
                    candidate.score,
                    candidate.priority.value if hasattr(candidate.priority, 'value') else str(candidate.priority),
                    json.dumps(candidate.score_reasons),
                    candidate.status,
                    candidate.created_at,
                ),
            )

    def save_dedupe_record(self, record: DedupeRecord):
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO dedupe_records (
                    id, canonical_company_id, duplicate_company_id, match_signals,
                    confidence, decision, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.canonical_company_id,
                    record.duplicate_company_id,
                    json.dumps(record.match_signals),
                    record.confidence,
                    record.decision.value if hasattr(record.decision, 'value') else str(record.decision),
                    record.created_at,
                ),
            )

    def find_company_by_domain(self, domain: str) -> Optional[Company]:
        with get_db(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM companies WHERE domain = ? ORDER BY created_at ASC LIMIT 1",
                (domain,),
            ).fetchone()
            if not row:
                return None
            return self._hydrate_company(conn, row)

    def list_job_companies(self, job_id: str) -> List[Company]:
        with get_db(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM companies WHERE job_id = ? ORDER BY created_at ASC",
                (job_id,),
            ).fetchall()
            return [self._hydrate_company(conn, row) for row in rows]

    def get_job_lead_candidates(self, job_id: str) -> List[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT c.*, lc.score, lc.priority, lc.score_reasons, lc.id as lead_id
                FROM companies c
                JOIN lead_candidates lc ON c.id = lc.company_id
                WHERE c.job_id = ?
                ORDER BY lc.score DESC
                """,
                (job_id,),
            ).fetchall()
            results = []
            for r in rows:
                company = self._hydrate_company(conn, r)
                d = company.model_dump()
                d["score"] = r["score"]
                d["priority"] = r["priority"]
                d["score_reasons"] = json.loads(r["score_reasons"] or "[]")
                results.append(d)
            return results

    def save_location(self, location: Location):
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO locations (
                    id, company_id, name, address, city, state, country, phone,
                    source_url, is_primary, confidence, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    location.id,
                    location.company_id,
                    location.name,
                    location.address,
                    location.city,
                    location.state,
                    location.country,
                    location.phone,
                    location.source_url,
                    int(location.is_primary),
                    location.confidence,
                    location.created_at,
                ),
            )

    def save_observed_fact(self, fact: ObservedFact):
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO observed_facts (
                    id, company_id, key, value, source_url, confidence, extraction_type, observed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fact.id,
                    fact.company_id,
                    fact.key,
                    json.dumps(fact.value) if not isinstance(fact.value, str) else fact.value,
                    fact.source_url,
                    fact.confidence,
                    fact.extraction_type,
                    fact.observed_at,
                ),
            )

    def get_job_dedupe_records(self, job_id: str) -> List[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT d.*, c1.name as canonical_name, c2.name as duplicate_name
                FROM dedupe_records d
                JOIN companies c1 ON d.canonical_company_id = c1.id
                JOIN companies c2 ON d.duplicate_company_id = c2.id
                WHERE c1.job_id = ?
                """,
                (job_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def update_company_review_status(self, company_id: str, status: str):
        with get_db(self.db_path) as conn:
            conn.execute("UPDATE companies SET review_status = ? WHERE id = ?", (status, company_id))

    def bulk_update_review_status(self, company_ids: List[str], status: str):
        with get_db(self.db_path) as conn:
            conn.executemany("UPDATE companies SET review_status = ? WHERE id = ?", [(status, cid) for cid in company_ids])

    def get_dashboard_overview(self) -> Dict[str, Any]:
        with get_db(self.db_path) as conn:
            total_jobs = conn.execute("SELECT COUNT(*) FROM crawl_jobs").fetchone()[0]
            active_jobs = conn.execute("SELECT COUNT(*) FROM crawl_jobs WHERE status = 'running'").fetchone()[0]
            total_companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
            total_leads = conn.execute("SELECT COUNT(*) FROM lead_candidates").fetchone()[0]
            high_priority = conn.execute("SELECT COUNT(*) FROM lead_candidates WHERE priority = 'High'").fetchone()[0]
            pending_review = conn.execute("SELECT COUNT(*) FROM companies WHERE review_status = 'pending'").fetchone()[0]
            approved_leads = conn.execute("SELECT COUNT(*) FROM companies WHERE review_status = 'approved'").fetchone()[0]
            total_errors = conn.execute("SELECT COUNT(*) FROM crawl_errors").fetchone()[0]

            return {
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "total_companies": total_companies,
                "total_leads": total_leads,
                "high_priority_leads": high_priority,
                "pending_review": pending_review,
                "approved_leads": approved_leads,
                "total_errors": total_errors,
            }

    def get_job_evidence(self, job_id: str) -> List[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT f.*, c.name as company_name
                FROM observed_facts f
                JOIN companies c ON f.company_id = c.id
                WHERE c.job_id = ?
                ORDER BY f.observed_at DESC
                """,
                (job_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_push_eligible_leads(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Returns ONLY locally approved lead candidates for the specified job.
        Strictly excludes pending, rejected, or needs_review candidates.
        """
        with get_db(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT c.*, lc.score, lc.priority, lc.score_reasons
                FROM companies c
                JOIN lead_candidates lc ON c.id = lc.company_id
                WHERE c.job_id = ? AND c.review_status = 'approved'
                ORDER BY lc.score DESC
                """,
                (job_id,),
            ).fetchall()

            results = []
            for r in rows:
                c = dict(r)
                comp_model = self._hydrate_company(conn, r)
                comp_dict = comp_model.model_dump()
                comp_dict["score"] = c["score"]
                comp_dict["priority"] = c["priority"]
                comp_dict["score_reasons"] = json.loads(c["score_reasons"] or "[]")
                results.append(comp_dict)
            return results

    def save_push_history(self, job_id: str, payload_summary: str, status: str, response_message: str = ""):
        with get_db(self.db_path) as conn:
            push_id = f"psh_{uuid.uuid4().hex[:12]}"
            pushed_at = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                INSERT INTO push_history (id, job_id, payload_summary, status, response_message, pushed_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (push_id, job_id, payload_summary, status, response_message, pushed_at),
            )

    def get_job_push_counters(self, job_id: str) -> Dict[str, int]:
        with get_db(self.db_path) as conn:
            approved = conn.execute(
                "SELECT COUNT(*) FROM companies WHERE job_id = ? AND review_status = 'approved'", (job_id,)
            ).fetchone()[0]
            pending = conn.execute(
                "SELECT COUNT(*) FROM companies WHERE job_id = ? AND review_status = 'pending'", (job_id,)
            ).fetchone()[0]
            rejected = conn.execute(
                "SELECT COUNT(*) FROM companies WHERE job_id = ? AND review_status = 'rejected'", (job_id,)
            ).fetchone()[0]
            submitted = conn.execute(
                "SELECT COUNT(*) FROM push_history WHERE job_id = ? AND status = 'submitted'", (job_id,)
            ).fetchone()[0]
            return {
                "approved_locally": approved,
                "push_eligible": approved,
                "pending_review": pending,
                "rejected": rejected,
                "submitted": submitted,
            }

    def _hydrate_company(self, conn: sqlite3.Connection, row: sqlite3.Row) -> Company:
        company_id = row["id"]
        emails = [
            Email(
                id=r["id"],
                company_id=r["company_id"],
                email=r["email"],
                normalized_email=r["normalized_email"],
                is_generic=bool(r["is_generic"]),
                source_url=r["source_url"],
                created_at=r["created_at"],
            )
            for r in conn.execute("SELECT * FROM emails WHERE company_id = ?", (company_id,)).fetchall()
        ]
        phones = [
            Phone(
                id=r["id"],
                company_id=r["company_id"],
                phone=r["phone"],
                normalized_phone=r["normalized_phone"],
                raw_phone=r["raw_phone"],
                source_url=r["source_url"],
                is_primary=bool(r["is_primary"]),
                created_at=r["created_at"],
            )
            for r in conn.execute("SELECT * FROM phones WHERE company_id = ?", (company_id,)).fetchall()
        ]
        socials = [
            SocialProfile(
                id=r["id"],
                company_id=r["company_id"],
                platform=r["platform"],
                url=r["url"],
                handle=r["handle"],
                source_url=r["source_url"],
                created_at=r["created_at"],
            )
            for r in conn.execute("SELECT * FROM social_profiles WHERE company_id = ?", (company_id,)).fetchall()
        ]
        contacts = [
            Contact(
                id=r["id"],
                company_id=r["company_id"],
                name=r["name"],
                title=r["title"],
                decision_maker_tier=r.get("decision_maker_tier") if isinstance(r, dict) else (r["decision_maker_tier"] if "decision_maker_tier" in r.keys() else None),
                email=r["email"],
                phone=r["phone"],
                linkedin_url=r["linkedin_url"],
                source_url=r["source_url"],
                created_at=r["created_at"],
            )
            for r in conn.execute("SELECT * FROM contacts WHERE company_id = ?", (company_id,)).fetchall()
        ]
        lead_candidate_row = conn.execute("SELECT * FROM lead_candidates WHERE company_id = ?", (company_id,)).fetchone()
        lead_candidate = None
        if lead_candidate_row:
            lead_candidate = LeadCandidate(
                id=lead_candidate_row["id"],
                company_id=lead_candidate_row["company_id"],
                job_id=lead_candidate_row["job_id"],
                score=lead_candidate_row["score"],
                priority=PriorityLevel(lead_candidate_row["priority"]),
                score_reasons=json.loads(lead_candidate_row["score_reasons"] or "[]"),
                created_at=lead_candidate_row["created_at"],
            )

        disc_from = json.loads(row["discovered_from"] or "[]") if "discovered_from" in row.keys() and row["discovered_from"] else []

        return Company(
            id=row["id"],
            job_id=row["job_id"],
            name=row["name"],
            normalized_name=row["normalized_name"],
            domain=row["domain"],
            website=row["website"],
            industry=row["industry"],
            category=row["category"],
            description=row["description"],
            address=row["address"],
            city=row["city"],
            state=row["state"],
            country=row["country"],
            source=row["source"],
            source_url=row["source_url"],
            confidence=row["confidence"],
            discovered_from=disc_from,
            query_variant=row["query_variant"] if "query_variant" in row.keys() else None,
            rating=row["rating"] if "rating" in row.keys() else None,
            review_count=row["review_count"] if "review_count" in row.keys() else None,
            website_missing=bool(row["website_missing"]) if "website_missing" in row.keys() else False,
            review_status=row["review_status"] if "review_status" in row.keys() else "pending",
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            emails=emails,
            phones=phones,
            social_profiles=socials,
            contacts=contacts,
            lead_candidate=lead_candidate,
        )


class CampaignRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def create_campaign(self, campaign_id: str, name: str, industry: str, location_scope: str, target_leads: int = 100):
        with get_db(self.db_path) as conn:
            now_str = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                INSERT INTO crawl_campaigns (id, name, industry, location_scope, target_leads, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (campaign_id, name, industry, location_scope, target_leads, "running", now_str, now_str),
            )

    def list_campaigns(self, limit: int = 50) -> List[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM crawl_campaigns ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]


class AgentRunRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def create_run(self, run_id: str, goal: str, provider: str, model: str, target_leads: int = 100):
        with get_db(self.db_path) as conn:
            now_str = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                INSERT INTO agent_runs (id, goal, status, provider, model, target_leads, started_at)
                VALUES (?, ?, 'planning', ?, ?, ?, ?)
                """,
                (run_id, goal, provider, model, target_leads, now_str),
            )

    def update_run(self, run_id: str, status: str, last_action: str = None, summary: str = None, current_job_id: str = None, valid_leads: int = 0):
        with get_db(self.db_path) as conn:
            now_str = datetime.now(timezone.utc).isoformat()
            completed_at = now_str if status in ["completed", "failed", "cancelled"] else None
            conn.execute(
                """
                UPDATE agent_runs
                SET status = ?, last_action = ?, summary = ?, current_job_id = ?, current_valid_leads = ?, completed_at = ?
                WHERE id = ?
                """,
                (status, last_action, summary, current_job_id, valid_leads, completed_at, run_id),
            )

    def log_action(self, run_id: str, action_type: str, summary: str, tool_call: str = None, tool_result_summary: str = None):
        with get_db(self.db_path) as conn:
            action_id = f"act_{uuid.uuid4().hex[:12]}"
            now_str = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                INSERT INTO agent_actions (id, agent_run_id, action_type, summary, tool_call, tool_result_summary, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (action_id, run_id, action_type, summary, tool_call, tool_result_summary, now_str),
            )

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            row = conn.execute("SELECT * FROM agent_runs WHERE id = ?", (run_id,)).fetchone()
            if not row:
                return None
            run_dict = dict(row)
            actions = conn.execute("SELECT * FROM agent_actions WHERE agent_run_id = ? ORDER BY created_at ASC", (run_id,)).fetchall()
            run_dict["actions"] = [dict(a) for a in actions]
            return run_dict


    def _hydrate_company(self, conn: sqlite3.Connection, row: sqlite3.Row) -> Company:
        company_id = row["id"]
        emails = [
            Email(
                id=r["id"],
                company_id=r["company_id"],
                email=r["email"],
                normalized_email=r["normalized_email"],
                is_generic=bool(r["is_generic"]),
                source_url=r["source_url"],
                created_at=r["created_at"],
            )
            for r in conn.execute("SELECT * FROM emails WHERE company_id = ?", (company_id,)).fetchall()
        ]
        phones = [
            Phone(
                id=r["id"],
                company_id=r["company_id"],
                phone=r["phone"],
                normalized_phone=r["normalized_phone"],
                raw_phone=r["raw_phone"],
                country_code=r["country_code"],
                source_url=r["source_url"],
                created_at=r["created_at"],
            )
            for r in conn.execute("SELECT * FROM phones WHERE company_id = ?", (company_id,)).fetchall()
        ]
        socials = [
            SocialProfile(
                id=r["id"],
                company_id=r["company_id"],
                platform=r["platform"],
                url=r["url"],
                normalized_url=r["normalized_url"],
                handle=r["handle"],
                source_url=r["source_url"],
                created_at=r["created_at"],
            )
            for r in conn.execute("SELECT * FROM social_profiles WHERE company_id = ?", (company_id,)).fetchall()
        ]
        contacts = [
            Contact(
                id=r["id"],
                company_id=r["company_id"],
                job_id=r["job_id"],
                name=r["name"],
                title=r["title"],
                email=r["email"],
                phone=r["phone"],
                linkedin_url=r["linkedin_url"],
                source_url=r["source_url"],
                confidence=r["confidence"],
                created_at=r["created_at"],
            )
            for r in conn.execute("SELECT * FROM contacts WHERE company_id = ?", (company_id,)).fetchall()
        ]

        return Company(
            id=row["id"],
            job_id=row["job_id"],
            name=row["name"],
            normalized_name=row["normalized_name"],
            domain=row["domain"],
            website=row["website"],
            industry=row["industry"],
            category=row["category"],
            description=row["description"],
            address=row["address"],
            city=row["city"],
            state=row["state"],
            country=row["country"],
            source=row["source"],
            source_url=row["source_url"],
            confidence=row["confidence"],
            discovered_from=json.loads(row["discovered_from"]) if "discovered_from" in row.keys() and row["discovered_from"] else [],
            query_variant=row["query_variant"] if "query_variant" in row.keys() else None,
            rating=row["rating"] if "rating" in row.keys() else None,
            review_count=row["review_count"] if "review_count" in row.keys() else None,
            website_missing=bool(row["website_missing"]) if "website_missing" in row.keys() and row["website_missing"] is not None else False,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            emails=emails,
            phones=phones,
            social_profiles=socials,
            contacts=contacts,
        )


class ErrorRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path

    def log_error(self, job_id: str, url: str, error_type: str, message: str, target_id: Optional[str] = None, stack_trace: Optional[str] = None):
        import uuid
        from datetime import datetime, timezone
        error_id = f"err_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO crawl_errors (id, job_id, target_id, url, error_type, message, stack_trace, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (error_id, job_id, target_id, url, error_type, message, stack_trace, now),
            )

    def list_job_errors(self, job_id: str) -> List[Dict[str, Any]]:
        with get_db(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM crawl_errors WHERE job_id = ? ORDER BY created_at DESC",
                (job_id,),
            ).fetchall()
            return [dict(r) for r in rows]
