# Operational Runbook: Worker Management & Lifecycle

## 1. Overview
GrowX operates 4 dedicated asynchronous worker processes + 1 coordinator:
- `CrawlerWorker` (`growx_crawl.workers.crawler`)
- `BrowserWorker` (`growx_crawl.workers.browser`)
- `IntelligenceWorker` (`growx_crawl.workers.intelligence`)
- `VerificationWorker` (`growx_crawl.workers.verification`)
- `NightlyCoordinator` (`growx_crawl.workers.coordinator`)

## 2. Worker Lifecycle & Heartbeats
- Workers send heartbeats to `workers` table every 20–30s.
- During job execution, the worker renews its lease every 20s.
- If a worker dies without heartbeats for >90s, the supervisor marks it `offline` via `POST /v1/ops/workers/reap`.
- If a worker's job lease expires (>300s), `POST /v1/ops/queue/reclaim` automatically reclaims the task and puts it back in `queued` status.

## 3. Browser Worker Memory Management
- Playwright Chromium processes are recycled every 50 pages or 1GB RAM to eliminate memory leaks.
- If a browser worker crashes, HTTP crawling remains completely unaffected.

## 4. Starting Workers Individually
```bash
# Start crawler worker
python -m growx_crawl.workers.crawler

# Start browser worker
python -m growx_crawl.workers.browser

# Start intelligence worker
python -m growx_crawl.workers.intelligence

# Start verification worker
python -m growx_crawl.workers.verification

# Start nightly coordinator
python -m growx_crawl.workers.coordinator
```
