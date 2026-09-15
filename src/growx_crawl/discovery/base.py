from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from growx_crawl.models.discovery import DiscoveryCandidate


class DiscoveryProvider(ABC):
    @abstractmethod
    async def discover(
        self,
        query: str,
        job_id: str,
        location: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 50,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[DiscoveryCandidate]:
        """
        Discovers company candidates for a given query/location.
        """
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Returns provider health status and configuration details.
        """
        pass
