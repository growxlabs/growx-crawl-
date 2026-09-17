"""
GrowX Data Factory Metrics & Telemetry.
Tracks high-resolution operational counters, stage outcomes, change statistics,
and cost allocations for every factory execution.
"""

from typing import Any, Dict
from growx_crawl.data_factory.models import MorningSummary
from growx_crawl.shared.time import utc_iso_now


class DataFactoryMetrics:
    """Telemetry collector and morning intelligence summary generator."""

    def __init__(self):
        self.queries_run: int = 0
        self.results_found: int = 0
        self.new_domains: int = 0
        self.known_domains: int = 0
        self.pages_fetched_http: int = 0
        self.pages_fetched_browser: int = 0
        self.pages_failed: int = 0
        self.bytes_downloaded: int = 0
        self.observations_produced: int = 0
        self.facts_produced: int = 0
        self.facts_changed: int = 0
        self.companies_created: int = 0
        self.companies_updated: int = 0
        self.people_created: int = 0
        self.er_matches: int = 0
        self.er_reviews: int = 0
        self.verifications_reused: int = 0
        self.verifications_executed: int = 0
        self.quality_passes: int = 0
        self.quality_blocks: int = 0
        self.quarantined: int = 0
        self.errors: int = 0
        self.estimated_cost: float = 0.0

    def get_summary(self) -> Dict[str, Any]:
        return {
            "queries_run": self.queries_run,
            "results_found": self.results_found,
            "new_domains": self.new_domains,
            "known_domains": self.known_domains,
            "pages_fetched_http": self.pages_fetched_http,
            "pages_fetched_browser": self.pages_fetched_browser,
            "pages_failed": self.pages_failed,
            "bytes_downloaded": self.bytes_downloaded,
            "observations_produced": self.observations_produced,
            "facts_produced": self.facts_produced,
            "facts_changed": self.facts_changed,
            "companies_created": self.companies_created,
            "companies_updated": self.companies_updated,
            "people_created": self.people_created,
            "er_matches": self.er_matches,
            "er_reviews": self.er_reviews,
            "verifications_reused": self.verifications_reused,
            "verifications_executed": self.verifications_executed,
            "quality_passes": self.quality_passes,
            "quality_blocks": self.quality_blocks,
            "quarantined": self.quarantined,
            "errors": self.errors,
            "estimated_cost": round(self.estimated_cost, 4),
        }

    def generate_morning_report(
        self,
        run_id: str,
        started_at: str,
        completed_at: Optional[str] = None,
    ) -> MorningSummary:
        end_time = completed_at or utc_iso_now()
        total_companies = self.companies_created + self.companies_updated
        cost_per_co = round(self.estimated_cost / max(1, total_companies), 4)

        report_md = f"""# GrowX Morning Intelligence Report
**Run ID:** `{run_id}`  
**Window:** `{started_at}` -> `{end_time}`  
**Estimated Run Cost:** ${self.estimated_cost:.2f} (Avg ${cost_per_co:.4f}/company)  

### Operational Highlights
- **Discovery:** {self.queries_run:,} queries executed | {self.new_domains:,} new domains discovered | {self.known_domains:,} known fresh domains skipped
- **Crawl & Extract:** {self.pages_fetched_http + self.pages_fetched_browser:,} pages crawled ({self.pages_fetched_http:,} HTTP, {self.pages_fetched_browser:,} browser) | {self.observations_produced:,} raw observations produced
- **Entities & Resolution:** {self.companies_created:,} new companies created | {self.companies_updated:,} updated | {self.people_created:,} decision-makers added | {self.er_matches:,} exact entity merges
- **Facts & Evidence:** {self.facts_produced:,} facts recorded | {self.facts_changed:,} critical attribute changes detected
- **Trust & Quality:** {self.verifications_reused:,} existing verifications reused | {self.verifications_executed:,} fresh verifications | {self.quality_passes:,} entities passed GTM quality gates
- **Resilience:** {self.errors:,} isolated domain errors | {self.quarantined:,} quarantined payloads
"""

        return MorningSummary(
            run_id=run_id,
            started_at=started_at,
            completed_at=end_time,
            queries_run=self.queries_run,
            new_domains=self.new_domains,
            companies_created=self.companies_created,
            companies_updated=self.companies_updated,
            people_created=self.people_created,
            facts_added=self.facts_produced,
            facts_changed=self.facts_changed,
            verified_companies=self.verifications_executed + self.verifications_reused,
            quality_trusted_entities=self.quality_passes,
            errors=self.errors,
            estimated_cost=self.estimated_cost,
            cost_per_company=cost_per_co,
            report_markdown=report_md.strip(),
            metadata_json=self.get_summary(),
        )
