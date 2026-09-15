import os
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from pydantic import BaseModel, Field


class IndustryProfile(BaseModel):
    name: str
    aliases: List[str] = Field(default_factory=list)
    search_terms: List[str] = Field(default_factory=list)
    positive_keywords: List[str] = Field(default_factory=list)
    negative_keywords: List[str] = Field(default_factory=list)
    decision_maker_roles: List[str] = Field(default_factory=list)
    scoring_weights: Dict[str, int] = Field(default_factory=lambda: {"contactability": 40, "digital_presence": 30, "relevance": 30})


class IndustryProfileRegistry:
    _profiles: Dict[str, IndustryProfile] = {}
    _loaded: bool = False

    @classmethod
    def _load_profiles(cls):
        if cls._loaded and cls._profiles:
            return

        base_dir = Path(__file__).resolve().parent.parent.parent.parent / "config" / "industries"
        if not base_dir.exists():
            base_dir.mkdir(parents=True, exist_ok=True)

        for file_path in base_dir.glob("*.yaml"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "name" in data:
                        prof = IndustryProfile(**data)
                        key = prof.name.lower().replace(" ", "_")
                        cls._profiles[key] = prof
                        for alias in prof.aliases:
                            cls._profiles[alias.lower().replace(" ", "_")] = prof
            except Exception:
                pass

        cls._loaded = True

    @classmethod
    def get_profile(cls, name_or_query: str) -> IndustryProfile:
        cls._load_profiles()
        clean_key = (name_or_query or "general").strip().lower().replace(" ", "_")

        if clean_key in cls._profiles:
            return cls._profiles[clean_key]

        # Partial matching check
        for k, prof in cls._profiles.items():
            if k in clean_key or clean_key in k:
                return prof

        # Dynamic fallback for custom free-form query strings
        tokens = [t for t in name_or_query.split() if len(t) > 2]
        return IndustryProfile(
            name=name_or_query.title(),
            aliases=[name_or_query],
            search_terms=[
                f"{name_or_query} company",
                f"{name_or_query} supplier",
                f"{name_or_query} services",
                f"best {name_or_query}",
            ],
            positive_keywords=tokens,
            negative_keywords=["scam", "spam"],
            decision_maker_roles=["Owner", "Founder", "Director", "Manager"],
            scoring_weights={"contactability": 40, "digital_presence": 30, "relevance": 30},
        )

    @classmethod
    def list_industry_names(cls) -> List[str]:
        cls._load_profiles()
        unique_names = sorted(list(set(p.name for p in cls._profiles.values())))
        return unique_names
