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
