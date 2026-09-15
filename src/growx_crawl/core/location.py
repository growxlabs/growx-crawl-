from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field


class LocationInfo(BaseModel):
    city: str
    district: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"

    def to_display_string(self) -> str:
        parts = [self.city]
        if self.state and self.state != self.city:
            parts.append(self.state)
        if self.country and self.country != "India":
            parts.append(self.country)
        return ", ".join(parts)


class LocationRegistry:
    _data: Dict[str, Any] = {}
    _loaded: bool = False

    @classmethod
    def _load(cls):
        if cls._loaded and cls._data:
            return

        file_path = Path(__file__).resolve().parent.parent.parent.parent / "config" / "locations" / "india.yaml"
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    cls._data = yaml.safe_load(f) or {}
            except Exception:
                pass
        cls._loaded = True

    @classmethod
    def resolve_location(cls, location_text: str) -> LocationInfo:
        cls._load()
        text_clean = (location_text or "Hyderabad").strip()
        text_lower = text_clean.lower()

        states = cls._data.get("states", {})

        # 1. Exact or substring match against known cities
        for st_name, st_info in states.items():
            for city in st_info.get("cities", []):
                if city.lower() in text_lower:
                    return LocationInfo(city=city, state=st_name, country="India")

        # 2. Check state names
        for st_name, st_info in states.items():
            if st_name.lower() in text_lower:
                return LocationInfo(city=st_info.get("capital", text_clean.title()), state=st_name, country="India")

        return LocationInfo(city=text_clean.title(), state="Telangana", country="India")

    @classmethod
    def get_cities_for_state(cls, state_name: str) -> List[LocationInfo]:
        cls._load()
        states = cls._data.get("states", {})
        for st_name, st_info in states.items():
            if state_name.lower() in st_name.lower():
                return [LocationInfo(city=c, state=st_name, country="India") for c in st_info.get("cities", [])]
        return [LocationInfo(city=state_name, state=state_name, country="India")]

    @classmethod
    def get_top_cities_for_country(cls, country_name: str = "India", top_n: int = 25) -> List[LocationInfo]:
        cls._load()
        results: List[LocationInfo] = []
        states = cls._data.get("states", {})
        for st_name, st_info in states.items():
            for c in st_info.get("cities", []):
                results.append(LocationInfo(city=c, state=st_name, country="India"))
                if len(results) >= top_n:
                    return results
        return results if results else [LocationInfo(city="Hyderabad", state="Telangana", country="India")]


class LocationPlanner:
    @classmethod
    def plan_locations(
        cls,
        location: Optional[str] = None,
        locations: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        top_cities: Optional[int] = None,
    ) -> List[LocationInfo]:
        if locations:
            city_names = [c.strip() for c in locations.split(",") if c.strip()]
            return [LocationRegistry.resolve_location(c) for c in city_names]

        if state:
            return LocationRegistry.get_cities_for_state(state)

        if country and top_cities:
            return LocationRegistry.get_top_cities_for_country(country, top_n=top_cities)

        if location:
            return [LocationRegistry.resolve_location(location)]

        return [LocationInfo(city="Hyderabad", state="Telangana", country="India")]
