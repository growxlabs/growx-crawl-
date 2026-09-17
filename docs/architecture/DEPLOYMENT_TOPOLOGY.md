# Architecture: Production Deployment Topology

## 1. High-Level Architectural Flow

```
                        GrowxLabs Operators
                                │
                                ▼
               Next.js 14 AutoGTM Product UI (Port 3000)
                     (Clean, Swiss Minimalist UX)
                                │
                                ▼ HTTP / JSON & SSE
                   FastAPI Production Engine (Port 7411)
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
 Canonical PostgreSQL    Cloudflare R2         Persistent Job Queue
 (Supabase Postgres)   (Object Store)        (Lease & Heartbeat Table)
                                                       │
         ┌──────────────────────┬──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼                      ▼
   Crawler Worker        Browser Worker       Intelligence Worker   Verification Worker
   (HTTP Batch)         (Headless Chrome)    (Resolution & Scoring)  (DNS, MX, Citations)
                                                       │
                                                       ▼
                                              Nightly Coordinator
                                            (Scheduled Data Factory)
```

## 2. Core Separation of Responsibilities
1. **Frontend Isolation:** Next.js never executes heavy crawl, AI, or ranking operations.
2. **Persistent Queue Authority:** Work is claimed via atomic leases with heartbeats.
3. **Graceful Worker Degradation:** If browser workers crash, HTTP crawling and scoring continue without degradation.
4. **Structured Canonical Truth:** All company, person, fact, and prospect entities reside in persistent Postgres tables.
5. **Cold Object Persistence:** Raw HTML, rendered DOM, screenshots, and export packages live in Cloudflare R2 with content hashes.
