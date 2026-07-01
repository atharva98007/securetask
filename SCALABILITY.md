# Scalability Note

Short notes on how SecureTask API would scale beyond a single-instance demo.

## 1. Application layer

- **Stateless API processes.** Auth is JWT-based (no server-side sessions), so any number of API instances can run behind a load balancer without sticky sessions or shared session storage. Scaling out is just adding more `uvicorn`/`gunicorn` workers or container replicas.
- **Modular routing.** New resources (e.g. `projects`, `comments`, `notifications`) plug in as their own `models/`, `schemas/`, and `api/v1/<resource>.py` file, registered once in `router.py`. This keeps the codebase scaling horizontally in *feature count* without routes stepping on each other.
- **API versioning already in place** (`/api/v1`) means breaking changes ship as `/api/v2` alongside the old version, so existing client integrations aren't broken by iteration.
- **Production ASGI server**: run with `gunicorn -k uvicorn.workers.UvicornWorker -w <N>` (N ≈ 2×CPU cores) instead of the single dev process used locally.

## 2. Database layer

- **Swap SQLite → Postgres for production** (already supported — just change `DATABASE_URL`; no code changes, since SQLAlchemy abstracts the dialect).
- **Connection pooling**: `pool_pre_ping=True` is already set; in production, tune `pool_size`/`max_overflow` or front the DB with **PgBouncer** for high connection counts.
- **Read replicas**: route `GET` list/detail queries to a read replica and writes to the primary once read traffic dominates (typical for a task-list app).
- **Indexes**: `email` is already indexed (unique) for fast login lookups; add a composite index on `(owner_id, status)` on `tasks` once filtering/listing volume grows, since that's the hot query path.
- **Migrations**: the demo uses `Base.metadata.create_all()` for zero-friction local setup. For a real deployment, switch to **Alembic** migrations so schema changes are versioned and reversible instead of implicit.

## 3. Caching

- **Redis** in front of read-heavy, rarely-changing endpoints (e.g. `GET /tasks` list pages, user profile lookups) with short TTLs and cache invalidation on writes.
- **Rate limiting** (also via Redis, e.g. `slowapi`) on `/auth/login` and `/auth/register` to blunt brute-force/credential-stuffing attempts — currently not implemented, called out here as the top next-step for hardening.

## 4. Horizontal scaling & deployment

- Containerized already (`Dockerfile` + `docker-compose.yml`); the natural next step is deploying the same image to **ECS/Kubernetes/Cloud Run**, fronted by a **load balancer** (ALB/NGINX) doing TLS termination and round-robin/least-connections routing across replicas.
- **Health checks**: `/health` is already exposed and ready to wire into a load balancer's or orchestrator's liveness/readiness probes.
- **Autoscaling** on CPU/request-rate thresholds, since the API layer is stateless and safe to scale elastically.

## 5. Longer-term: microservice extraction

At meaningfully larger scale, natural seams already exist along the module boundaries in this codebase:
- **Auth/Users service** — owns identity, issues JWTs; other services just verify the JWT signature (shared `SECRET_KEY` or, better, move to asymmetric RS256 so only the auth service holds the signing key).
- **Tasks service** — owns the task domain and could scale independently of auth traffic.
- Communication between services would move to internal REST/gRPC calls or an event bus (Kafka/RabbitMQ) for async workflows (e.g. "task completed" notifications), rather than the current single-process direct calls.

## 6. Observability

- Structured logging (JSON logs) + request IDs for tracing a request across services once split up.
- Centralized error tracking (Sentry) — the app's centralized exception handlers in `main.py` are already the natural hook point to report to a tracker.
- Metrics (Prometheus/Grafana) on request latency, error rate, and DB pool saturation to know *when* to scale rather than guessing.

---

**Summary**: the current design (stateless JWT auth, ORM-abstracted DB, versioned modular routing, containerized) is intentionally structured so that scaling is mostly *infrastructure* work (more replicas, a real Postgres instance, Redis, a load balancer) rather than *application rewrites* — the biggest code-level next steps would be Alembic migrations, Redis-backed rate limiting, and eventually splitting Auth and Tasks into separate services if load demands it.
