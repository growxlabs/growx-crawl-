"""
GrowX Verification Repository.
Defines storage interfaces for verification results and policies.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from growx_crawl.verification.models import VerificationResultEntity


class BaseVerificationRepository(ABC):
    @abstractmethod
    def save_result(self, result: VerificationResultEntity) -> None:
        pass

    @abstractmethod
    def get_result(self, entity_type: str, entity_id: str) -> Optional[VerificationResultEntity]:
        pass


class InMemoryVerificationRepository(BaseVerificationRepository):
    """In-memory verification repository for local runs and unit testing."""

    def __init__(self):
        self._results: Dict[str, VerificationResultEntity] = {}

    def save_result(self, result: VerificationResultEntity) -> None:
        key = f"{result.entity_type}:{result.entity_id}"
        self._results[key] = result

    def get_result(self, entity_type: str, entity_id: str) -> Optional[VerificationResultEntity]:
        key = f"{entity_type}:{entity_id}"
        return self._results.get(key)
