# Operational Runbook: Database Backup & Recovery

## 1. Backup Strategy
- Automated daily snapshot generated before nightly run.
- Pre-migration backup taken before any database schema migration is executed.
- Backups are stored in `./storage/backups/` and mirrored to cold object storage.

## 2. Generating a Backup
```bash
python scripts/backup_postgres.py
```
Outputs:
- Timestamped dump file: `growx_production_pg_YYYYMMDD_HHMMSS.sql`
- Metadata & SHA-256 integrity file: `*.meta.json`

## 3. Restoring & Verifying a Backup
```bash
# Verify integrity and dry-run restore
python scripts/restore_postgres.py storage/backups/growx_production_pg_20260917_120000.sql
```
Restore process:
1. Validates SHA-256 hash against metadata.
2. Restores into staging/isolated test database.
3. Queries each table to verify row count matching.
