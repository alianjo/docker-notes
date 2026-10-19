# Python API + PostgreSQL with Docker Compose

A small backend example for practicing Docker Compose, service discovery, PostgreSQL health checks, persistent storage, and API/database integration.

> **Local learning example only.** The credentials in `.env.example` are placeholders, the API is published only on the host loopback interface, and the configuration is not a production deployment recipe.

## Requirements

- Docker Desktop on Windows or macOS, or Docker Engine on Linux.
- Docker Compose v2 (`docker compose`).
- PowerShell, Command Prompt, or a Unix-like shell.

## Start on Windows PowerShell

Run the commands from this directory (`examples/api-postgres`):

```powershell
Copy-Item .env.example .env
# Edit .env and change POSTGRES_PASSWORD to a local development value.
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

The first build may take several minutes while Python packages and the base image are downloaded.

By default, the API is available only on the local machine at:

- API root: http://127.0.0.1:8002/
- Readiness (includes a database check): http://127.0.0.1:8002/health/ready
- Liveness: http://127.0.0.1:8002/health/live
- Interactive API docs: http://127.0.0.1:8002/docs
- List notes: http://127.0.0.1:8002/api/v1/notes

The PostgreSQL port is **not published to the host**. The API reaches the database through the Compose network using the service name `db` and port `5432`.

## Try the API

### PowerShell

```powershell
Invoke-RestMethod http://127.0.0.1:8002/health/live
Invoke-RestMethod http://127.0.0.1:8002/health/ready
Invoke-RestMethod http://127.0.0.1:8002/api/v1/notes

$payload = @{ content = "Learning Docker Compose" } | ConvertTo-Json
Invoke-RestMethod `
    -Method Post `
    -Uri http://127.0.0.1:8002/api/v1/notes `
    -ContentType "application/json" `
    -Body $payload

Invoke-RestMethod http://127.0.0.1:8002/api/v1/notes
```

You can create more notes; they should remain in PostgreSQL when the API container is recreated.

## Useful Compose commands

```powershell
# Follow logs from both services
docker compose logs -f

# Follow only the API logs
docker compose logs -f api

# Check service and health status
docker compose ps

# Validate the resolved Compose configuration
docker compose config

# Rebuild and restart the API after changing its code
docker compose up --build -d api

# Stop and remove the containers and the Compose network
docker compose down
```

`docker compose down` keeps the named `postgres_data` volume. To intentionally remove the database volume and all data stored in it, use `docker compose down --volumes`. **This is destructive and cannot be undone unless you have a backup.**

## Configuration

- `.env.example` documents the settings used by Compose. Copy it to `.env` for local use.
- `.env` is ignored by Git. Do not commit real credentials.
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` initialize the PostgreSQL container on its first initialization of the data directory.
- `API_PORT` controls the host port mapped to container port `8000` (default `8002`). For example, `API_PORT=8010` maps the API to `127.0.0.1:8010`.
- The database uses a named volume called `postgres_data`.

If you change PostgreSQL's initialization credentials after the named volume already contains a database, changing `.env` alone does **not** change the existing database user's password. Use the proper database administration procedure or recreate the volume only when its data can be discarded.

## Architecture

```text
Host machine (127.0.0.1:8002)
          |
          v
   +--------------+       Compose network       +------------------+
   |  FastAPI API | ---------------------------> | PostgreSQL 17    |
   |  port 8000   |          db:5432             | named data volume|
   +--------------+                              +------------------+
```

Compose waits for PostgreSQL's health check before starting the API. The API also defines its own readiness check, which runs a database query. This demonstrates the difference between a process being started and an application being ready to serve requests.

## Limitations and security notes

- Credentials in `.env.example` are educational placeholders; change them even for local use.
- Environment variables can be visible to users with sufficient access to inspect the container or daemon. Avoid using them as a production-grade secret management system.
- The API has no authentication and should remain bound to localhost for this exercise.
- The example uses a single database instance and does not include migrations, TLS, backups, or production hardening.

## References

- [Docker Compose documentation](https://docs.docker.com/compose/)
- [Compose startup order and health checks](https://docs.docker.com/compose/how-tos/startup-order/)
- [Docker volumes](https://docs.docker.com/engine/storage/volumes/)
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Psycopg documentation](https://www.psycopg.org/psycopg3/docs/)
