# Operational Runbook: Incident Triage & Disaster Recovery

## 1. Outage Scenarios & Recovery Priorities

```
Priority Order:
1. Postgres Database Connectivity
2. FastAPI Product Engine
3. Dedicated Workers
4. Nightly Data Factory Run
5. Next.js Frontend UI
```

## 2. Specific Failure Playbooks

### A. Database Unreachable
1. Check container/host status: `docker ps | grep postgres`.
2. Inspect logs: `docker logs growx-postgres --tail 100`.
3. Check connection pool metrics: `GET /health/ready`.
4. If corrupt, restore latest verified backup via `python scripts/restore_postgres.py <backup_file>`.

### B. Worker Queue Stuck (>10 min backlog)
1. Inspect queue depth: `GET /v1/ops/queue`.
2. Check worker heartbeats: `GET /v1/ops/workers`.
3. Force-reap offline workers: `POST /v1/ops/workers/reap`.
4. Force-reclaim abandoned leases: `POST /v1/ops/queue/reclaim`.

### C. Browser Worker Crash
- Browser crashes do NOT affect HTTP crawling.
- Browser worker container restarts automatically under Docker compose.
- Failed screenshot/render jobs are automatically retried up to 3 times.

### D. External AI Provider Outage
- GrowX degrades gracefully: deterministic entity resolution, rule-based ICP evaluation, and ranking continue without interruption.
- AI-assisted enrichment tasks remain in `retrying` status until provider connectivity resumes.

### E. Cloudflare R2 Object Storage Unreachable
- Artifact writes fail safe; jobs mark error and retry.
- Raw DOM snapshots are cached locally on worker ephemeral disk until R2 endpoint recovers.
