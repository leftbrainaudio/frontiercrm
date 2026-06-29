# Developer Setup Guide — FrontierCRM

Set up a local development environment for FrontierCRM. These steps assume macOS or Linux.

## Prerequisites

| Tool | Version | Required for |
|------|---------|-------------|
| Python | 3.11 | Backend |
| Node.js | 22 | Frontend |
| Docker | latest | PostgreSQL, Redis, Meilisearch |
| Docker Compose | v2 | Orchestrating services |

## 1. Clone the repo

```bash
git clone <repo-url> frontiercrm
cd frontiercrm
```

## 2. Start infrastructure services

```bash
cd backend
docker compose up -d db redis meilisearch
```

Expected output (abbreviated):

```
[+] Running 4/4
 ✔ Container backend-db-1          Started
 ✔ Container backend-redis-1       Started
 ✔ Container backend-meilisearch-1 Started
```

Verify:

```bash
docker compose ps
```

Output:

```
NAME                          STATUS
backend-db-1                  Up (healthy)
backend-redis-1               Up (healthy)
backend-meilisearch-1         Up (healthy)
```

## 3. Backend setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Copy the environment file:

```bash
cp .env.example .env
```

Default `.env` values work for local development. Key defaults:

| Variable | Default | Notes |
|----------|---------|-------|
| DJANGO_DEBUG | True | Enables tracebacks and dev toolbar |
| DATABASE_URL | postgresql://postgres:***@localhost:5432/frontiercrm | Docker postgres |
| REDIS_URL | redis://localhost:6379/1 | Docker redis |
| MEILISEARCH_URL | http://localhost:7700 | Docker meilisearch |
| MEILISEARCH_API_KEY | masterKey | Docker default |

Run migrations and seed data:

```bash
python manage.py migrate --noinput
```

Expected output:

```
Operations to perform:
  Apply all migrations: accounts, activities, contacts, email, files, notes, pipelines, tasks, teams, webhooks
Running migrations:
  Applying <app>_0001_initial... OK
  ... (all migrations applied)
```

```bash
python manage.py createsuperuser
# Follow prompts for email, username, password
```

Start the dev server:

```bash
DJANGO_SETTINGS_MODULE=config.settings.development \
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --reload
```

Or with hot-reload (dev):

```bash
python manage.py runserver 0.0.0.0:8000
```

Verify:

```bash
curl -s http://localhost:8000/api/health/
```

Output:

```json
{"status":"ok","service":"frontiercrm-api"}
```

## 4. Frontend setup

```bash
cd frontend
npm ci
```

Start the dev server:

```bash
npm run dev
```

Expected output:

```
  VITE v8.x.x  ready in 123ms
  ➜  Local:   http://localhost:5173/
  ➜  Network: http://0.0.0.0:5173/
```

Open http://localhost:5173/ in your browser. Sign up or log in.

## 5. Celery workers (optional — for email sync, search indexing, backups)

```bash
cd backend
source venv/bin/activate

# Start worker
celery -A config worker -l info --concurrency=4

# In a second terminal, start beat scheduler
celery -A config beat -l info
```

## 6. Running tests

### Backend

```bash
cd backend
source venv/bin/activate

# All tests
pytest

# With coverage
pytest --cov --cov-report=term

# Single test file
pytest tests/test_contacts_api.py -v

# Run tests matching a keyword
pytest -k "deal" -v
```

Expected output:

```
======================================== short test summary info =========================================
PASSED ... 411 passed in 15.2s
```

### Frontend

```bash
cd frontend
npm test
```

## 7. Docker Compose (full stack)

For a complete local environment without installing anything besides Docker:

```bash
cd backend
docker compose up --build
```

This starts: API (gunicorn, port 8000), Celery worker, Celery beat, PostgreSQL, Redis, Meilisearch.

## 8. Linting

```bash
# Backend
cd backend && source venv/bin/activate && ruff check .

# Frontend
cd frontend && npm run lint
```

## Common issues

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `connection refused` on :5432 | Postgres not running | `docker compose up -d db` |
| `relation does not exist` | Migrations not run | `python manage.py migrate` |
| `ModuleNotFoundError` | venv not activated | `source venv/bin/activate` |
| 401 on API calls | Token expired or missing | Log out and log in again |
| Meilisearch returning 0 results | Index not built | Run `python manage.py reindex_meilisearch` |
| `pg_isready` fails on M1 Mac | Rosetta issue | Use `platform: linux/amd64` in docker compose |

## Environment variables reference

Full list in `backend/config/settings/base.py`. Required variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DJANGO_SECRET_KEY | Yes | dev-secret-key-change-in-production | Django secret key |
| DATABASE_URL | Yes | (Docker compose default) | PostgreSQL connection string |
| REDIS_URL | No | redis://localhost:6379/1 | Redis cache URL |
| CELERY_BROKER_URL | No | redis://localhost:6379/0 | Celery broker |
| MEILISEARCH_URL | No | http://localhost:7700 | Search service |
| CORS_ALLOWED_ORIGINS | No | http://localhost:5173,... | CORS origins |

## WebSocket support

The API supports WebSocket connections via Django Channels. In production, these run on the same port as HTTP. No separate WebSocket server is needed.

```bash
# Connect from browser dev console
const ws = new WebSocket('ws://localhost:8000/ws/notifications/');
ws.onmessage = (event) => console.log(event.data);
```