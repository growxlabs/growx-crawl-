from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from growx_crawl.core.config import settings


class QueryExpander:
    @classmethod
    def expand_query(
        cls,
        query: Optional[str] = None,
        industry: Optional[str] = None,
        location: Optional[str] = None,
        max_variants: int = 10,
    ) -> List[str]:
        industry_name = (industry or "jewellery").lower()
        profile_data = cls._load_profile(industry_name)
        base_queries = profile_data.get("queries", [])

        loc_str = location.strip() if location else ""

        variants: List[str] = []
        seen = set()

        # 1. If explicit free-form query provided, put it first
        if query and query.strip() and query.strip().lower() != "seed crawl":
            clean_q = query.strip()
            variants.append(clean_q)
            seen.add(clean_q.lower())

        # 2. Generate expanded variants from profile + location
        for bq in base_queries:
            variant = f"{bq} {loc_str}".strip() if loc_str else bq.strip()
            if variant.lower() not in seen:
                seen.add(variant.lower())
                variants.append(variant)
                if len(variants) >= max_variants:
                    break

        return variants or [query or "company"]

    @classmethod
    def _load_profile(cls, industry_name: str) -> Dict[str, Any]:
        config_dir = settings.config_dir / "discovery"
        profile_path = config_dir / f"{industry_name}.yaml"
        if not profile_path.exists():
            profile_path = config_dir / "default.yaml"

        if profile_path.exists():
            try:
                with open(profile_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                pass
        return {"queries": [industry_name or "company"]}
