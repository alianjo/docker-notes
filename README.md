# Docker Notes

A practical, developer-focused handbook for learning Docker through clear explanations, useful commands, and hands-on examples.

This repository covers the core concepts and workflows needed to build, run, connect, configure, and troubleshoot containerized applications. It is designed for developers who want to use Docker effectively in local development and prepare applications for deployment, with a particular focus on backend development.

## Table of Contents

- [Learning Path](#learning-path)
- [Getting Started](#getting-started)
- [Hands-on Examples](#hands-on-examples)
- [Useful Docker Commands](#useful-docker-commands)
- [Best Practices](#best-practices)
- [Official Resources](#official-resources)
- [Credits and Attribution](#credits-and-attribution)

## Learning Path

Follow the guides in order, or jump directly to the topic you need.

| # | Topic | What You'll Learn |
|---|---|---|
| 1 | [Docker Fundamentals](docs/01-fundamentals.md) | Core concepts and how Docker works |
| 2 | [Images and Containers](docs/02-images-and-containers.md) | Build, run, inspect, and manage containers |
| 3 | [Dockerfile](docs/03-dockerfile.md) | Write Dockerfiles and build reproducible images |
| 4 | [Networking](docs/04-networking.md) | Connect containers and understand network isolation |
| 5 | [Volumes and Storage](docs/05-volumes-and-storage.md) | Persist data and understand mount types |
| 6 | [Environment Variables](docs/06-environment-variables.md) | Configure applications without hardcoding settings |
| 7 | [Docker Compose](docs/07-docker-compose.md) | Manage multi-container applications |
| 8 | [Security](docs/08-security.md) | Apply safer container and image practices |
| 9 | [Production](docs/09-production.md) | Prepare containerized applications for deployment |
| 10 | [Troubleshooting](docs/10-troubleshooting.md) | Diagnose common Docker problems |

## Getting Started

### Prerequisites

- Docker Desktop on Windows or macOS, or Docker Engine on Linux.
- A terminal such as PowerShell, Command Prompt, or a Unix shell.
- Basic familiarity with the command line.

Follow the official [Docker installation guide](https://docs.docker.com/get-started/get-docker/).

### Verify Your Installation

Make sure Docker is installed and running:

```powershell
docker --version
docker compose version
docker run --rm hello-world
```

The final command runs a test container and downloads the image if it is not already available locally.

If a command fails, verify that the Docker daemon is running and consult the [Docker documentation](https://docs.docker.com/).

## Hands-on Examples

The `examples/` directory is organized around practical backend development scenarios.

- [`examples/python-api/`](examples/python-api/) — a containerized Python API.
- [`examples/api-postgres/`](examples/api-postgres/) — a Python API and PostgreSQL running together.

Each example includes its relevant configuration and instructions for building, running, inspecting, and cleaning up the environment.

## Useful Docker Commands

The following commands are useful when working with containers, images, and Docker Compose.

### Containers

```powershell
# List running containers
docker ps

# List all containers, including stopped ones
docker ps -a

# Run a test container
docker run --rm hello-world

# View container logs
docker logs <container_name>

# Open a shell inside a running container
docker exec -it <container_name> sh

# Stop a running container
docker stop <container_name>
```

### Images

Run `docker build` from a directory containing a Dockerfile.

```powershell
# List local images
docker images

# Build an image
docker build -t my-app:local .

# Inspect an image
docker image inspect my-app:local

# Remove unused images
docker image prune
```

Review the resources that Docker proposes to remove before confirming a prune operation.

### Docker Compose

Run these commands from a directory containing a Compose file, such as `compose.yaml` or `docker-compose.yaml`.

```powershell
# Validate and render the Compose configuration
docker compose config

# Build images and start services in the background
docker compose up --build -d

# List services and their status
docker compose ps

# Follow service logs
docker compose logs -f

# Stop and remove containers and networks created by Compose
docker compose down
```

**Important:** Use `docker compose down -v` only when you intentionally want to remove the Compose project's declared named volumes as well as its attached anonymous volumes. This can delete persistent application data.

## Best Practices

- Use explicit and predictable Dockerfile instructions.
- Add a `.dockerignore` file to exclude unnecessary files from the build context.
- Never bake passwords, access tokens, or production secrets into an image.
- Use named volumes for data that must persist independently of a container's lifecycle.
- Run application processes as a non-root user whenever practical.
- Keep base images and dependencies maintained, and review updates before adopting them.
- Use Docker Compose to define related development services declaratively.
- Use health checks where appropriate and distinguish container startup from application readiness.
- Test commands and configurations instead of relying on unverified examples.
- Review the consequences of cleanup commands before removing containers, images, networks, or volumes.

For additional guidance, see the official [Docker build best practices](https://docs.docker.com/build/building/best-practices/) documentation.

## Official Resources

- [Docker Get Started](https://docs.docker.com/get-started/)
- [Docker CLI Reference](https://docs.docker.com/reference/cli/docker/)
- [Dockerfile Reference](https://docs.docker.com/reference/dockerfile/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Compose File Reference](https://docs.docker.com/reference/compose-file/)
- [Docker Engine Security](https://docs.docker.com/engine/security/)
- [Docker Build Best Practices](https://docs.docker.com/build/building/best-practices/)

## Credits and Attribution

This repository originated as a fork of [alianjo/docker-notes](https://github.com/alianjo/docker-notes).

The original notes also acknowledge [Play with Docker Scenarios](https://training.play-with-docker.com/) and [Nikolai Levshakov](https://github.com/nikolailevshakov).

This repository reorganizes and extends the original learning material. Original author credits and applicable license notices should be preserved.

---

A practical learning resource for developers who want to understand Docker by using it.
