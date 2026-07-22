# Deployment guide

## Container build

```powershell
docker build -f deploy/docker/Dockerfile -t docnexus:latest .
```

The image uses a Node builder stage and a Python runtime stage. The runtime
contains only compiled web assets, the integrated backend package, and Python
dependencies.

## Compose

```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

Before production deployment, set a random `SECRET_KEY` of at least 32
characters, restrict `CORS_ORIGINS`, configure provider credentials, and use
managed secret injection rather than committing `.env`.

The default Compose service persists SQLite under `/app/data`. For multiple
application replicas, configure `DATABASE_URL` for a managed relational
database instead of sharing SQLite.

Health probe endpoint: `GET /health`.
