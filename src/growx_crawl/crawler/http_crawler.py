import asyncio
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from growx_crawl.crawler.base import BaseCrawler
from growx_crawl.crawler.politeness import DomainPolitenessManager
from growx_crawl.models.page import FetchedPage
from growx_crawl.models.target import CrawlTarget


class HttpCrawler(BaseCrawler):
    def __init__(
        self,
        user_agent: str = "GrowXCrawl/1.0 (+https://growxlabs.tech/bot)",
        timeout_seconds: float = 15.0,
        max_response_bytes: int = 5 * 1024 * 1024,  # 5 MB
        politeness_manager: Optional[DomainPolitenessManager] = None,
    ):
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes
        self.politeness_manager = politeness_manager or DomainPolitenessManager()

    async def fetch(self, target: CrawlTarget) -> Optional[FetchedPage]:
        await self.politeness_manager.throttle(target.domain)

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                follow_redirects=True,
                headers=headers,
                verify=False,  # Allow self-signed SSL certs for crawling robustness
            ) as client:
                async with client.stream("GET", target.url) as response:
                    content_type = response.headers.get("content-type", "").lower()

                    # Reject large binary files (PDFs, images, zip, audio/video)
                    if any(
                        binary_type in content_type
                        for binary_type in [
                            "image/",
                            "audio/",
                            "video/",
                            "application/pdf",
                            "application/zip",
                            "application/octet-stream",
                        ]
                    ):
                        target.last_error = f"Ignored binary content-type: {content_type}"
                        return None

                    body_bytes = bytearray()
                    async for chunk in response.aiter_bytes():
                        body_bytes.extend(chunk)
                        if len(body_bytes) > self.max_response_bytes:
                            target.last_error = "Response exceeded max size limit (5MB)"
                            return None

                    html_content = body_bytes.decode("utf-8", errors="replace")

                    # Extract title and text content
                    soup = BeautifulSoup(html_content, "lxml")
                    title_elem = soup.find("title")
                    title = title_elem.get_text(strip=True) if title_elem else None

                    # Strip script and style tags for clean text content
                    for s in soup(["script", "style", "noscript", "svg"]):
                        s.extract()
                    text_content = soup.get_text(separator=" ", strip=True)

                    return FetchedPage(
                        job_id=target.job_id,
                        target_id=target.id,
                        url=str(response.url),
                        status_code=response.status_code,
                        content_type=content_type,
                        html_content=html_content,
                        title=title,
                        text_content=text_content,
                    )

        except Exception as e:
            target.last_error = str(e)
            return None
