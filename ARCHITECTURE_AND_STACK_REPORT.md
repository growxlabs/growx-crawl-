# GrowX Crawl & AutoGTM Platform
## Enterprise System Architecture, Repository Blueprint & Technology Stack Report

**Generated:** September 17, 2026  
**Platform Version:** 1.2.0-PROD  
**Author:** GrowX Labs Engineering Team (`engineering@growxlabs.tech`)  
**Repository:** `https://github.com/growxlabs/growx-crawl-.git`  
**License:** Proprietary / MIT Hybrid  

---

## Executive Summary

**GrowX Crawl** is a high-performance, enterprise-grade **Autonomous Web Intelligence and Go-To-Market (AutoGTM) Engine**. Built as a high-margin **SWAS (Software-with-a-Service)** platform, it solves the fatal flaw of traditional sales databases (Apollo, ZoomInfo, Explee)—which suffer from 30%–40% stale data and high email bounce rates—by harvesting **Live Web Truth** directly from active websites, corporate registries, and live search engines in real time.

### Core Value Propositions
1. **Live Web Truth over Stale Databases:** Deep multi-page crawling extracts live facts (tech stack, hiring signals, recent announcements, pricing tiers) to ground every outreach sequence in verifiable evidence.
2. **Auto-Escalating Evasion & Stealth:** 3-tier fetcher cluster (Fast HTTP &rarr; Headless Playwright &rarr; Camoufox/Chromium Ghost Stealth with Cloudflare Turnstile bypass).
3. **Built-in Self-Hosted Search Engine:** High-speed SQLite FTS5 full-text indexing with BM25 ranking and snippet highlighting.
4. **Zero-Cost Email Verification:** Asynchronous DNS-over-HTTPS (DoH) MX lookup and socket-level SMTP deliverability verification without external API fees.
5. **Turnkey SWAS Client Engine:** Powers end-to-end B2B sales pipeline generation, BDE briefing dossiers, and automated multi-channel copy generation (Email, LinkedIn, Twitter/X).

---

## 1. Complete Repository Tree Structure

Below is the directory map of the entire GrowX Crawl codebase, detailing the purpose and responsibility of every package and file:

```text
c:\growxlabs\growx-crawl\
├── .env.example                     # Environment template (API keys, ports, secrets)
├── .gitignore                       # Production gitignore (locks DBs, data/, caches, env)
├── ARCHITECTURE_AND_STACK_REPORT.md # Master System Architecture & Stack Report
├── README.md                        # Project documentation & quickstart guide
├── pyproject.toml                   # Project metadata, packaging, dependencies, pytest config
├── growx-crawl.bat / .cmd           # Windows quick-launch scripts
│
├── config/                          # Configuration presets & system profiles
│   └── (industry configs, scoring weights, seed definitions)
│
├── data/                            # Persistent SQLite database storage (WAL mode)
│   └── growx-crawl.db               # SQLite database with FTS5 tables & foreign keys
│
├── exports/                         # Exported client deliverables (Excel .xlsx, CSV, JSON)
│
├── src/growx_crawl/                 # Primary Application Source Code
│   ├── __init__.py                  # Root package initializer
│   │
│   ├── agent/                       # Autonomous Multi-Step Agent Runtime
│   │   ├── __init__.py
│   │   ├── runtime.py               # Autonomous goal planner and execution loop
│   │   ├── tools.py                 # Tool interfaces exposed to the agent (crawl, extract, verify)
│   │   └── models/                  # Agent state and action schemas
│   │
│   ├── api/v1/                      # Production REST & Streaming API Routers
│   │   ├── __init__.py
│   │   ├── router.py                # Core v1 API (Scrape, Extract, Crawl, Batch, Screenshot, PDF, SEO, Search)
│   │   └── ops_router.py            # RBAC Ops API (Session auth, Key management, DB stats, Logs, Engine state)
│   │
│   ├── autogtm/                     # AutoGTM Autonomous Pipeline (Explee-Killer Engine)
│   │   ├── __init__.py              # AutoGTM exports
│   │   ├── models.py                # Pydantic models (CompanyAnalysis, ICPProfile, ProspectLead, OutreachSequence)
│   │   ├── analyzer.py              # Multi-page website analyzer & tech stack extractor
│   │   ├── icp.py                   # Ideal Customer Profile synthesizer & search dork builder
│   │   ├── prospector.py            # Live prospect discovery & decision-maker harvester
│   │   ├── verifier.py              # Zero-cost DoH MX resolver & SMTP socket deliverability tester
│   │   ├── copywriter.py            # Multi-channel personalized sales copy generator (Poke method / Hormozi)
│   │   └── pipeline.py              # End-to-end AutoGTM orchestrator with real-time SSE progress
│   │
│   ├── cli/                         # Command-Line Interface (Typer / Rich)
│   │   ├── __init__.py
│   │   └── main.py                  # CLI commands: `growx-crawl scrape`, `crawl`, `search`, `export`
│   │
│   ├── core/                        # Core Infrastructure, Security & Configuration
│   │   ├── auth.py                  # API Key manager, HMAC hashing, rate-limiting, tier checks
│   │   ├── ops_auth.py              # Secure Ops Authentication (Locked to sai@growxlabs.tech)
│   │   ├── cache.py                 # In-memory LRU cache with TTL for ultra-fast response times
│   │   ├── config.py                # Pydantic Settings management (.env loader)
│   │   ├── enums.py                 # System-wide enums (LeadStage, FetcherType, ReviewStatus)
│   │   ├── industry.py              # Industry taxonomy & profile registry
│   │   └── location.py              # Geographic canonicalization & coordinate resolver
│   │
│   ├── crawler/                     # Multi-Tier Crawling & Fetching Engine
│   │   ├── base.py                  # Abstract base crawler interface
│   │   ├── fetcher.py               # Auto-escalating fetcher (Fast HTTP -> Playwright Dynamic with full CSS)
│   │   ├── http_crawler.py          # Lightweight high-speed HTTPX crawler
│   │   ├── browser_crawler.py       # Playwright browser controller for dynamic JS apps
│   │   ├── multi_page.py            # Recursive BFS/DFS website crawler with depth controls
│   │   ├── batch.py                 # Concurrency-limited batch scraping engine
│   │   ├── scraper.py               # Single-page scraper with <base href> stylesheet preservation
│   │   ├── screenshot.py            # Full-page high-DPI visual capture engine
│   │   ├── pdf.py                   # Clean A4 print PDF document generator
│   │   ├── seo_audit.py             # Technical SEO, Core Web Vitals & AI-Readiness auditor
│   │   ├── robots.py                # Asynchronous robots.txt compliance evaluator
│   │   ├── politeness.py            # Domain rate-limiting & delay coordinator
│   │   ├── proxies.py               # Proxy rotation & health monitoring pool
│   │   ├── page_classifier.py       # Semantic page classifier (About, Team, Pricing, Contact, Blog)
│   │   ├── page_discoverer.py       # Sitemap.xml & DOM link extractor
│   │   └── stealth/                 # Anti-Bot & Fingerprint Evasion Subsystem
│   │       ├── behavior.py          # Humanized mouse jitter, curves, and natural scroll dynamics
│   │       ├── fingerprint.py       # Canvas, WebGL, AudioContext & WebRTC spoofing
│   │       ├── ghost.py             # Camoufox & Chromium ghost runner with font rendering
│   │       ├── solver.py            # Heuristic challenge solver
│   │       ├── turnstile.py         # Cloudflare Turnstile automated solver
│   │       └── warmer.py            # Cookie & session pre-warming engine
│   │
│   ├── dedupe/                      # Deduplication & Entity Resolution
│   │   ├── __init__.py
│   │   └── engine.py                # Fuzzy string matching, domain normalization, phone & name deduplication
│   │
│   ├── discovery/                   # Lead Discovery & Seed Ingestion Providers
│   │   ├── base.py                  # Base provider interface
│   │   ├── registry.py              # Provider registry & health check coordinator
│   │   ├── directory.py             # Web business directory scraper
│   │   ├── maps.py                  # Google Maps / Local business harvester
│   │   ├── search.py                # Search engine dorking provider
│   │   ├── seed_file.py             # CSV / XLSX bulk seed importer
│   │   ├── expander.py              # Query expansion engine for high-recall harvesting
│   │   └── url_classifier.py        # Machine learning / heuristic URL router
│   │
│   ├── enrichment/                  # Deep Enrichment & Sales Intelligence
│   │   ├── __init__.py
│   │   ├── enricher.py              # Company & contact data enricher
│   │   ├── ai_enricher.py           # LLM-assisted enrichment engine
│   │   └── bde_brief.py             # 1-Page actionable BDE sales briefing generator
│   │
│   ├── events/                      # Real-Time Event Streaming (SSE)
│   │   ├── __init__.py
│   │   ├── models.py                # CrawlEvent, JobStatusEvent schemas
│   │   └── broadcaster.py           # Pub/Sub event broadcaster for live browser progress
│   │
│   ├── exporters/                   # Client-Ready Delivery Exporters
│   │   ├── __init__.py
│   │   ├── xlsx.py                  # Styled multi-tab Excel exporter with executive styling
│   │   ├── csv_exporter.py          # High-performance CSV streaming exporter
│   │   └── json_exporter.py         # Formatted JSON lead dossier exporter
│   │
│   ├── extractors/                  # Specialized Content & Metadata Extractors
│   │   ├── base.py                  # Extractor protocol
│   │   ├── structured.py            # CSS / XPath selector extraction engine
│   │   ├── schema_org.py            # JSON-LD & Microdata schema parser
│   │   ├── company.py               # Company name, registration, and logo extractor
│   │   ├── contact.py               # Contact person, executive name & title extractor
│   │   ├── email.py                 # Regex & mailto: email harvester
│   │   ├── phone.py                 # E.164 international phone number normalizer
│   │   ├── address.py               # Street address, city, state, postal code parser
│   │   ├── social.py                # LinkedIn, Twitter/X, GitHub, Instagram link harvester
│   │   └── digital_presence.py      # Website health, responsiveness & tech stack detector
│   │
│   ├── integrations/                # External Systems & CRM Bridges
│   │   ├── __init__.py
│   │   ├── client.py                # Asynchronous webhook dispatcher
│   │   ├── dto.py                   # Data Transfer Object validation schemas
│   │   ├── growxlabs.py             # Native GrowX Labs CRM sync bridge
│   │   └── validator.py             # Outbound payload security & integrity validator
│   │
│   ├── jobs/                        # Orchestration & Job Engine
│   │   ├── __init__.py
│   │   └── engine.py                # CrawlJobEngine coordinator for multi-worker tasks
│   │
│   ├── models/                      # Database & Domain Pydantic Schemas
│   │   ├── __init__.py
│   │   ├── job.py                   # CrawlJob, JobConfig, JobStats
│   │   ├── lead.py                  # Company, Lead, ContactPerson, LeadCandidate
│   │   ├── target.py                # Target, TargetPage, TargetContent
│   │   ├── page.py                  # ScrapedPage, DOMSnapshot
│   │   ├── discovery.py             # DiscoveryResult, SeedRecord
│   │   └── enrichment.py            # EnrichedProfile, IntelligenceBrief
│   │
│   ├── normalization/               # Data Cleaning & Canonicalization
│   │   ├── __init__.py
│   │   └── normalizer.py            # Company name cleaning, phone formatting, URL canonicalization
│   │
│   ├── scoring/                     # Lead Qualification & Prioritization
│   │   ├── __init__.py
│   │   └── scorer.py                # ICP match score, data completeness score, BDE priority tiering
│   │
│   ├── search/                      # Self-Hosted Web Search Engine
│   │   ├── __init__.py
│   │   ├── engine.py                # SearchEngine controller with query routing
│   │   ├── schema.py                # SQLite FTS5 table initialization (`search_index`, `search_documents`)
│   │   ├── indexer.py               # High-throughput HTML tokenizer & document indexer
│   │   ├── query.py                 # Query parser supporting domain: filters and quoted phrases
│   │   └── ranker.py                # BM25 relevance ranker + inbound link graph scoring
│   │
│   ├── storage/                     # Persistence & Database Access Layer
│   │   ├── __init__.py
│   │   ├── db.py                    # Thread-safe SQLite connection factory with WAL mode
│   │   ├── schema.py                # Complete relational schema (11 tables + triggers + indexes)
│   │   └── repository.py            # Repositories for Jobs, Leads, Targets, Keys, Errors, Agent runs
│   │
│   ├── utils/                       # Shared Helpers
│   │   ├── __init__.py
│   │   └── logger.py                # Structured console & file logging with color formatting
│   │
│   ├── web/                         # Web Server & User Interfaces
│   │   ├── app.py                   # FastAPI Application initialization, route mounting, middleware
│   │   └── static/                  # Production Frontend Web Assets
│   │       ├── index.html           # Enterprise Crawl & Lead Management Console
│   │       ├── landing.html         # High-Converting AutoGTM & API Landing Page
│   │       ├── ops.html             # High-Security Ops & System Control Center
│   │       ├── app.js               # Reactive single-page application controller
│   │       └── style.css            # Custom cyber-dark design system
│   │
│   └── workers/                     # Asynchronous Concurrency Pools
│       ├── __init__.py
│       └── pool.py                  # Dynamic worker pool with adaptive backoff
│
└── tests/                           # Comprehensive Test Suite (73 Tests, 100% Passing)
    ├── fixtures/                    # Mock HTML pages, seeds, team pages
    ├── test_css_crawling.py         # Full-page CSS stylesheet capture & snapshot rendering tests
    ├── test_search_engine.py        # FTS5 search, BM25 ranking & query parsing tests
    ├── test_v1_engine.py            # Scrape, extract, batch, screenshot, PDF, SEO audit tests
    ├── test_ops_security.py         # RBAC authentication, session protection & key management tests
    ├── test_agent_runtime.py        # Autonomous agent loop tests
    ├── test_dedupe.py               # Entity resolution & deduplication tests
    ├── test_deep_enrichment.py      # BDE Brief & AI enrichment tests
    ├── test_discovery_providers.py  # Maps & directory discovery tests
    ├── test_extractors.py           # Email, phone, address, schema.org extractor tests
    ├── test_job_engine.py           # Multi-worker job orchestration tests
    ├── test_live_streaming.py       # SSE event broadcast tests
    ├── test_normalizer.py           # Canonicalization tests
    ├── test_scoring.py              # Lead scoring algorithm tests
    ├── test_stealth.py              # Fingerprint & anti-bot tests
    ├── test_storage.py              # SQLite WAL concurrency tests
    ├── test_visual_engines.py       # Screenshot & PDF generation tests
    └── test_web_dashboard.py        # Web router & dashboard API tests
```

---

## 2. System Architecture & Component Interactions

```
                            EXTERNAL INBOUND TRAFFIC
                                       │
                 ┌─────────────────────┴─────────────────────┐
                 ▼                                           ▼
      [HTTPS REST API Clients]                    [Browser Web Clients]
     curl / Python / Node SDK                    Landing / Console / Ops
                 │                                           │
                 └─────────────────────┬─────────────────────┘
                                       │
                                       ▼
    ┌────────────────────────────────────────────────────────────────────────┐
    │                       FASTAPI APPLICATION CORE                         │
    │  • HMAC-SHA256 API Key Verification                                    │
    │  • Session-based Ops RBAC (sai@growxlabs.tech)                         │
    │  • In-Memory LRU Cache (<10ms cache hits)                              │
    │  • Rate Limiting & Quota Management                                    │
    └───────────────────┬───────────────────────────────┬────────────────────┘
                        │                               │
                        ▼                               ▼
    ┌──────────────────────────────────────┐  ┌──────────────────────────────┐
    │     CORE CRAWL & SEARCH ENGINE       │  │    AUTOGTM REVENUE PIPELINE   │
    │  • Single-Page Scraper (Fast/JS)     │  │  • Domain Deep Crawl          │
    │  • Full CSS Stylesheet Extraction    │  │  • Offer & Tech Synthesis     │
    │  • Multi-Page Recursive Crawl        │  │  • ICP & Buyer Persona Matrix │
    │  • Visual Screenshot & Print PDF     │  │  • Live Prospect Harvester    │
    │  • Technical SEO & AI Readiness      │  │  • Zero-Cost DoH MX Verifier  │
    │  • FTS5 BM25 Full-Text Search        │  │  • Multi-Channel Copywriter   │
    └───────────────────┬──────────────────┘  └──────────────┬───────────────┘
                        │                                    │
                        └───────────────────┬────────────────┘
                                            │
                                            ▼
    ┌────────────────────────────────────────────────────────────────────────┐
    │                   AUTO-ESCALATING FETCHER CLUSTER                      │
    │                                                                        │
    │  Tier 1: Fast HTTPX Fetcher      ──> <100ms latency for static pages   │
    │  Tier 2: Playwright Headless    ──> Full JS execution, dynamic CSS     │
    │  Tier 3: Ghost Camoufox Stealth  ──> Cloudflare Turnstile, Fingerprints│
    └───────────────────────────────────────┬────────────────────────────────┘
                                            │
                                            ▼
    ┌────────────────────────────────────────────────────────────────────────┐
    │                    STORAGE & PERSISTENCE LAYER                         │
    │  SQLite 3 (WAL Mode + FTS5 Indexing + Memory-Mapped I/O)               │
    │  • Targets & Page Snapshots (<base href> preserved)                   │
    │  • Crawl Jobs & Event History                                          │
    │  • Qualified B2B Leads & BDE Intelligence Briefs                       │
    │  • API Keys, Audit Logs & System Metrics                               │
    └───────────────────────────────────────┬────────────────────────────────┘
                                            │
                 ┌──────────────────────────┴──────────────────────────┐
                 ▼                                                     ▼
      [Client Delivery Exporters]                            [Real-Time SSE Stream]
     Excel .xlsx / CSV / Lead Dossier                       Live Browser Feedback
```

---

## 3. Features Implemented Up to Now

### Capability 1: High-Speed Web Scraper (`POST /v1/scrape`)
- **Latency:** Fast HTTP mode operates at `<100ms`; dynamic browser mode operates at `1.2s–2.5s`.
- **Full-Page CSS Fidelity:** Waits for `document.fonts.ready` and extracts all `<link rel="stylesheet">` elements and inline `<style>` tags.
- **Snapshot Preservation:** Injects `<base href="{url}">` into stored HTML snapshots, ensuring offline preview without broken stylesheets or images.
- **Live Preview Endpoint:** `GET /v1/targets/{id}/preview` serves rendered DOM snapshots with full styles.

### Capability 2: Structured Selector Extraction (`POST /v1/extract`)
- Accepts arbitrary CSS and XPath selector dictionaries.
- Extracts single elements, collections, attributes, and inner text.
- Supports extracting directly from previously crawled snapshots via `POST /v1/extract-from-target`.

### Capability 3: Deep Multi-Page Recursive Crawling (`POST /v1/crawl`)
- Configurable recursion depth (1 to 10) and page caps (up to 1,000 pages per job).
- Intelligent URL prioritization: discovers sitemaps (`/sitemap.xml`) and prioritizes `/about`, `/team`, `/pricing`, `/contact`, and `/products`.
- Respects `robots.txt` compliance rules on demand.

### Capability 4: Concurrency-Controlled Batch Scraping (`POST /v1/batch`)
- Dispatches hundreds of target URLs across an asynchronous worker pool.
- Automatic rate-limiting and domain politeness to prevent IP throttling.
- Optional webhook notifications upon batch completion.

### Capability 5 & 6: Visual Screenshot & Print PDF Engines
- **Screenshot (`POST /v1/screenshot`):** Full-page and viewport captures in PNG or JPEG with high-DPI retina emulation.
- **PDF (`POST /v1/pdf`):** Standard A4 print PDFs with background colors and stylesheets enabled.

### Capability 7: Technical SEO & AI-Readiness Audit (`POST /v1/seo-audit`)
- Evaluates title, meta tags, OpenGraph, Canonical URLs, and H1/H2 heading hierarchy.
- **AI-Readiness Score (0–100):** Evaluates semantic markup, Schema.org JSON-LD presence, text-to-code ratio, and accessibility for LLM scrapers.

### Capability 8: Self-Hosted Web Search Engine (`GET /v1/search`)
- Built-in full-text search powered by SQLite FTS5.
- BM25 relevance ranking weighted by domain (3.0), title (12.0), description (5.0), and body text (1.0).
- Automatic snippet extraction with keyword highlighting.
- Supports domain-specific queries (e.g. `domain:growxlabs.tech crawler`).

### Capability 9: AutoGTM Engine (Explee-Killer)
- **Deep Domain Analysis (`analyzer.py`):** Scrapes client homepage, pricing, and product subpages. Detects tech stack signatures (Stripe, Shopify, React, Next.js, HubSpot).
- **ICP Synthesis (`icp.py`):** Synthesizes target industries, company employee tiers, buyer roles, pain points, and formulated Google/Bing search dorks.
- **Live Prospect Harvesting (`prospector.py`):** Finds active decision-makers matching the ICP and extracts live website facts as personalization hooks.
- **Zero-Cost Email Verifier (`verifier.py`):** Cloudflare & Google DNS-over-HTTPS (DoH) MX checks + socket-level SMTP handshake deliverability test.
- **Multi-Channel Copywriter (`copywriter.py`):** Generates 3-step cold email sequences, LinkedIn connection notes (<300 chars), and Twitter/X DMs grounded in crawled facts.

### Capability 10: High-Security Operations Portal (`/ops`)
- Restricted access locked exclusively to `sai@growxlabs.tech`.
- Secure session authentication with SHA-256 password verification and cookie validation.
- Live database diagnostics, API key creation, system metrics, and audit log inspection.

---

## 4. Technology Stack & Specifications

| Layer | Technology | Rationale & Specifications |
| :--- | :--- | :--- |
| **Language & Runtime** | **Python 3.12 / 3.14 (64-bit)** | Native asynchronous event loop, modern typing, performance optimizations. |
| **API Framework** | **FastAPI + Uvicorn** | Asynchronous ASGI framework, sub-millisecond route handling, native OpenAPI docs. |
| **Browser Automation** | **Playwright + Camoufox** | Anti-bot evasion, stealth browser fingerprinting, full dynamic CSS & JS rendering. |
| **HTML & DOM Parsing** | **BeautifulSoup4 + lxml** | High-speed C-based parsing engine for complex DOM trees. |
| **Database Engine** | **SQLite 3 (WAL Mode)** | Zero external database overhead, Write-Ahead Logging for concurrent reads, FTS5 full-text search. |
| **HTTP & Networking** | **HTTPX (Async)** | Asynchronous HTTP/1.1 and HTTP/2 client with connection pooling and proxy support. |
| **DNS Resolution** | **DNS-over-HTTPS (DoH)** | Cloudflare & Google DoH via HTTPS (port 443). Eliminates UDP port 53 firewall restrictions. |
| **Export Engines** | **openpyxl** | Generates styled, multi-tab Excel reports with formatting and formulas for executive delivery. |
| **Frontend Architecture** | **Vanilla ES6+ JS & CSS3** | Zero heavy frontend frameworks (no React/Vue bundle overhead). Lightning-fast page load times. |
| **Security & Cryptography**| **hashlib (SHA-256) + secrets** | Constant-time string comparisons, cryptographically secure API keys, and session tokens. |

---

## 5. Blueprint for Scaling to High-Throughput Enterprise

To scale GrowX Crawl from its current single-server footprint to millions of daily crawls:

```
                                SCALE ARCHITECTURE
                                
                               [Cloudflare / CDN]
                                       │
                                       ▼
                       [Load Balancer / Reverse Proxy]
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           ▼                           ▼                           ▼
    [GrowX Node 1]              [GrowX Node 2]              [GrowX Node 3]
     FastAPI Web                 FastAPI Web                 FastAPI Web
           │                           │                           │
           └───────────────────────────┼───────────────────────────┘
                                       │
                                       ▼
                      [Redis / Dragonfly Job Queue]
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           ▼                           ▼                           ▼
    [Crawler Worker 1]          [Crawler Worker 2]          [Crawler Worker 3]
    Playwright Pool             Playwright Pool             Playwright Pool
    Residential Proxies         Residential Proxies         Residential Proxies
                                       │
                                       ▼
                     [PostgreSQL / SQLite WAL Replicas]
```

1. **Proxy Pool Scaling:** Integrate rotating residential and mobile proxy pools (e.g., Bright Data, Oxylabs, Webshare) to bypass geo-restrictions and rate-limits.
2. **Distributed Queue:** Decouple long-running crawl jobs via Redis or Dragonfly queue workers.
3. **Multi-Tenant Concierge Dashboard:** Allow SWAS clients to log into dedicated white-labeled dashboards displaying their booked meetings, live crawled prospects, and active outreach sequences.

---
*GrowX Labs Confidential — For Internal Architecture & Scaling Strategy.*
