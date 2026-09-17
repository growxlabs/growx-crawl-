# Operational Runbook: Secrets Management & Key Rotation

## 1. Secrets Classification & Storage
All production secrets must live strictly in environment variables or cloud secret managers. Never commit secrets to git repositories.

| Secret Name | Purpose | Rotation Frequency |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | 90 days |
| `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | Cloudflare R2 object storage access | 180 days |
| `GROWX_AUTH_JWT_SECRET` | HMAC signature key for internal user tokens | 90 days |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | AI Gateway inference keys | 90 days |
| `GROWX_SERVICE_TOKENS` | Internal service tokens for worker processes | 180 days |

## 2. Key Rotation Procedure
1. Generate new secret value.
2. Update `.env.production` or Cloud Secret Manager.
3. Restart FastAPI engine and worker processes:
   `docker compose -f deploy/docker-compose.yml restart api worker-crawler worker-browser worker-intelligence worker-verification`
4. Confirm health: `GET /health/ready`.
5. Revoke old credentials in provider console.
