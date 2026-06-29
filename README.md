# TaskFlow Agent Cloud — Project A: Agent Core API

A production-grade multi-tenant REST API for managing containerized agents. Demonstrates FastAPI, PostgreSQL, Redis caching, JWT authentication, Docker deployment, and CI/CD.

**Live Demo:** http://65.0.5.132:8000

## Tech Stack

- **Backend:** Python 3.11, FastAPI 0.136.1
- **Database:** PostgreSQL 18
- **Cache:** Redis 8.0.1
- **Auth:** JWT (PyJWT), bcrypt password hashing
- **Deployment:** Docker, Docker Compose, AWS EC2 (ap-south-1)
- **CI/CD:** GitHub Actions (pytest, docker build, push)

## Features

1. **Agent CRUD API** — Create, list, read, update, delete agents
2. **Multi-Tenant Isolation** — tenant_id propagated in JWT token
3. **JWT Authentication** — Signup with bcrypt, login returns token
4. **Redis Caching** — Cache-aside pattern, 5-min TTL, invalidation on write
5. **Testing & CI/CD** — 95% test coverage, automated GitHub Actions

## Quick Start

```bash
git clone https://github.com/syedshoriful/taskflow-agent-api.git
cd taskflow-agent-api
pip install -r requirements.txt
docker compose up --build
uvicorn main:app --reload
pytest tests/ -v
```

## Live Deployment

**Server:** AWS EC2 (Mumbai, ap-south-1)  
**IP:** 65.0.5.132:8000  
**Status:** Running ✅

## API Endpoints

- `POST /signup` — Register new user
- `POST /login` — Login, get JWT token
- `POST /agents` — Create agent
- `GET /agents?tenant_id=X` — List agents (cached)
- `GET /agents/{id}` — Get agent
- `PUT /agents/{id}` — Update agent
- `DELETE /agents/{id}` — Delete agent

## Author

Syed Shariful Alam Opu | Backend Engineer  
GitHub: [@syedshoriful](https://github.com/syedshoriful)
