"""
GrowX Data Factory Planner.
Builds the comprehensive operational plan for a nightly or on-demand run,
merging segment configurations, search queries, stale entity refreshes, and resource quotas.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from growx_crawl.data_factory.models import (
    CrawlMode,
    DataFactoryPlan,
    PriorityTier,
    RunType,
    TargetSegment,
)
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now


class DataFactoryPlanner:
    """Compiles executable DataFactoryPlans from target segments and stale queues."""

    DEFAULT_SEGMENTS_DIR = Path("config/data_factory/segments")

    def __init__(self, segments_dir: Optional[Path] = None):
        self.segments_dir = segments_dir or self.DEFAULT_SEGMENTS_DIR

    def load_segment_file(self, file_path: Path) -> Optional[TargetSegment]:
        if not file_path.exists():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return TargetSegment(
                name=data.get("name", file_path.stem),
                industry_terms=data.get("industry_terms", []),
                geo_terms=data.get("geo_terms", []),
                company_size_hints=data.get("company_size_hints", []),
                search_queries=data.get("search_queries", []),
                crawl_depth=data.get("crawl_depth", 2),
                priority=PriorityTier(data.get("priority", "P1")),
            )
        except Exception:
            return None

    def load_all_segments(self) -> List[TargetSegment]:
        segments: List[TargetSegment] = []
        if not self.segments_dir.exists():
            return segments
        for p in self.segments_dir.glob("*.yaml"):
            seg = self.load_segment_file(p)
            if seg:
                segments.append(seg)
        return segments

    def create_plan(
        self,
        run_type: RunType = RunType.NIGHTLY,
        segments: Optional[List[TargetSegment]] = None,
        custom_config: Optional[Dict[str, Any]] = None,
    ) -> DataFactoryPlan:
        cfg = dict(custom_config or {})

        loaded_segments = segments or self.load_all_segments()
        if not loaded_segments:
            # Fallback default segment for GrowxLabs priorities (Manufacturing & Fabrication)
            loaded_segments = [
                TargetSegment(
                    name="india_custom_fabrication",
                    industry_terms=["Precision Sheet Metal", "Custom CNC Fabrication", "Industrial Manufacturing"],
                    geo_terms=["India", "Pune", "Bengaluru", "Hyderabad"],
                    company_size_hints=["50-500"],
                    search_queries=[
                        "precision sheet metal fabrication companies India",
                        "custom CNC machining industrial manufacturers Pune Bengaluru",
                    ],
                    crawl_depth=2,
                    priority=PriorityTier.P1,
                )
            ]

        plan_id = generate_id("plan_")
        return DataFactoryPlan(
            id=plan_id,
            version="v1",
            run_type=run_type,
            target_segments=loaded_segments,
            discovery_sources=cfg.get("discovery_sources", ["search", "seed", "expansion"]),
            max_companies=cfg.get("max_companies", 500),
            max_pages=cfg.get("max_pages", 1000),
            max_browser_sessions=cfg.get("max_browser_sessions", 50),
            max_runtime_minutes=cfg.get("max_runtime_minutes", 480),
            refresh_budget=cfg.get("refresh_budget", 200),
            ai_budget=cfg.get("ai_budget", 10.0),
            verification_budget=cfg.get("verification_budget", 5.0),
            crawl_mode=CrawlMode(cfg.get("crawl_mode", "standard")),
            priority_rules=cfg.get("priority_rules", {}),
            created_at=utc_iso_now(),
        )
