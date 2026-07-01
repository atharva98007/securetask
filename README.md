SecureTask API
A scalable REST API with JWT authentication and role-based access control (RBAC), built with FastAPI + SQLAlchemy, plus a lightweight vanilla-JS frontend for demoing the endpoints.
Built for the Primetrade.ai Backend Developer Intern assignment.
🔗 Live demo: https://securetask-otb6.onrender.com/app/
📄 API docs (Swagger): https://securetask-otb6.onrender.com/docs
> Note: hosted on Render's free tier, which spins down after 15 minutes of inactivity — the first request after idle time can take 30–60 seconds to wake up.
---
Stack
Layer	Choice
Framework	FastAPI
Database	SQLite (default, zero-config) — Postgres/MySQL ready
ORM	SQLAlchemy 2.0
Auth	JWT (access + refresh tokens) via `python-jose`
Hashing	bcrypt via `passlib`
Validation	Pydantic v2
Docs	Auto-generated Swagger (`/docs`) + Postman collection
Frontend	Vanilla HTML/CSS/JS (no build step)
Deployment	Docker + docker-compose (API + Postgres), Render-ready
---
Features
Auth: register, login, refresh, `/auth/me` — passwords hashed with bcrypt, strong password validation (min 8 chars, upper/lower/digit).
RBAC: two roles, `user` and `admin`. The first registered account automatically becomes admin (bootstrap convenience for a fresh DB); everyone after that is `user`. Admins can list all users, promote/demote roles, deactivate accounts, and see/manage every task. Regular users can only see and manage their own tasks.
Tasks CRUD: create/read/update/delete, with `status` (pending/in_progress/completed) and `priority` (low/medium/high), pagination (`page`, `page_size`), and status filtering.
API versioning: everything lives under `/api/v1/...` so breaking changes can ship as `/api/v2` without disrupting existing clients.
Consistent error format: every error response is `{"success": false, "error": {"message": ..., ...}}` with the correct HTTP status code (400/401/403/404/409/422/500).
Input validation: Pydantic schemas validate every request body (lengths, email format, enum values, password strength).
Frontend: register/login screens, protected dashboard, task CRUD with inline status/priority tags, pagination, and success/error banners reflecting real API responses. Access tokens auto-refresh via the refresh token on 401.
---
Project Structure
```
securetask-api/
├── app/
│   ├── core/
│   │   ├── config.py          # env-driven settings
│   │   └── security.py        # hashing + JWT helpers
│   ├── db/
│   │   └── database.py        # SQLAlchemy engine/session
│   ├── models/                # SQLAlchemy ORM models (User, Task)
│   ├── schemas/                # Pydantic request/response schemas
│   ├── api/
│   │   ├── deps.py            # get_current_user, admin guard
│   │   └── v1/
│   │       ├── auth.py        # /auth/*
│   │       ├── tasks.py       # /tasks/* (CRUD, RBAC-scoped)
│   │       ├── users.py       # /users/* (admin only)
│   │       └── router.py      # aggregates v1 routes
│   └── main.py                # app factory, CORS, error handlers, static mount
├── frontend/
│   └── index.html             # single-file demo UI
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── render.yaml                # one-click Render deploy config
├── postman_collection.json
└── README.md
```
This structure keeps concerns isolated (models / schemas / routes / security) so new resources (e.g. `projects`, `comments`) can be added as a new `models/`, `schemas/`, and `api/v1/` file without touching existing code — see `SCALABILITY.md` for how this extends further.
---
Setup & Run — Windows
Requires Python 3.11+ (python.org/downloads) and Git (git-scm.com).
```cmd
cd securetask-api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Setup & Run — macOS / Linux
```bash
cd securetask-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Then open:
Frontend demo UI → http://localhost:8000/app/
Swagger docs → http://localhost:8000/docs
ReDoc → http://localhost:8000/redoc
Health check → http://localhost:8000/health
The first account you register through `/auth/register` (or the frontend's "Register" screen) automatically becomes an admin.
---
Setup & Run (Docker + Postgres)
```bash
cd securetask-api
docker compose up --build
```
This spins up Postgres and the API together, with the API reading `DATABASE_URL` from `docker-compose.yml`. Same URLs as above once containers are healthy.
To point the local (non-Docker) app at Postgres instead of SQLite, edit `.env`:
```
DATABASE_URL=postgresql://securetask:securetask@localhost:5432/securetask
```
(and run `docker compose up db` to start just the database.)
---
Deploying to Render (free tier)
Push this repo to GitHub.
Sign up at render.com with GitHub — no credit card required for a free web service.
New → Web Service → connect the repo. Render auto-detects the `Dockerfile` and reads `render.yaml` for environment variables (including auto-generating a secure `SECRET_KEY`).
Choose the Free instance type → Create Web Service.
Your live URL will look like `https://<your-service-name>.onrender.com`.
Free-tier notes: the service spins down after 15 minutes of inactivity (cold start ~30–60s on next request), and the SQLite file resets on redeploys since free-tier disk isn't persistent. For persistent data, add a free Render Postgres instance and point `DATABASE_URL` at it — no code changes required.
---
API Overview
All endpoints are under `/api/v1`.
Method	Endpoint	Auth	Description
POST	`/auth/register`	none	Create account
POST	`/auth/login`	none	Get access + refresh tokens
POST	`/auth/refresh`	refresh token	Rotate a new access/refresh pair
GET	`/auth/me`	access token	Current user profile
POST	`/tasks`	access token	Create a task (owned by caller)
GET	`/tasks`	access token	List tasks (own tasks; all if admin), paginated + filterable
GET	`/tasks/{id}`	access token	Get one task (owner or admin)
PUT	`/tasks/{id}`	access token	Update a task (owner or admin)
DELETE	`/tasks/{id}`	access token	Delete a task (owner or admin)
GET	`/users`	admin only	List all users
PATCH	`/users/{id}/role`	admin only	Change a user's role
PATCH	`/users/{id}/deactivate`	admin only	Deactivate an account
Full request/response schemas are in Swagger (`/docs`) and `postman_collection.json` (import directly into Postman; set the `base_url` collection variable to your deployed URL if not testing locally).
Auth flow
`POST /auth/register` → creates account, returns user profile (no token yet).
`POST /auth/login` → returns `{ access_token, refresh_token }`.
Send `Authorization: Bearer <access_token>` on subsequent requests.
When the access token expires (60 min default), `POST /auth/refresh` with the refresh token (7-day default) to get a new pair — the frontend does this automatically on a 401.
---
Security Notes
Passwords are never stored or logged in plaintext — hashed with bcrypt.
JWTs are signed (HS256) and carry `sub` (user id), `role`, `type` (access/refresh), `iat`, `exp`. `SECRET_KEY` must be rotated to a long random value in production (see `.env.example` for a generation command) — Render auto-generates a secure one on deploy via `render.yaml`.
Access and refresh tokens are typed (`type` claim) so a refresh token can't be replayed as an access token, and vice versa.
Ownership checks happen server-side on every task read/write — a user can never read or mutate another user's task by guessing an ID; admin-only routes are protected by a dependency, not by trusting client-supplied roles.
All input is validated by Pydantic before it reaches the database (type/length/format/enum checks), which also mitigates injection-style payloads; SQLAlchemy's parameterized queries handle the rest.
CORS is configured centrally in `app/core/config.py` — restrict `CORS_ORIGINS` to real frontend domains in production instead of `"*"`.
---
Testing the API
This was manually verified end-to-end during development:
Registration (incl. weak-password rejection, duplicate-email rejection)
Login, token issuance, and refresh
Task CRUD as a regular user
Cross-user task access correctly blocked (403)
Admin listing all tasks/users; non-admin blocked from `/users` (403)
Swagger UI, ReDoc, and the static frontend all serve correctly
Deployed and verified live on Render
Import `postman_collection.json` into Postman for a ready-made test flow (Login auto-captures the token into a collection variable for subsequent requests).
---
Scalability
See `SCALABILITY.md` for how this design extends to higher load and more modules (caching, load balancing, DB scaling, microservice extraction).
