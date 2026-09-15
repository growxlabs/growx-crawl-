# GrowX Crawl (`growx-crawl`)

Production-grade web scraping API with auto-escalating fetcher modes (fast HTTP, headless browser, stealth), structured data extraction, multi-page crawling, screenshot capture, PDF generation, and full-site SEO audits.

---

## // OVERVIEW

One API, seven capabilities. Single-page scrape with auto-escalating fetcher (fast > dynamic > stealth). CSS/XPath structured extraction. Multi-page crawl (up to 50 pages, 5 levels deep) with async job polling and webhooks. Screenshot capture (PNG/JPEG, full-page). PDF generation (A4/Letter/Legal). Full-site SEO audit. Batch scraping up to 100 URLs in parallel. Cloudflare bypass, proxy support, robots.txt compliance, and response caching built in.

---

## // SPECIFICATIONS

| Dimension | Specification |
| :--- | :--- |
| **Capabilities (7)** | Single-page scrape, CSS/XPath extraction, Multi-page crawl, Batch scrape, Screenshots, PDF generation, SEO audit |
| **Fetcher (3 Modes)** | Fast HTTP (~100ms), Dynamic JS (headless Chromium), Stealth (anti-detection, Cloudflare bypass) |
| **Batch Concurrency**| Up to 100 URLs in parallel with async job polling & webhooks |
| **Crawl Depth** | Up to 50 pages, 5 levels deep |
| **Cache Storage** | In-memory & SQLite cache with configurable TTL |
| **Authentication** | Bearer Token (`Authorization: Bearer gx_live_...`) or `x-api-key` |

---

## // ARCHITECTURE (SCRAPER PIPELINE)

```
       API Request (scrape/crawl/audit)
                      │
                      ▼
          Auth + Rate Limit + Cache
                      │
                      ▼
     ┌─────────────────────────────────┐
     │ Fetcher Selector (auto-escalate)│
     └────────────────┬────────────────┘
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
  [Fast HTTP]    [Dynamic JS]    [Stealth]
    (~100ms)    (Headless Chrome) (Anti-detect)
       └──────────────┬──────────────┘
                      │
                      ▼
       Output (JSON / Webhook / Poll)
```

---

## // RESTful v1 API Reference

### 1. `POST /v1/scrape` (Sampling)
Scrape a single URL and return structured data including title, text, metadata, headings, internal/external links, and images.
```bash
curl -X POST http://127.0.0.1:7411/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "fetcher": "auto"}'
```

### 2. `POST /v1/extract`
CSS & XPath structured extraction with custom selectors.
```bash
curl -X POST http://127.0.0.1:7411/v1/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "selectors": {"title": "h1", "description": "meta[name=\"description\"] @content"}}'
```

### 3. `POST /v1/crawl`
Initiate asynchronous recursive multi-page crawl up to 50 pages.
```bash
curl -X POST http://127.0.0.1:7411/v1/crawl \
  -H "Content-Type: application/json" \
  -d '{"seed_url": "https://example.com", "max_depth": 3, "max_pages": 50}'
```

### 4. `POST /v1/batch`
Parallel batch scraping up to 100 URLs.
```bash
curl -X POST http://127.0.0.1:7411/v1/batch \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://site1.com", "https://site2.com"], "concurrency": 10}'
```

### 5. `POST /v1/screenshot`
Capture full-page or viewport screenshots in PNG or JPEG format.

### 6. `POST /v1/pdf`
Generate publication-grade PDF documents (A4, Letter, Legal).

### 7. `POST /v1/audit/seo`
Full-site technical SEO audit, Core Web Vitals, and AI citation readiness.

### 8. `GET /v1/health`
Real-time health monitor reporting latency, cluster status, and active fetcher engines.

---

## // DEVELOPER CONSOLE & DASHBOARD

Run the local server and web UI:
```bash
python -m uvicorn growx_crawl.web.app:app --host 127.0.0.1 --port 7411
```
Or via CLI:
```bash
growx-crawl dashboard
```
Open **`http://127.0.0.1:7411`** to interact with the Developer Console, inspect all 12 endpoints, and execute live scraping tests directly from the sandbox.
