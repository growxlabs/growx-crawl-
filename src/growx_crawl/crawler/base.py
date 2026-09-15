from abc import ABC, abstractmethod
from typing import Optional
from growx_crawl.models.page import FetchedPage
from growx_crawl.models.target import CrawlTarget


class BaseCrawler(ABC):
    @abstractmethod
    async def fetch(self, target: CrawlTarget) -> Optional[FetchedPage]:
        """
        Fetches the content for a given CrawlTarget.
        Returns FetchedPage or None if fetching failed.
        """
        pass
