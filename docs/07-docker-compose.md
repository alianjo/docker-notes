# Docker Compose

Docker Compose is a tool for defining and running multi-container applications. A Compose file describes services, networks, volumes, configuration, and how those parts fit together. Instead of remembering a long sequence of `docker run` commands, you can keep the application's configuration in version control and manage the stack with commands such as `docker compose up` and `docker compose down`.

This chapter uses the current Compose CLI syntax (`docker compose`) and PowerShell-friendly commands. The hands-on lab runs PostgreSQL and Adminer locally so you can practice service discovery, health checks, persistent volumes, environment-variable interpolation, and the Compose lifecycle without first creating an application image.

## Table of Contents

- [What Compose Does](#what-compose-does)
- [Core Concepts](#core-concepts)
- [Compose File Structure](#compose-file-structure)
- [Hands-on Lab: PostgreSQL and Adminer](#hands-on-lab-postgresql-and-adminer)
- [Environment Variables and `.env`](#environment-variables-and-env)
- [Startup Order and Health Checks](#startup-order-and-health-checks)
- [Networks and Service Discovery](#networks-and-service-discovery)
- [Volumes and Persistent Data](#volumes-and-persistent-data)
- [Everyday Compose Commands](#everyday-compose-commands)
- [Development Overrides and Profiles](#development-overrides-and-profiles)
- [Troubleshooting](#troubleshooting)
- [Security and Best Practices](#security-and-best-practices)
- [Common Mistakes](#common-mistakes)
- [Key Takeaways](#key-takeaways)
- [Further Reading](#further-reading)

## What Compose Does

A backend project often depends on more than one process. For example, a Django or FastAPI service may require PostgreSQL and Redis. Compose lets you describe these services in one YAML file, then create and manage the environment as a single project.

Compose can:

- Build an image from a Dockerfile or pull an existing image.
- Create and connect service containers to networks.
- Publish selected container ports on the host.
- Attach named volumes or bind mounts.
- Configure environment variables, health checks, restart policies, and service dependencies.
- Display service status and aggregate logs.

Compose describes how the environment should be configured; it does not automatically make an application resilient, secure, or production-ready. The application still needs correct configuration, error handling, and operational monitoring.

## Core Concepts

### Project

A Compose project groups the resources created from a Compose configuration. By default, Compose derives the project name from the directory name, subject to its naming rules. You can choose a name with the top-level `name:` field or the `-p` command-line option.

### Service

A service describes one type of component, including its image or build context, ports, environment, networks, mounts, and other runtime settings. Compose commonly creates one or more containers for each service.

Examples include `api`, `db`, `redis`, and `proxy`.

### Network

Compose creates a default network for a project unless the configuration changes that behavior. Services attached to the same Compose network can normally reach one another using their service names as DNS hostnames.

Inside an API container, a database connection generally uses the database service name and the database's container port, for example `db:5432`. It should not use `localhost:5432` to reach another container: `localhost` inside a container refers to that container itself.

### Volume

A named volume can keep state outside an individual container's writable layer. This is especially important for databases. Removing a container does not normally remove a named volume, while `docker compose down -v` requests removal of project volumes and can delete persistent data.

### Compose file

The conventional filename is `compose.yaml`. Compose also recognizes other supported filenames, including `compose.yml` and the legacy `docker-compose.yaml` / `docker-compose.yml` names. Prefer `compose.yaml` for new examples.

## Compose File Structure

Here is a small illustrative configuration with an application service and a database service:

```yaml
services:
  api:
    build: ./api
    environment:
      DATABASE_HOST: db
      DATABASE_PORT: "5432"
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: local-dev-only
    volumes:
      - database_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  database_data:
```

This is a teaching example, not a complete secure deployment. It assumes `./api` contains a valid Dockerfile and that the application reads the `DATABASE_HOST` and `DATABASE_PORT` settings. The sample password is intentionally a local-development placeholder; do not use it for real credentials.

Important parts:

- `build: ./api` tells Compose to build the API image using the `api` directory as its build context.
- `image: postgres:17-alpine` selects a PostgreSQL image and tag.
- `environment` sets variables inside a container. Values written directly in the file are configuration, not secrets storage.
- `depends_on` with `condition: service_healthy` waits for the database health check to pass before starting the dependent service.
- `healthcheck` defines a command Compose can use to evaluate the database container's health.
- `database_data` declares a named volume for persistent database files.

The doubled dollar signs in `$${POSTGRES_USER}` and `$${POSTGRES_DB}` are intentional. They prevent Compose from interpolating these variables while reading the YAML; the shell inside the database container expands them when the health check executes.

## Hands-on Lab: PostgreSQL and Adminer

This lab starts PostgreSQL with Adminer, a browser-based database administration interface. It is designed for local learning. Keep the ports bound to the loopback interface and do not reuse the demo credentials for a real application.

### Step 1: Create a lab directory

In PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path "compose-lab" | Out-Null
Set-Location "compose-lab"
```

Create two files in this directory: `compose.yaml` and `.env`.

### Step 2: Create `.env`

Add the following content to `.env`:

```dotenv
POSTGRES_DB=appdb
POSTGRES_USER=appuser
POSTGRES_PASSWORD=local-dev-change-me
```

This file supplies values for Compose interpolation. Only variables explicitly referenced in the Compose file are passed to a container; merely defining a variable in `.env` does not automatically inject it into every service.

Treat the password here as a throwaway local value. Do not commit a real `.env` file to Git.

### Step 3: Create `compose.yaml`

```yaml
name: docker-notes-lab

services:
  db:
    image: postgres:17-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-appdb}
      POSTGRES_USER: ${POSTGRES_USER:-appuser}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 10s
    networks:
      - backend

  adminer:
    image: adminer:4
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:8080"
    environment:
      ADMINER_DEFAULT_SERVER: db
    depends_on:
      db:
        condition: service_healthy
    networks:
      - backend

volumes:
  postgres_data:

networks:
  backend:
    driver: bridge
```

The `${NAME:-default}` syntax supplies a default if a variable is unset or empty. `${NAME:?message}` makes Compose report an error if the required variable is unset or empty. The `127.0.0.1:8080:8080` port mapping makes the Adminer interface available only through the host's loopback interface, rather than all host network interfaces.

### Step 4: Validate the configuration

From the same directory as `compose.yaml` and `.env`, run:

```powershell
docker compose config
```

Compose parses and renders the configuration, including its resolved interpolation values. Review the output before sharing it; rendered configuration can include sensitive values.

### Step 5: Start the services

```powershell
docker compose up --detach
```

Compose pulls the images if needed, creates the network and volume, and starts the services. The Adminer service waits until the database health check reports healthy.

Check service status:

```powershell
docker compose ps
docker compose logs --follow db
```

Press `Ctrl+C` to stop following logs; this does not stop the containers.

### Step 6: Open Adminer

Open [http://localhost:8080](http://localhost:8080) in your browser and use these lab settings:

- **System:** PostgreSQL
- **Server:** `db`
- **Username:** `appuser`
- **Password:** `local-dev-change-me` (the example value from `.env`)
- **Database:** `appdb`

If you changed the values in `.env`, use your chosen values instead. The hostname `db` works between containers because it is the Compose service name on the shared network; it is not the hostname to use from your Windows host.

### Step 7: Stop the lab

Stop and remove the containers and the project network:

```powershell
docker compose down
```

The named volume `postgres_data` is retained by this command, so the lab's database files can survive a normal container teardown and subsequent startup.

To remove the lab's named volume as well, use the following only when you intentionally want to discard the database data:

```powershell
docker compose down --volumes
```

Do not run the second command if you need to preserve data. Cleanup commands can permanently remove local development state.

## Environment Variables and `.env`

Compose uses environment variables for more than one purpose. It is important to distinguish these mechanisms.

### Interpolation

Compose reads variables from the shell environment and its interpolation environment sources, including a project `.env` file or files explicitly supplied with `--env-file`. These variables can fill placeholders in `compose.yaml`:

```yaml
services:
  api:
    image: "my-api:${API_TAG:-dev}"
```

For example, `API_TAG=1.2` can resolve the image reference to `my-api:1.2`. The variable is used to render the Compose model; this alone does not create an `API_TAG` environment variable inside the container.

### Container environment

Use `environment` to set variables explicitly inside a service:

```yaml
services:
  api:
    image: my-api:local
    environment:
      APP_ENV: development
      DATABASE_HOST: db
```

Or use `env_file` to load environment variables for a service:

```yaml
services:
  api:
    image: my-api:local
    env_file:
      - ./api.env
```

The `env_file` attribute and the project `.env` file are not interchangeable. A project `.env` is commonly used for Compose-file interpolation; a service-level `env_file` sets variables in the container's environment.

For example, to select a different interpolation file:

```powershell
docker compose --env-file .env.dev config
docker compose --env-file .env.dev up --detach
```

Always review the resolved configuration when testing variable changes.

## Startup Order and Health Checks

A simple `depends_on` declaration establishes a startup and shutdown relationship, but a running process is not necessarily ready to serve requests. A database may need several seconds to initialize after its container starts.

Where appropriate, define a health check and use the long form of `depends_on` with `condition: service_healthy`:

```yaml
services:
  api:
    build: ./api
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:17-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 10
```

The database example still needs its credentials and data configuration, as shown in the previous examples. A health check tests the condition you define; it does not prove that every application-level query will succeed. Applications should also handle temporary connection failures and reconnect where appropriate.

## Networks and Service Discovery

Compose normally creates a project network and connects services to it. Services on that network can find each other by service name using Docker's internal DNS.

For example, an API connects to PostgreSQL using:

```text
Host: db
Port: 5432
```

A connection to `localhost:5432` from inside the API container would normally refer to the API container itself, not the PostgreSQL service.

You generally do not need to publish a database port to the host just to let another Compose service connect to it. Publish only the ports that need to be accessed from outside the Compose network.

## Volumes and Persistent Data

Declare named volumes at the top level of the Compose file and mount them into services:

```yaml
services:
  db:
    image: postgres:17-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Compose creates the named volume when required. Named volumes are usually preferable for database storage, while bind mounts are often useful for sharing source code or configuration files with a development container.

Read [Volumes and Storage](05-volumes-and-storage.md) for a broader explanation of mounts, backups, and recovery. A Docker volume is not automatically a backup: production data still needs a tested backup and restore process.

## Everyday Compose Commands

Run these commands from the project directory unless the command specifies a different file or project:

```powershell
# Validate and render the Compose model
docker compose config

# List services and their state
docker compose ps

# Build images and create/start services
docker compose up --build --detach

# Follow logs from all services
docker compose logs --follow

# Follow logs for one service
docker compose logs --follow db

# Run a one-off command in a new service container
docker compose run --rm db psql --version

# Execute a command in an existing running container
docker compose exec db psql --version

# Stop services without removing containers
docker compose stop

# Start existing stopped containers
docker compose start

# Stop and remove containers and project networks
docker compose down
```

The `run` command creates a one-off container for a service, whereas `exec` runs a command in an already running container. Not every service image contains a shell or every utility, so select commands that the chosen image actually supports.

## Development Overrides and Profiles

Compose supports multiple configuration files. This is useful when a shared base file defines the core services and a development override adds local-only settings.

For example, Compose automatically merges `compose.yaml` with `compose.override.yaml` when both files exist in the project directory and the default file-loading behavior applies. You can also specify files explicitly:

```powershell
docker compose -f compose.yaml -f compose.dev.yaml config
docker compose -f compose.yaml -f compose.dev.yaml up --detach
```

The order matters: later files can override or extend earlier configuration. Check the rendered output with `docker compose config` before starting services.

Profiles can make optional services available only when requested:

```yaml
services:
  debug-tool:
    image: alpine:3.21
    profiles: ["debug"]
    command: ["sh", "-c", "echo Debug tools enabled"]
```

Start the service with its profile enabled:

```powershell
docker compose --profile debug up --detach
```

Profiles are useful for optional tools, but they should not replace clear environment separation and access controls.

## Troubleshooting

### The configuration contains an unresolved or empty variable

Run `docker compose config` and verify the shell environment, the project `.env` file, the path passed with `--env-file`, and any default or required-value expression used in the YAML.

### A service cannot connect to the database

Check that both services are connected to a common network, that the database service name is used as the hostname, the port is correct, the database is healthy, and the credentials match. Do not assume that a running container means the database is ready.

### A port is already allocated

Another process or container may already be using the host port. Change the host side of the port mapping (for example, from `127.0.0.1:8080:8080` to `127.0.0.1:8081:8080`) and recreate the affected service if appropriate.

### A volume seems to contain old data

Database initialization variables often apply only when an empty data directory is initialized. Changing `.env` later does not automatically reinitialize an existing database volume. Inspect the data and follow a deliberate migration or reset procedure; do not delete a volume blindly.

### Changes to the Compose file do not appear in the service

Review the resolved configuration with `docker compose config`. If an image needs rebuilding, use `docker compose up --build --detach`. Some configuration changes require containers to be recreated. Make sure the command runs from the intended project directory and uses the correct Compose files.

### View service logs

```powershell
docker compose ps
docker compose logs --tail 100 db
docker compose logs --follow
```

## Security and Best Practices

- Keep local `.env` files containing sensitive values out of version control; commit a safe `.env.example` containing placeholders instead.
- Do not put real secrets directly in a Compose file, Dockerfile, image, or public repository.
- Prefer dedicated secret-management mechanisms for sensitive credentials. Compose secrets can expose a secret to explicitly authorized services as a mounted file, but the available mechanism and security guarantees depend on the deployment environment.
- Remember that environment variables can be visible through container configuration and diagnostic tools. They are not a general-purpose secret vault.
- Bind development-only web interfaces to `127.0.0.1` when they should be accessible only from the local host.
- Avoid publishing database ports unless host access is required.
- Use health checks when service readiness matters, and make applications tolerant of temporary dependency failures.
- Declare named volumes for persistent data and maintain separate, tested backups.
- Use explicit image tags and update them deliberately.
- Review `docker compose config` output carefully; interpolated values can include sensitive settings.
- Understand the effect of `docker compose down --volumes` before running it.

## Common Mistakes

**Using `localhost` as the database hostname inside an API container.** Use the database's Compose service name, such as `db`, when both services share a network.

**Assuming the project `.env` file is automatically passed into every container.** Variables must be referenced by the Compose model or supplied through a service's `env_file` or `environment` configuration.

**Treating `depends_on` as proof that a service is ready.** Use a suitable health check and `condition: service_healthy` when appropriate, and still handle runtime connection failures in the application.

**Deleting a volume to force a configuration change.** Database initialization settings generally do not rewrite an existing data directory. Understand the database's update process before resetting storage.

**Assuming Compose files are merged in arbitrary order.** The order of files supplied using `-f` affects the merged configuration. Verify it with `docker compose config`.

**Publishing every service port.** Only publish ports required by host clients or external systems; services can communicate internally over Compose networks.

## Key Takeaways

- Compose describes multi-container applications in YAML.
- Services can be built from local Dockerfiles or use existing images.
- Containers on a shared Compose network can generally address each other using service names.
- Project `.env` files support interpolation, while `environment` and service-level `env_file` configure container environments.
- Health checks can help control startup dependencies, but applications still need to handle transient failures.
- Named volumes preserve data beyond container removal; `down --volumes` can delete that data.
- Secrets need careful handling and should not be hardcoded into configuration or images.
- `docker compose config`, `ps`, and `logs` are useful first steps when diagnosing configuration and startup problems.

## Further Reading

- [Docker Compose Quickstart](https://docs.docker.com/compose/gettingstarted/)
- [Compose file reference](https://docs.docker.com/reference/compose-file/)
- [How Compose works](https://docs.docker.com/compose/intro/compose-application-model/)
- [Environment variable interpolation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/)
- [Set environment variables in containers](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/)
- [Control startup order](https://docs.docker.com/compose/how-tos/startup-order/)
- [Docker volumes](https://docs.docker.com/engine/storage/volumes/)

## Next Chapter

Continue with [Security](08-security.md) after completing the guides on environment variables and the Compose workflow.
