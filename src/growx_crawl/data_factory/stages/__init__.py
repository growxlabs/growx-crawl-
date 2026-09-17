"""
GrowX Data Factory Pipeline Stages.
Exports all 9 canonical stage processors:
1. Discover
2. Crawl
3. Extract
4. Resolve
5. Facts
6. Verify
7. Quality
8. History
9. Index
"""

from growx_crawl.data_factory.stages.crawl import CrawlStage
from growx_crawl.data_factory.stages.discover import DiscoverStage
from growx_crawl.data_factory.stages.extract import ExtractStage
from growx_crawl.data_factory.stages.facts import FactsStage
from growx_crawl.data_factory.stages.history import HistoryStage
from growx_crawl.data_factory.stages.index import IndexStage
from growx_crawl.data_factory.stages.quality import QualityStage
from growx_crawl.data_factory.stages.resolve import ResolveStage
from growx_crawl.data_factory.stages.verify import VerifyStage

__all__ = [
    "DiscoverStage",
    "CrawlStage",
    "ExtractStage",
    "ResolveStage",
    "FactsStage",
    "VerifyStage",
    "QualityStage",
    "HistoryStage",
    "IndexStage",
]
