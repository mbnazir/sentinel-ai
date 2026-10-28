# Sentinel AI v0.13.0 - Local Deployment

## Prerequisites

Install:

- Docker Desktop or Docker Engine with Docker Compose v2
- Git
- Python 3.13 only if you want to run helper scripts directly outside containers
- Network access from the Sentinel host to the Quartz REST endpoint

Recommended local resources:

- 4 CPU cores
- 8 GB RAM minimum
- 15 GB free disk

## 1. Extract the project

```bash
unzip sentinel-ai-milestone-13.zip
cd sentinel-ai
```

## 2. Create the environment file

```bash
cp .env.example .env
```

For local development, edit `.env` and use values similar to:

```env
APP_NAME=Sentinel AI
APP_VERSION=0.13.0
ENVIRONMENT=development
API_V1_PREFIX=/api/v1
DOCS_ENABLED=true
LOG_LEVEL=INFO

POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=sentinel_ai
POSTGRES_USER=sentinel
POSTGRES_PASSWORD=sentinel_local_password

REDIS_URL=redis://redis:6379/0

JWT_SECRET=replace-this-with-a-random-secret-at-least-32-bytes-long
JWT_ALGORITHM=HS256
JWT_ACCESS_MINUTES=480
JWT_AUDIENCE=sentinel-ai-api

CORS_ORIGINS=http://localhost:8080,http://localhost:5173
SECURITY_HEADERS_ENABLED=true

QUARTZ_API_BEARER_TOKEN=replace-with-quartz-read-only-api-token

AI_PROVIDER=disabled
AI_MODEL=gemini-2.5-flash
GEMINI_API_KEY=
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
```

Do not place a production Quartz credential in source control.

## 3. Start the platform

```bash
docker compose up --build -d
```

Services:

- PostgreSQL: internal container
- Redis: internal container
- FastAPI: http://localhost:8000
- React/Nginx dashboard: http://localhost:8080
- Celery worker: background scan processing

Check status:

```bash
docker compose ps
```

Check health:

```bash
curl http://localhost:8000/live
curl http://localhost:8000/ready
```

Expected readiness response:

```json
{
  "status": "ready",
  "dependencies": {
    "postgres": true,
    "redis": true
  }
}
```

## 4. Create a local development access token

The platform does not contain a local username/password store. Generate a development JWT:

```bash
docker compose exec api python -m app.cli.dev_token --role admin
```

If the repository is mounted differently, generate it from the host:

```bash
PYTHONPATH=backend python scripts/create_dev_token.py --role admin
```

Copy the resulting token.

Open:

```text
http://localhost:8080
```

Paste the token into the Sentinel access-token screen.

For command-line calls:

```bash
export SENTINEL_TOKEN='paste-token-here'
```

## 5. Check protected APIs

```bash
curl \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  http://localhost:8000/api/v1/dashboard/scans
```

## 6. Database migrations

The API container runs `alembic upgrade head` automatically at startup.

Manual migration check:

```bash
docker compose exec api alembic current
docker compose exec api alembic heads
```

## 7. Logs

```bash
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f postgres
docker compose logs -f redis
```

## 8. Stop Sentinel

```bash
docker compose down
```

Keep database volumes:

```bash
docker compose down
```

Delete all local Sentinel data:

```bash
docker compose down -v
```

Do not use `-v` if you need to retain investigations, snapshots, or findings.

## 9. Enable AI Investigator - optional

Gemini:

```env
AI_PROVIDER=gemini
AI_MODEL=gemini-2.5-flash
GEMINI_API_KEY=your-key
```

OpenAI-compatible:

```env
AI_PROVIDER=openai
AI_MODEL=your-approved-model
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=https://api.openai.com/v1
```

Restart:

```bash
docker compose up -d --force-recreate api worker
```

The AI Investigator summarizes evidence already stored in Sentinel. It does not generate fraud findings or modify deterministic evidence.

## 10. Local development without Docker for API

Start PostgreSQL and Redis separately, then:

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Worker in another terminal:

```bash
cd backend
source .venv/bin/activate
celery -A app.workers.celery_app.celery_app worker --loglevel=INFO --concurrency=2
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.
