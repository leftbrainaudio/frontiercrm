# FrontierCRM — Local Access

## URLs

| Service | URL |
|---------|-----|
| **Frontend app** | http://localhost:5173/ |
| **API health** | http://localhost:8000/api/health/ |

## Login

| Email | Password | Role |
|---|---|---|
| `demo@frontiercrm.com` | `password123` | Regular user — has all seed data |
| `admin@frontiercrm.com` | `password123` | Admin / Superuser |

## Seed Data

Already loaded. Contains:
- 5 accounts, 10 contacts, 16 deals (across 7 pipeline stages)
- 22 activities, 37 tasks, 10 notes, 6 emails
- Won deals, lost deals, deals in every stage

## Running the servers

```bash
# Backend (port 8000)
cd ~/frontiercrm/backend
DATABASE_URL=sqlite:///db.sqlite3 source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000

# Frontend (port 5173) — needs backend running
cd ~/frontiercrm/frontend
npx vite preview --host 0.0.0.0 --port 5173
```