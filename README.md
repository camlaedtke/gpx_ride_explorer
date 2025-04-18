# AI-Bike-Coach Platform

## Overview
A full-stack, cloud-hosted platform for cyclists that syncs Strava rides, computes analytics (TSS, CTL/ATL/TSB, PRs), and provides a Streamlit UI and AI chat agent.

## Features
- Strava OAuth + webhook sync to TimescaleDB (via Supabase)
- Analytics engine: TSS, CTL/ATL/TSB, Mean-Maximal-Power
- REST backend (FastAPI), background worker (Celery)
- Streamlit UI: Dashboard, Ride Explorer, Chat
- LangChain-powered chat agent (SQL over Supabase)

## Local Development

### Prerequisites
- Docker & Docker Compose
- Strava API credentials
- Supabase project (or use local TimescaleDB)
- OpenAI API key

### Setup
1. Copy `.env.example` to `.env` and fill in your secrets:
   - SUPABASE_URL
   - SUPABASE_ANON_KEY
   - STRAVA_CLIENT_ID
   - STRAVA_CLIENT_SECRET
   - OPENAI_API_KEY
   - REDIS_URL (default: redis://redis:6379/0)
2. Build and start all services:
   ```sh
   docker-compose up --build
   ```
3. Access:
   - FastAPI: http://localhost:8000
   - Streamlit UI: http://localhost:8501

### Database Migrations
- Use Alembic for SQLAlchemy migrations.
- Enable TimescaleDB extension in migrations for hypertables (see `app/db/models.py`).

### Supabase Setup Notes
- Create a new project at https://app.supabase.com
- Get your project URL and anon key from Project Settings > API
- Set up a Postgres database or connect to your own TimescaleDB

## Folder Structure
- `app/` - FastAPI backend, analytics, Strava sync, agent
- `ui/` - Streamlit UI
- `data/` - Example GPX files

## TODO
- Implement Celery tasks, analytics, agent, and UI logic
- Add Alembic migrations
- Add tests


# Directory & File Responsibilities

ai-bike-coach/
├─ app/                 # service layer
│  ├─ main.py           # FastAPI app factory, routers include auth, webhook, health
│  ├─ config.py         # Pydantic Settings, loads env (.env or secrets manager)
│  ├─ db/
│  │  ├─ models.py      # SQLAlchemy ORM + Timescale raw SQL
│  │  ├─ session.py     # engine + SessionLocal factory
│  │  └─ migrations/    # Alembic versions
│  ├─ strava/
│  │  ├─ client.py      # stravalib wrapper, get_client() auto‑refresh
│  │  ├─ routes.py      # /auth/login, /auth/callback endpoints
│  │  ├─ webhook.py     # /webhook GET verify + POST event
│  │  └─ sync.py        # Celery tasks: bulk_sync, fetch_activity
│  ├─ analytics/
│  │  ├─ pmc.py         # calc_tss, update_ctl_atl_tsb
│  │  └─ pr.py          # update_mmp, check_new_prs
│  └─ agent/
│     ├─ tools.py       # LangChain SQLDatabase tool + helper functions
│     └─ chat_agent.py  # initialise agent, answer(query)
├─ worker/              # celery entrypoint
│  └─ worker.py
├─ ui/
│  ├─ streamlit_app.py  # sidebar nav; st.session_state user_id
│  ├─ dashboard.py      # CTL/ATL/TSB plots, PR tables
│  ├─ ride_explorer.py  # Activity selector, map + charts (adapted GPX explorer)
│  └─ chat_page.py      # Streamlit chat with agent.answer()
├─ Dockerfile           # multi‑stage build: base -> fastapi+worker -> streamlit
├─ docker-compose.yml   # services: api, worker, ui, redis, db
├─ requirements.txt
└─ README.md

Development Roadmap

Phase	Goal	Key Deliverables	Acceptance Criteria
0.1	Local environment boots	docker‑compose up starts Postgres, Redis; FastAPI /health endpoint	Containers build without error; DB migrations run; /health returns {"status":"ok"}
0.2	Strava OAuth handshake	/auth/login redirect; /auth/callback stores tokens in users table	After manual grant, access/refresh tokens appear in DB and can be refreshed
0.3	Manual activity pull	CLI or API sync_initial(user_id) populates activities and streams for last 30 days	30 days of rides visible via SQL query; at least one streams row per ride
0.4	Webhook → worker pipeline	Strava webhook hits FastAPI, Celery fetches new ride, stores to DB	Finishing a new ride on Strava inserts activity & stream rows within 1 minute
0.5	Streamlit Ride Explorer tab hooked to DB	Existing GPX viewer adapted to query DB for a selected activity	Selecting a ride renders map + charts directly from DB data
0.6	Analytics engine v1	Daily Celery task calculates TSS; calculates CTL/ATL/TSB & stores results	Dashboard shows CTL vs ATL vs TSB plotted for last 90 days
0.7	Peak‑power / PR tracker	MMP algorithm updates pr_records; dashboard lists PRs	New 5‑min power PR detected and displayed after ingesting test file
0.8	LangChain SQL agent	Chat tab answers questions by querying DB via agent	Query “What was my CTL yesterday?” returns correct numeric value (±1)
1.0	MVP deployed	CI/CD builds images; Render/Railway stack with HTTPS	Same functionality accessible publicly; OAuth & webhook work end‑to‑end

Tips
	•	Implement end‑to‑end “happy path” early: OAuth → one activity → Streamlit viewer.
	•	Use fake Strava export (sample.fit → convert to GPX) in tests to avoid hitting rate limits during CI.
	•	Write Alembic migrations once models stabilize; run with alembic upgrade head in docker-compose up.
	•	Protect the webhook endpoint with Strava’s X‑Strava‑Signature header check.
	•	In Celery, batch‑insert stream rows with COPY or execute_values for speed (Strava streams can be 10 000+ rows per ride).
	•	Cache CTL/ATL queries in Supabase’s daily_metrics table to keep Streamlit snappy.