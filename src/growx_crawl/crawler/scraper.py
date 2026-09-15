from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse
import uuid
from bs4 import BeautifulSoup

from growx_crawl.crawler.fetcher import fetcher_pipeline
from growx_crawl.crawler.robots import robots_engine
from growx_crawl.storage.db import get_db


def ensure_base_href(html: str, base_url: str) -> str:
    """
    Ensure the HTML document has a <base href="..."> tag in <head>
    so that all relative CSS stylesheets, fonts, and images resolve correctly
    when viewed offline, in an iframe, or from database snapshots.
    """
    if not html or not base_url:
        return html
    if "<base " in html.lower():
        return html
    base_tag = f'<base href="{base_url}">'
    head_match = re.search(r"<head[^>]*>", html, re.IGNORECASE)
    if head_match:
        pos = head_match.end()
        return html[:pos] + "\n  " + base_tag + html[pos:]
    html_match = re.search(r"<html[^>]*>", html, re.IGNORECASE)
    if html_match:
        pos = html_match.end()
        return html[:pos] + f"\n<head>\n  {base_tag}\n</head>" + html[pos:]
    return f"<head>{base_tag}</head>\n" + html


class ScraperEngine:
    """
    Capability 1: Single-Page Scraper with Auto-Escalating Fetcher,
    robots.txt compliance check, and persistent target page snapshot storage.
    """

    async def scrape(
        self,
        url: str,
        fetcher: str = "auto",
        wait_for: Optional[str] = None,
        wait_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[List[Dict[str, str]]] = None,
        proxy: Optional[str] = None,
        timeout: int = 30,
        respect_robots: bool = False,
    ) -> Dict[str, Any]:
        # Check robots.txt compliance if requested
        if respect_robots:
            allowed = await robots_engine.can_fetch(url)
            if not allowed:
                return {
                    "status": "blocked",
                    "url": url,
                    "error": "Blocked by robots.txt compliance rules",
                    "respect_robots": True,
                }

        fetch_headers = dict(headers or {})
        if cookies:
            cookie_str = "; ".join([f"{c.get('name')}={c.get('value')}" for c in cookies if 'name' in c and 'value' in c])
            if cookie_str:
                fetch_headers["Cookie"] = cookie_str

        res = await fetcher_pipeline.fetch(
            url=url,
            mode=fetcher,
            wait_for=wait_for,
            wait_ms=wait_ms,
            headers=fetch_headers,
            proxy=proxy,
            timeout=timeout,
        )

        soup = BeautifulSoup(res.html, "html.parser")
        parsed_url = urlparse(url)

        # Title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Meta tags
        def get_meta(attr: str, val: str) -> Optional[str]:
            m = soup.find("meta", attrs={attr: val})
            return m.get("content", "").strip() if m else None

        description = get_meta("name", "description") or get_meta("property", "og:description") or ""
        og_title = get_meta("property", "og:title") or title
        og_image = get_meta("property", "og:image") or ""
        og_type = get_meta("property", "og:type") or "website"
        canonical_link = soup.find("link", rel="canonical")
        canonical = canonical_link.get("href") if canonical_link else url

        # Headings
        headings: List[Dict[str, str]] = []
        for tag in ["h1", "h2", "h3"]:
            for el in soup.find_all(tag):
                t = el.get_text(strip=True)
                if t and len(headings) < 30:
                    headings.append({"tag": tag, "text": t})

        # Links
        links: List[Dict[str, Any]] = []
        seen_links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            abs_url = urljoin(url, href)
            if abs_url in seen_links:
                continue
            seen_links.add(abs_url)
            is_external = urlparse(abs_url).netloc != parsed_url.netloc
            link_text = a.get_text(strip=True)
            if len(links) < 60:
                links.append({"href": abs_url, "text": link_text, "is_external": is_external})

        # Images
        images: List[Dict[str, str]] = []
        seen_imgs = set()
        for img in soup.find_all("img", src=True):
            src = img["src"].strip()
            if not src or src.startswith("data:"):
                continue
            abs_src = urljoin(url, src)
            if abs_src in seen_imgs:
                continue
            seen_imgs.add(abs_src)
            alt = img.get("alt", "").strip()
            if len(images) < 40:
                images.append({"src": abs_src, "alt": alt})

        # Full-Page CSS & Stylesheet Extraction
        stylesheets: List[Dict[str, Any]] = []
        seen_sheets = set()
        for link in soup.find_all("link"):
            rel = link.get("rel", [])
            rel_list = [r.lower() for r in (rel if isinstance(rel, list) else [rel])]
            if "stylesheet" in rel_list:
                href = link.get("href", "").strip()
                if not href or href.startswith("data:"):
                    continue
                abs_href = urljoin(url, href)
                if abs_href in seen_sheets:
                    continue
                seen_sheets.add(abs_href)
                media = link.get("media", "").strip() or "all"
                link_id = link.get("id", "").strip() or None
                stylesheets.append({
                    "href": abs_href,
                    "media": media,
                    "id": link_id,
                })

        # Inline style blocks & character count
        inline_style_tags = soup.find_all("style")
        inline_styles: List[Dict[str, Any]] = []
        total_inline_css_chars = 0
        for style_tag in inline_style_tags:
            css_text = style_tag.get_text()
            total_inline_css_chars += len(css_text)
            if len(inline_styles) < 10:
                inline_styles.append({
                    "id": style_tag.get("id"),
                    "length_chars": len(css_text),
                    "preview": css_text[:120].strip() + ("..." if len(css_text) > 120 else ""),
                })

        # Dynamic stylesheets from browser runtime if available
        dynamic_sheets = (res.extra_data.get("dynamic_stylesheets", [])
                          if hasattr(res, "extra_data") and res.extra_data else [])
        for ds in dynamic_sheets:
            d_href = ds.get("href")
            if d_href and d_href not in seen_sheets:
                seen_sheets.add(d_href)
                stylesheets.append({
                    "href": d_href,
                    "media": ds.get("media") or "all",
                    "id": ds.get("title"),
                    "rules_count": ds.get("rules_count", 0),
                    "dynamic": True,
                })

        # Text preview
        for s in soup(["script", "style", "noscript", "svg"]):
            s.decompose()
        clean_text = " ".join(soup.get_text().split())
        words = clean_text.split()

        # Preserve full-page CSS and relative asset resolution by injecting <base href>
        persisted_html = ensure_base_href(res.html, url)

        # Generate persistent target_id & store HTML snapshot in SQLite
        target_id = f"tgt_{uuid.uuid4().hex[:10]}"
        job_id = f"single_{uuid.uuid4().hex[:8]}"
        page_id = f"page_{uuid.uuid4().hex[:10]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            with get_db() as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO crawl_jobs (id, query, status, created_at)
                    VALUES (?, ?, 'completed', ?)
                    """,
                    (job_id, url, now_iso),
                )
                conn.execute(
                    """
                    INSERT INTO crawl_targets (
                        id, job_id, url, domain, status, depth,
                        discovered_at, started_at, completed_at
                    ) VALUES (?, ?, ?, ?, 'completed', 0, ?, ?, ?)
                    """,
                    (target_id, job_id, url, parsed_url.netloc, now_iso, now_iso, now_iso),
                )
                conn.execute(
                    """
                    INSERT INTO pages (
                        id, job_id, target_id, url, status_code,
                        content_type, html_content, title, text_content, created_at
                    ) VALUES (?, ?, ?, ?, ?, 'text/html', ?, ?, ?, ?)
                    """,
                    (
                        page_id,
                        job_id,
                        target_id,
                        url,
                        res.status_code,
                        persisted_html,
                        title,
                        clean_text[:2000],
                        now_iso,
                    ),
                )
        except Exception:
            pass

        # Real-time search engine indexing
        try:
            from growx_crawl.search.indexer import document_indexer
            document_indexer.index_document(
                target_id=target_id,
                url=url,
                html=persisted_html,
                fallback_title=title,
                timestamp=now_iso,
            )
        except Exception:
            pass

        return {
            "status": "success",
            "target_id": target_id,
            "url": url,
            "fetcher_used": res.fetcher_used,
            "escalated": res.escalated,
            "response_metadata": {
                "http_status": res.status_code,
                "latency_ms": res.latency_ms,
                "content_length_bytes": len(res.html),
                "word_count": len(words),
            },
            "data": {
                "title": title,
                "description": description,
                "canonical": canonical,
                "open_graph": {
                    "title": og_title,
                    "description": description,
                    "image": og_image,
                    "type": og_type,
                    "url": canonical,
                },
                "headings": headings,
                "links_count": len(seen_links),
                "links": links[:25],
                "images_count": len(seen_imgs),
                "images": images[:15],
                "stylesheets_count": len(stylesheets),
                "stylesheets": stylesheets[:30],
                "inline_styles_count": len(inline_style_tags),
                "inline_css_chars": total_inline_css_chars,
                "text_preview": clean_text[:800] + ("..." if len(clean_text) > 800 else ""),
            },
        }


scraper_engine = ScraperEngine()
