from typing import Optional
from growx_crawl.crawler.base import BaseCrawler
from growx_crawl.models.page import FetchedPage
from growx_crawl.models.target import CrawlTarget


class BrowserCrawler(BaseCrawler):
    """
    Playwright Browser Crawler fallback interface.
    Used when client-side JavaScript rendering is required.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless

    async def fetch(self, target: CrawlTarget) -> Optional[FetchedPage]:
        # Browser fallback stub - can be extended with Playwright if installed
        target.last_error = "Browser crawler fallback required but Playwright driver disabled"
        return None
