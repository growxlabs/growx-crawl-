import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from growx_crawl.storage.db import get_db
from growx_crawl.search.schema import init_search_tables

logger = logging.getLogger("growx_crawl.search.indexer")


class DocumentIndexer:
    """
    High-performance document parser, link extractor, and FTS5 inverted index writer.
    """

    @staticmethod
    def extract_document_data(url: str, html: str, fallback_title: str = "") -> Dict[str, Any]:
        """
        Parses raw HTML: strips boilerplate noise, extracts title, meta description,
        clean body text, and discovered outlinks.
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()

        if not html:
            return {
                "url": url,
                "domain": domain,
                "title": fallback_title or domain,
                "description": "",
                "content": "",
                "word_count": 0,
                "content_length": 0,
                "outlinks": [],
            }

        soup = BeautifulSoup(html, "html.parser")

        # 1. Extract Title
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        if not title:
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text().strip()
        if not title:
            title = fallback_title or domain

        # 2. Extract Meta Description
        description = ""
        meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find(
            "meta", attrs={"property": "og:description"}
        )
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"].strip()

        # 3. Extract Outlinks for Link Graph & PageRank Authority
        outlinks: List[Tuple[str, str, str]] = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            abs_url = urljoin(url, href)
            parsed_dest = urlparse(abs_url)
            if parsed_dest.scheme in ("http", "https") and parsed_dest.netloc:
                anchor = " ".join(a_tag.get_text().split())[:120]
                outlinks.append((abs_url, parsed_dest.netloc.lower(), anchor))

        # 4. Remove noisy boilerplate tags
        for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "aside", "form"]):
            tag.decompose()

        raw_text = soup.get_text(separator=" ")
        clean_text = " ".join(raw_text.split())
        words = clean_text.split()

        # If description was empty, extract first sentence or 180 chars of text
        if not description and clean_text:
            description = clean_text[:180] + ("..." if len(clean_text) > 180 else "")

        return {
            "url": url,
            "domain": domain,
            "title": title[:300],
            "description": description[:500],
            "content": clean_text[:100000],  # Index up to 100k characters per document
            "word_count": len(words),
            "content_length": len(clean_text),
            "outlinks": outlinks[:150],  # Store top 150 outlinks per page
        }

    def index_document(
        self,
        target_id: str,
        url: str,
        html: str,
        fallback_title: str = "",
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Indexes a single web page into SQLite FTS5 inverted index and updates link graph.
        """
        now_iso = timestamp or datetime.now(timezone.utc).isoformat()
        doc = self.extract_document_data(url, html, fallback_title)

        with get_db() as conn:
            init_search_tables(conn)

            # 1. Remove old version of document from FTS5 index if previously indexed
            conn.execute("DELETE FROM search_index WHERE target_id = ?;", (target_id,))
            conn.execute("DELETE FROM search_index WHERE url = ?;", (url,))

            # 2. Insert into FTS5 inverted index
            conn.execute(
                """
                INSERT INTO search_index (target_id, url, domain, title, description, content)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    target_id,
                    url,
                    doc["domain"],
                    doc["title"],
                    doc["description"],
                    doc["content"],
                ),
            )

            # 3. Upsert into structured document catalog
            conn.execute(
                """
                INSERT OR REPLACE INTO search_documents (
                    target_id, url, domain, title, description,
                    content_length, word_count, indexed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    target_id,
                    url,
                    doc["domain"],
                    doc["title"],
                    doc["description"],
                    doc["content_length"],
                    doc["word_count"],
                    now_iso,
                ),
            )

            # 4. Record outlinks into link graph table
            if doc["outlinks"]:
                link_rows = [
                    (url, doc["domain"], dest_url, dest_domain, anchor, now_iso)
                    for (dest_url, dest_domain, anchor) in doc["outlinks"]
                ]
                conn.executemany(
                    """
                    INSERT OR IGNORE INTO page_links (
                        from_url, from_domain, to_url, to_domain, anchor_text, discovered_at
                    ) VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    link_rows,
                )

                # Update inbound links counter for touched domains
                dest_domains = list(set([dest_domain for (_, dest_domain, _) in doc["outlinks"]]))
                for d in dest_domains[:20]:
                    conn.execute(
                        """
                        UPDATE search_documents
                        SET inbound_links = (SELECT COUNT(*) FROM page_links WHERE to_domain = ?)
                        WHERE domain = ?;
                        """,
                        (d, d),
                    )

        return {
            "status": "indexed",
            "target_id": target_id,
            "url": url,
            "domain": doc["domain"],
            "title": doc["title"],
            "word_count": doc["word_count"],
            "outlinks_count": len(doc["outlinks"]),
        }

    def bulk_reindex_all_pages(self, limit: int = 500) -> Dict[str, Any]:
        """
        Scans all crawled pages stored in SQLite 'pages' table and builds the full-text search index.
        """
        indexed_count = 0
        with get_db() as conn:
            init_search_tables(conn)
            rows = conn.execute(
                """
                SELECT p.id, p.target_id, p.url, p.title, p.html_content, p.created_at
                FROM pages p
                ORDER BY p.created_at DESC
                LIMIT ?;
                """,
                (limit,),
            ).fetchall()

        for r in rows:
            target_id = r["target_id"] or r["id"]
            url = r["url"]
            html = r["html_content"] or ""
            title = r["title"] or ""
            created_at = r["created_at"]
            if url and html:
                try:
                    self.index_document(
                        target_id=target_id,
                        url=url,
                        html=html,
                        fallback_title=title,
                        timestamp=created_at,
                    )
                    indexed_count += 1
                except Exception as err:
                    logger.warning(f"Error indexing page {url}: {err}")

        return {
            "total_scanned": len(rows),
            "indexed_count": indexed_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


document_indexer = DocumentIndexer()
