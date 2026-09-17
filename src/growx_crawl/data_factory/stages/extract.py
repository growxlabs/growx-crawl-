"""
GrowX Data Factory Stage 3: Extraction.
Converts raw crawl artifacts into structured attribute observations with provenance links.
Supports offline reprocessing directly from R2 without recrawling.
"""

import re
from typing import Any, Dict, List, Optional
from growx_crawl.data_factory.metrics import DataFactoryMetrics
from growx_crawl.extractors.structured import structured_extractor
from growx_crawl.object_store import BucketName, get_object_store
from growx_crawl.shared.ids import generate_id
from growx_crawl.shared.time import utc_iso_now


class ExtractStage:
    """Extracts structured entity attributes and packages them into observations."""

    def __init__(self, object_store=None):
        if object_store is not None:
            self.object_store = object_store
        else:
            try:
                self.object_store = get_object_store()
            except Exception:
                self.object_store = None

    def extract_from_html(self, html: str, domain: str, company_name: str) -> Dict[str, Any]:
        """Runs structured extractor and regex extractors over HTML body."""
        # Simple robust heuristic parsing
        emails = list(set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", html)))
        phones = list(set(re.findall(r"\+?[0-9]{1,3}[-.\s]?[0-9]{3}[-.\s]?[0-9]{4,6}", html)))

        # Clean non-corporate emails
        clean_emails = [e for e in emails if not e.endswith(".png") and not e.endswith(".jpg")]

        # Determine description
        desc_match = re.search(r"<p>(.*?)</p>", html, re.DOTALL | re.IGNORECASE)
        description = desc_match.group(1).strip() if desc_match else f"{company_name} corporate profile."

        return {
            "company_name": company_name,
            "domain": domain,
            "description": description,
            "emails": clean_emails,
            "phones": phones,
            "extracted_at": utc_iso_now(),
        }

    def execute(
        self,
        crawled_items: List[Dict[str, Any]],
        metrics: DataFactoryMetrics,
    ) -> List[Dict[str, Any]]:
        """Processes crawl results into raw observation packages."""
        extracted_observations: List[Dict[str, Any]] = []

        for item in crawled_items:
            html = item.get("raw_html") or ""
            domain = item["domain"]
            name = item.get("company_name", domain)

            extracted = self.extract_from_html(html, domain, name)
            extracted["source_url"] = item.get("url", f"https://{domain}")
            extracted["r2_key"] = item.get("r2_key")
            extracted["content_hash"] = item.get("content_hash")
            extracted["observation_id"] = generate_id("obs_")

            metrics.observations_produced += 1
            extracted_observations.append(extracted)

        return extracted_observations

    def reprocess_from_r2(self, r2_keys: List[str], metrics: DataFactoryMetrics) -> List[Dict[str, Any]]:
        """
        Offline extraction reprocessing: loads stored raw HTML artifacts directly
        from R2 without performing any live network crawl.
        """
        import asyncio
        import concurrent.futures
        import inspect

        reprocessed: List[Dict[str, Any]] = []
        for key in r2_keys:
            try:
                raw_bytes = None
                if not self.object_store:
                    continue

                if hasattr(self.object_store, "get_object"):
                    obj = self.object_store.get_object(key)
                    if obj is not None:
                        raw_bytes = obj.read() if hasattr(obj, "read") else (obj.encode() if isinstance(obj, str) else obj)
                elif hasattr(self.object_store, "get"):
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = None

                    if loop and loop.is_running():
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            raw_bytes = pool.submit(asyncio.run, self.object_store.get(BucketName.RAW, key)).result()
                    else:
                        coro = self.object_store.get(BucketName.RAW, key)
                        if inspect.isawaitable(coro):
                            raw_bytes = asyncio.run(coro)
                        else:
                            raw_bytes = coro

                if not raw_bytes:
                    continue

                html = raw_bytes.decode("utf-8") if isinstance(raw_bytes, bytes) else str(raw_bytes)
                domain = key.split("/")[1] if "/" in key else "unknown.com"
                obs = self.extract_from_html(html, domain, domain.title())
                obs["r2_key"] = key
                obs["observation_id"] = generate_id("obs_reproc_")
                metrics.observations_produced += 1
                reprocessed.append(obs)
            except Exception:
                metrics.errors += 1
        return reprocessed
