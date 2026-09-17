# Operational Runbook: Production Deployment

## 1. Scope & Strategy
This document outlines the standard deployment procedure for the **GrowX Crawl & AutoGTM Platform** internal production environment.

## 2. Pre-Deployment Checklist
1. All automated tests pass: `python -m pytest -v` (zero failures across all phases).
2. Next.js production build succeeds: `npm run build` inside `frontend/`.
3. Pre-migration backup created: `python scripts/backup_postgres.py`.
4. Environment variables verified: `GROWX_ENV=production`, `DATABASE_URL` reachable.

## 3. Standard Deployment Flow
```bash
# 1. Pull latest verified commits
git checkout main && git pull origin main

# 2. Acquire migration lock & apply database migrations
python -c "from growx_crawl.storage.migrations.runner import migration_runner; assert migration_runner.acquire_lock(), 'Lock busy'"

# 3. Build & start containers
docker compose -f deploy/docker-compose.yml build
docker compose -f deploy/docker-compose.yml up -d

# 4. Release migration lock
python -c "from growx_crawl.storage.migrations.runner import migration_runner; migration_runner.release_lock()"

# 5. Run production smoke tests
python scripts/smoke_test_production.py
```

## 4. Post-Deployment Verification
- Hit `/health/ready` to verify Postgres pool connectivity.
- Hit `/health/dependencies` to verify all components.
- Check active worker registrations: `GET /v1/ops/workers`.
