from abc import ABC, abstractmethod
from typing import Any, Dict
from growx_crawl.models.page import FetchedPage


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, page: FetchedPage) -> Dict[str, Any]:
        """
        Extracts entity data from a FetchedPage.
        """
        pass
