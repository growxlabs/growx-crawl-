"""
GrowX Entity Resolution Repository.
Provides storage interfaces and local persistence for resolution candidates.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from growx_crawl.entity_resolution.models import ResolutionCandidate


class BaseResolutionRepository(ABC):
    @abstractmethod
    def save_candidate(self, candidate: ResolutionCandidate) -> None:
        pass

    @abstractmethod
    def get_candidate(self, candidate_id: str) -> Optional[ResolutionCandidate]:
        pass

    @abstractmethod
    def list_pending_reviews(self, limit: int = 50) -> List[ResolutionCandidate]:
        pass


class InMemoryResolutionRepository(BaseResolutionRepository):
    """In-memory candidate repository for local operations and testing."""

    def __init__(self):
        self._candidates: Dict[str, ResolutionCandidate] = {}

    def save_candidate(self, candidate: ResolutionCandidate) -> None:
        self._candidates[candidate.id] = candidate

    def get_candidate(self, candidate_id: str) -> Optional[ResolutionCandidate]:
        return self._candidates.get(candidate_id)

    def list_pending_reviews(self, limit: int = 50) -> List[ResolutionCandidate]:
        return [c for c in self._candidates.values() if c.status == "pending"][:limit]
