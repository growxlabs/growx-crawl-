# Operational Runbook: Nightly Data Factory Execution

## 1. Schedule & Timing
- Scheduled trigger: 02:00 UTC daily.
- Configured execution window: 6 hours max.
- Target focus: High-priority GTM segments (e.g. `manufacturing_india`, `us_b2b_saas`).

## 2. Pipeline Execution Stages
1. **Planning Stage:** Discovers candidates, applies rate-limiting rules, compiles plan.
2. **Crawl & Discovery Stage:** Fetches authoritative corporate domains and careers pages.
3. **Intelligence & Fact Stage:** Normalizes entities, resolves canonical IDs, supersedes facts.
4. **Verification Stage:** Validates DNS, MX, person employments, and DOM citations.
5. **Quality Gate Stage:** Enforces 0.80+ verification and data completeness criteria.
6. **Competitor & ICP Stage:** Maps competitor graph overlaps and scores prospects against active ICPs.
7. **Ranking Stage:** Computes multi-dimensional scores and emits signed audit explanations.
8. **Summary Stage:** Compiles executive Markdown morning briefing.

## 3. Operations & Controls
- **Trigger Manually:** `POST /v1/data-factory/start` or `python -m growx_crawl.workers.nightly`
- **Pause Pipeline:** Coordinator `pause()` pauses dispatching without killing in-flight tasks.
- **Resume Pipeline:** Coordinator `resume()` resumes task dispatch.
- **Morning Report Inspection:** `GET /v1/data-factory/latest` returns complete executive metrics.
