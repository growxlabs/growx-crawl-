import json
import re
from typing import Any, Dict, List
from bs4 import BeautifulSoup
from growx_crawl.crawler.fetcher import fetcher_pipeline
from growx_crawl.crawler.robots import robots_engine


class SEOAuditor:
    """
    Capability 7: Full-Site Technical SEO & AI Engine Optimization (AEO) Audit Engine.
    Evaluates DOM metadata, schema JSON-LD, content readability, and AI LLM search friendliness.
    """

    async def audit(self, url: str, check_ai_readiness: bool = True) -> Dict[str, Any]:
        res = await fetcher_pipeline.fetch(url, mode="auto", timeout=30)
        soup = BeautifulSoup(res.html, "html.parser")

        scores: List[int] = []
        checks: Dict[str, Any] = {}
        recommendations: List[Dict[str, str]] = []

        # 1. Title check
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        if title and 10 <= len(title) <= 70:
            checks["title"] = {"status": "pass", "value": title, "length": len(title), "score": 100}
            scores.append(100)
        elif title:
            checks["title"] = {
                "status": "warning",
                "value": title,
                "length": len(title),
                "message": "Title length outside optimal range (10-70 characters)",
                "score": 75,
            }
            scores.append(75)
            recommendations.append({"priority": "medium", "issue": "Sub-optimal title length", "fix": "Adjust title to between 10 and 70 characters."})
        else:
            checks["title"] = {"status": "fail", "message": "Missing <title> tag", "score": 0}
            scores.append(0)
            recommendations.append({"priority": "high", "issue": "Missing title tag", "fix": "Add a descriptive <title> tag to the <head>."})

        # 2. Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        desc_text = meta_desc.get("content", "").strip() if meta_desc else ""
        if desc_text and 50 <= len(desc_text) <= 165:
            checks["meta_description"] = {"status": "pass", "value": desc_text, "length": len(desc_text), "score": 100}
            scores.append(100)
        elif desc_text:
            checks["meta_description"] = {
                "status": "warning",
                "value": desc_text,
                "length": len(desc_text),
                "message": f"Description length is {len(desc_text)} chars (recommended: 50-165)",
                "score": 70,
            }
            scores.append(70)
            recommendations.append({"priority": "medium", "issue": "Meta description length", "fix": "Keep description between 50 and 165 characters."})
        else:
            checks["meta_description"] = {"status": "fail", "message": "Missing meta description", "score": 0}
            scores.append(0)
            recommendations.append({"priority": "high", "issue": "Missing meta description", "fix": "Add a <meta name='description'> tag for snippet generation."})

        # 3. Headings Structure (H1, H2, H3)
        h1s = soup.find_all("h1")
        h2s = soup.find_all("h2")
        h3s = soup.find_all("h3")
        if len(h1s) == 1:
            checks["h1_tag"] = {"status": "pass", "value": h1s[0].get_text(strip=True), "score": 100}
            scores.append(100)
        elif len(h1s) > 1:
            checks["h1_tag"] = {"status": "warning", "count": len(h1s), "message": "Multiple H1 tags detected", "score": 80}
            scores.append(80)
            recommendations.append({"priority": "low", "issue": "Multiple H1 headings", "fix": "Use a single primary H1 tag per page."})
        else:
            checks["h1_tag"] = {"status": "fail", "message": "Missing H1 tag", "score": 0}
            scores.append(0)
            recommendations.append({"priority": "high", "issue": "Missing H1 heading", "fix": "Add one clear <h1> heading defining the main topic."})

        checks["heading_counts"] = {"h1": len(h1s), "h2": len(h2s), "h3": len(h3s)}

        # 4. Viewport tag
        viewport = soup.find("meta", attrs={"name": "viewport"})
        checks["mobile_viewport"] = {
            "status": "pass" if viewport else "fail",
            "value": viewport.get("content") if viewport else None,
            "score": 100 if viewport else 0,
        }
        scores.append(100 if viewport else 0)

        # 5. Canonical tag
        canonical = soup.find("link", rel="canonical")
        checks["canonical"] = {
            "status": "pass" if canonical else "warning",
            "value": canonical.get("href") if canonical else None,
            "score": 100 if canonical else 60,
        }
        scores.append(100 if canonical else 60)

        # 6. OpenGraph & Social Cards
        og_title = soup.find("meta", property="og:title")
        og_desc = soup.find("meta", property="og:description")
        og_image = soup.find("meta", property="og:image")
        twitter_card = soup.find("meta", attrs={"name": "twitter:card"})
        og_elements = [el for el in [og_title, og_desc, og_image] if el]
        og_score = 100 if len(og_elements) == 3 else (70 if len(og_elements) >= 1 else 30)
        checks["open_graph"] = {
            "status": "pass" if og_score == 100 else "warning",
            "has_og_title": bool(og_title),
            "has_og_description": bool(og_desc),
            "has_og_image": bool(og_image),
            "has_twitter_card": bool(twitter_card),
            "score": og_score,
        }
        scores.append(og_score)

        # 7. Images alt attribute audit
        images = soup.find_all("img")
        missing_alt = [img for img in images if not img.get("alt")]
        img_score = 100 if not missing_alt else max(20, int((1 - len(missing_alt) / max(len(images), 1)) * 100))
        checks["image_alt_tags"] = {
            "status": "pass" if not missing_alt else "warning",
            "total_images": len(images),
            "missing_alt_count": len(missing_alt),
            "score": img_score,
        }
        scores.append(img_score)
        if missing_alt:
            recommendations.append({"priority": "medium", "issue": f"{len(missing_alt)} images missing alt text", "fix": "Add descriptive alt attributes for accessibility and image search."})

        # 8. Robots Directives
        meta_robots = soup.find("meta", attrs={"name": "robots"})
        robots_content = meta_robots.get("content", "").lower() if meta_robots else "index, follow"
        is_indexable = "noindex" not in robots_content
        checks["robots_meta"] = {
            "status": "pass" if is_indexable else "warning",
            "directives": robots_content,
            "indexable": is_indexable,
            "score": 100 if is_indexable else 50,
        }
        scores.append(100 if is_indexable else 50)

        # 9. AI Citation & LLM Search Readiness (AEO)
        ai_readiness = {}
        if check_ai_readiness:
            # Detect JSON-LD structured data schemas
            schema_scripts = soup.find_all("script", type="application/ld+json")
            schema_types = []
            for sc in schema_scripts:
                try:
                    data = json.loads(sc.string or "{}")
                    if isinstance(data, dict):
                        schema_types.append(data.get("@type", "Thing"))
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                schema_types.append(item.get("@type", "Thing"))
                except Exception:
                    pass

            text_str = " ".join(soup.get_text().split())
            word_count = len(text_str.split())

            # Detect FAQ patterns (questions in H2/H3 or schema)
            questions_in_headings = [h.get_text(strip=True) for h in (h2s + h3s) if h.get_text(strip=True).endswith("?")]
            has_faq_patterns = len(questions_in_headings) > 0 or "FAQPage" in schema_types

            # Structured lists/tables count
            tables_count = len(soup.find_all("table"))
            lists_count = len(soup.find_all(["ul", "ol"]))

            # Calculate AEO score
            aeo_factors = 0
            if schema_types:
                aeo_factors += 35
            if word_count >= 500:
                aeo_factors += 25
            elif word_count >= 200:
                aeo_factors += 15
            if has_faq_patterns:
                aeo_factors += 20
            if (tables_count + lists_count) > 0:
                aeo_factors += 20

            ai_readiness = {
                "aeo_score": min(100, aeo_factors),
                "ai_search_friendliness": "Optimal" if aeo_factors >= 75 else ("Moderate" if aeo_factors >= 50 else "Limited"),
                "has_structured_data": len(schema_types) > 0,
                "detected_schemas": list(set(schema_types)),
                "word_count": word_count,
                "faq_patterns_detected": len(questions_in_headings),
                "data_tables_count": tables_count,
                "content_lists_count": lists_count,
                "llm_citation_potential": "High" if aeo_factors >= 75 and word_count >= 400 else "Standard",
            }
            scores.append(min(100, aeo_factors))

        overall_score = sum(scores) // len(scores) if scores else 85

        return {
            "status": "success",
            "url": url,
            "overall_score": overall_score,
            "rating": "Excellent" if overall_score >= 90 else ("Good" if overall_score >= 70 else "Needs Improvement"),
            "latency_ms": res.latency_ms,
            "checks": checks,
            "ai_readiness": ai_readiness,
            "recommendations": recommendations,
        }


seo_auditor = SEOAuditor()
