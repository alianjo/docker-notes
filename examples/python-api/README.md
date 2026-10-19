# Python API Docker Example

A small FastAPI application used by the Docker Notes handbook. It demonstrates a Dockerfile, dependency installation, non-root execution, a container health check, environment-based configuration, and port publishing.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | API overview and useful links |
| `GET` | `/health` | Lightweight health endpoint |
| `GET` | `/api/v1/info` | Public application name and version |
| `GET` | `/api/v1/greet?name=Amir` | Query-parameter example |
| `GET` | `/docs` | Interactive OpenAPI documentation |

The API deliberately does not expose the process environment or accept secrets through query parameters.

## Run locally on Windows

Use PowerShell from this directory:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

In a second PowerShell window, try:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/info
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/greet?name=Amir"
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation. Stop the local server with `Ctrl+C`.

## Build and run with Docker

Run these commands from this directory. Docker must be installed and running.

```powershell
docker build -t docker-notes-python-api:local .
docker run --rm --name docker-notes-python-api --env-file .env.example -p 127.0.0.1:8000:8000 docker-notes-python-api:local
```

The port is bound to `127.0.0.1` so this learning example is reachable locally without publishing the port on every host network interface. Keep the container running and use a second PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/greet?name=Amir"
docker inspect --format "{{json .State.Health}}" docker-notes-python-api
```

Stop and remove the container by pressing `Ctrl+C` in the window running `docker run`. Because the container was started with `--rm`, Docker removes it after it exits. The built image remains locally.

To remove the image when it is no longer needed:

```powershell
docker image rm docker-notes-python-api:local
```

## Configure the application name

Edit `.env.example` for this local demonstration or create a separate `.env` file:

```dotenv
APP_NAME=My Local API
```

Then pass the selected file with `--env-file`. Do not put passwords, access tokens, or other secrets into the example env file, image, or source control. Environment variables are configuration, not a dedicated secret-management system.

## Implementation notes

- The image uses a slim Python base image and installs pinned direct dependencies.
- The application runs as a non-root user.
- The Dockerfile defines a health check using the Python standard library.
- Port `8000` is the container's listening port; host port publishing is configured at runtime.
- This is an educational example, not a complete production deployment template. Review base image updates, dependency updates, TLS termination, resource limits, and operational requirements before production use.
