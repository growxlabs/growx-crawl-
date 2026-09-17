# Operational Runbook: Rollback Procedures

## 1. Fast Rollback (Frontend & API)
If a newly deployed container version fails health checks or introduces regression:

```bash
# 1. Rollback git commit
git checkout HEAD~1

# 2. Re-deploy previous stable container images
docker compose -f deploy/docker-compose.yml build
docker compose -f deploy/docker-compose.yml up -d

# 3. Verify health
python scripts/smoke_test_production.py
```

## 2. Database Schema Rollback
If a schema migration failed mid-way or needs reversion:
1. Ensure migration lock is acquired:
   `python -c "from growx_crawl.storage.migrations.runner import migration_runner; migration_runner.acquire_lock()"`
2. If non-destructive, apply rollback SQL script.
3. If table structure corrupted, restore pre-migration backup:
   `python scripts/restore_postgres.py storage/backups/<pre_migration_backup>.sql`
4. Release migration lock.
