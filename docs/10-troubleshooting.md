# Docker Troubleshooting

Troubleshooting Docker is easier when you work from evidence instead of repeatedly restarting containers or deleting resources. Start by identifying the failing layer, collect the relevant state and logs, change one thing at a time, and verify the result.

This chapter focuses on common problems encountered with Docker Desktop, Docker Engine, Dockerfiles, container startup, networking, storage, and Docker Compose. Commands are written for PowerShell where practical.

## Table of Contents

- [A Systematic Troubleshooting Workflow](#a-systematic-troubleshooting-workflow)
- [Check the Docker Client and Daemon](#check-the-docker-client-and-daemon)
- [A Container Exits Immediately](#a-container-exits-immediately)
- [Read Logs and Inspect State](#read-logs-and-inspect-state)
- [Image Build Failures](#image-build-failures)
- [Port Publishing and Connection Problems](#port-publishing-and-connection-problems)
- [Container-to-Container Networking](#container-to-container-networking)
- [Volume and Bind Mount Problems](#volume-and-bind-mount-problems)
- [Docker Compose Problems](#docker-compose-problems)
- [Environment Variable Problems](#environment-variable-problems)
- [Resource and Disk Problems](#resource-and-disk-problems)
- [Cleanup Without Losing Data](#cleanup-without-losing-data)
- [A Reusable Diagnostic Checklist](#a-reusable-diagnostic-checklist)
- [Further Reading](#further-reading)

## A Systematic Troubleshooting Workflow

Use this sequence before attempting a fix:

1. **Describe the symptom.** Record the exact command, error message, and what you expected to happen.
2. **Check the current state.** Determine whether the image exists, whether the container was created, and whether it is running or exited.
3. **Inspect logs and metadata.** Application logs, container state, exit codes, mounts, and port mappings provide different kinds of evidence.
4. **Verify configuration.** Check the image name, command, environment variables, filesystem paths, network, mounts, and Compose configuration.
5. **Make one change.** Avoid changing several settings at once, so you can identify which change resolved the issue.
6. **Verify the fix.** Repeat the failing action and test the application itself, not only whether the container is running.

Avoid starting with broad cleanup commands such as `docker system prune --all --volumes`. They can remove resources that are still needed and make the original problem harder to investigate.

## Check the Docker Client and Daemon

When Docker commands fail before they can inspect an image or container, first check whether the client can communicate with the Docker daemon.

```powershell
# Confirm that the Docker CLI is installed
 docker --version

# Display client and server information
 docker version

# Check the active Docker environment and daemon
 docker info
```

If `docker --version` works but `docker version` or `docker info` reports a daemon connection error, the CLI may be installed while the engine is stopped or unreachable.

On Windows or macOS, make sure Docker Desktop has finished starting. On Linux, check the Docker Engine service using the service manager appropriate for the distribution.

Also inspect the current Docker context:

```powershell
docker context ls
docker context show
```

The selected context determines which Docker endpoint the CLI targets. A context pointing to a remote or unavailable daemon can explain why local containers appear to be missing.

## A Container Exits Immediately

A container runs its configured main process. When that process exits, the container stops. This is not necessarily a Docker failure: the application may have finished successfully, rejected its configuration, or crashed during startup.

List all containers, including stopped ones:

```powershell
docker ps --all
```

Then inspect the exit code and state. Replace `my-container` with the actual container name or ID.

```powershell
docker inspect --format '{{.State.Status}} {{.State.ExitCode}} {{.State.Error}}' my-container
docker logs --tail 100 my-container
```

Look for missing configuration, import errors, invalid command arguments, failed database connections, file-permission errors, or an application listening on the wrong interface or port.

Useful distinctions:

- A short-lived command such as `docker run alpine echo hello` exits normally after printing its result.
- A web application usually needs a foreground process that remains running.
- A container restart policy may repeatedly restart a failing process, but it does not fix the underlying problem.
- An exited container can still be inspected and its logs can still be read until it is removed.

## Read Logs and Inspect State

Use logs to learn what the main process printed, and inspection to learn how Docker configured and observed the container. They are complementary tools.

```powershell
# Show recent output
 docker logs --tail 100 my-container

# Follow new output as it arrives
 docker logs --follow my-container

# Inspect complete container metadata
 docker inspect my-container

# Display resource usage for running containers
 docker stats

# Show recent Docker events
 docker events --since 10m
```

`docker logs` is most useful when the application writes diagnostics to standard output or standard error. If the application writes logs only to an internal file, consult its logging configuration as well.

When sharing logs in an issue or support request, remove credentials, access tokens, session identifiers, personal data, and other sensitive values first.

## Image Build Failures

### The Dockerfile Cannot Be Found

The final argument to `docker build` is the build context. If the command ends with `.`, Docker expects the current directory to be the context and typically looks for a file named `Dockerfile` there.

```powershell
Get-Location
Get-ChildItem

docker build -t notes-api:local .
```

Run the command from the directory containing the Dockerfile and application files, or provide the intended Dockerfile and context explicitly:

```powershell
docker build -f .\backend\Dockerfile -t notes-api:local .
```

In this example, the repository root is the build context and `backend\Dockerfile` supplies the instructions. Adjust the paths to match the actual project.

### A File Is Missing During COPY

`COPY` sources are resolved relative to the build context, not relative to the Dockerfile's directory. Check that the file exists inside the context and is not excluded by `.dockerignore`.

```powershell
Get-ChildItem -Force
Get-Content .dockerignore
```

Do not add secrets or unrelated local files to the build context just to work around a missing file. Correct the path or ignore rules instead.

### Dependency Installation Fails

Check the exact package error, Python or Node runtime version, lockfile or requirements file, network access, and target architecture. Avoid assuming that disabling the cache will repair a dependency or configuration error.

To rebuild without using cached layers for diagnostic purposes:

```powershell
docker build --no-cache --progress=plain -t notes-api:debug .
```

Use this to expose build output or test whether a stale cached layer is involved. It may make the build slower and does not itself fix the source of the error.

### The Image Builds but the App Does Not Start

Image construction and application startup are separate stages. Review the Dockerfile's `CMD` and `ENTRYPOINT`, the working directory, files copied into the image, runtime environment variables, user permissions, and startup logs.

```powershell
docker image inspect notes-api:local
docker run --rm notes-api:local
```

The second command runs the image using its configured default command. It is useful only if the image is expected to start in the foreground and does not require missing external services.

## Port Publishing and Connection Problems

A service running inside a container is not automatically reachable from the host. Verify both that the application is listening on the expected container port and that Docker publishes that port as intended.

```powershell
docker ps

docker port my-container
docker inspect --format '{{json .NetworkSettings.Ports}}' my-container
```

Common causes include:

- The container port was not published with `-p` or the equivalent Compose `ports` setting.
- The host port is already in use.
- The application listens only on `127.0.0.1` inside the container instead of an interface reachable through the container network, commonly `0.0.0.0` for an HTTP service.
- The host port and container port have been confused. In `-p 8080:80`, `8080` is the host port and `80` is the container port.
- A host firewall, VPN, proxy, or platform-specific network configuration is affecting access.

For a local-only development service, publish to the loopback interface:

```powershell
docker run --detach --publish 127.0.0.1:8080:80 --name troubleshoot-nginx nginx:alpine
```

Then test from the host:

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 8080
```

Open `http://localhost:8080` in a browser. When finished, stop and remove the test container:

```powershell
docker rm --force troubleshoot-nginx
```

If port 8080 is busy, choose another host port and update the test URL. Do not expose a service on all host interfaces unless the exposure is intended and appropriately protected.

## Container-to-Container Networking

Containers should generally communicate using service names on a shared user-defined network or a shared Compose network, rather than relying on hard-coded container IP addresses.

Check available networks and the networks attached to a container:

```powershell
docker network ls
docker inspect my-container
```

For Compose, use the service name and the service's container port for internal communication. For example, an API service can usually connect to a database service named `db` on port `5432`, even when the database port is not published to the host.

Typical mistakes include:

- Using `localhost` from one container to reach a different container. Inside a container, `localhost` means that same container.
- Putting the services on separate networks without a route between them.
- Using a published host port for service-to-service communication when the Compose service name and container port are appropriate.
- Starting an application before its dependency is ready, or failing to retry a temporary connection failure.

For a deeper explanation, see [Docker Networking](04-networking.md) and [Docker Compose](07-docker-compose.md).

## Volume and Bind Mount Problems

When expected files are missing, empty, or unexpectedly replaced, inspect the mounts before deleting or recreating anything.

```powershell
docker inspect --format '{{json .Mounts}}' my-container
docker volume ls
```

Check the mount type, host source, container destination, read/write setting, and permissions. A bind mount can obscure files that already existed at the target path inside the image. A named volume can also contain older data that is different from the files currently in the image.

On Windows with Docker Desktop, confirm that the source path exists and that the selected host directory is available to Docker Desktop. With `--mount type=bind`, a missing source path normally causes an error instead of silently creating the directory.

**Do not run `docker compose down -v` or `docker volume prune` as a first troubleshooting step.** Those operations can delete persistent data. Identify the affected volume and create or verify a backup before attempting any destructive storage operation.

For details, see [Volumes and Storage](05-volumes-and-storage.md).

## Docker Compose Problems

### Validate the Effective Configuration

Compose files can include variable interpolation and overrides. Validate the configuration before starting services:

```powershell
docker compose config --quiet
docker compose config
```

The first command checks the configuration quietly. The second prints the resolved configuration, which helps reveal merged settings and interpolation results. Treat the output as potentially sensitive if configuration values contain credentials.

### Inspect Service State and Logs

```powershell
docker compose ps --all
docker compose logs --tail 100
docker compose logs --follow api
```

Replace `api` with the actual service name. If a service fails, inspect its logs and configuration rather than assuming that all services failed for the same reason.

### A Dependency Is Not Ready

A service being started does not always mean it is ready to accept requests. Use health checks and appropriate `depends_on` conditions when supported by the service design, and ensure the application handles temporary dependency failures.

For example, a database process may be running while initialization is still in progress. A dependent API should not assume that the database can accept connections merely because its container exists.

### Wrong File, Directory, or Project

Compose resolves relative paths from the Compose project/configuration context. Confirm the current directory and the exact file used if multiple Compose files are present.

```powershell
Get-Location
docker compose -f .\compose.yaml config --quiet
docker compose -f .\compose.yaml ps --all
```

Adjust the filename and path to your project. When multiple `-f` files are used, their merge order matters.

## Environment Variable Problems

When a variable appears unset or has an unexpected value, verify where it is defined and how it reaches the application.

```powershell
# Display the environment configured for a container
 docker inspect --format '{{json .Config.Env}}' my-container

# Print the effective Compose configuration
 docker compose config
```

These commands may reveal sensitive values. Do not paste their unredacted output into public issues, logs, or chat messages.

Common causes include:

- A variable exists in a local `.env` file but is not passed into the container environment.
- A variable name is misspelled or differs in case.
- PowerShell's environment and Compose's interpolation environment are being confused.
- A value is defined in multiple places and a higher-precedence source wins.
- The application reads the variable only at startup and the container was not recreated after a configuration change.
- A secret was incorrectly stored as a normal environment variable or committed to version control.

See [Environment Variables in Docker](06-environment-variables.md) for precedence and configuration details.

## Resource and Disk Problems

A container can become slow or fail because of memory limits, CPU constraints, full storage, or resource contention on the host.

```powershell
docker stats
docker system df
docker info
```

Look for memory usage near its configured limit, repeated restarts, unexpectedly large images, and disk usage growth. On Docker Desktop, also check the resources and disk capacity available to its virtualized environment.

Do not remove volumes or images blindly to reclaim space. First identify what consumes space and which data is safe to delete. Production workloads should use planned resource limits and monitoring rather than rely only on manual inspection.

## Cleanup Without Losing Data

Use the narrowest cleanup operation that addresses the issue. Review the target before confirming a destructive operation.

```powershell
# Stop and remove a specific container
 docker stop my-container
 docker rm my-container

# Remove a specific image (only if no longer needed)
 docker image rm my-image:tag

# List volumes before considering volume cleanup
 docker volume ls
```

Removing a container does not automatically remove a separately managed named volume. Conversely, deleting a volume can permanently remove data that is not backed up elsewhere.

`docker system prune` removes unused Docker resources, and additional flags broaden what may be removed. Read the command's prompt and documentation before proceeding. Avoid adding `--volumes` unless you have identified the unused volumes and are certain their data can be discarded.

## A Reusable Diagnostic Checklist

When reporting a Docker issue, collect the following information after removing secrets and private data:

- The exact command or Compose action that failed.
- The complete, relevant error message.
- Output of `docker version` and, when appropriate, `docker info`.
- Output of `docker ps -a` and the relevant container logs.
- Relevant sanitized output from `docker inspect`.
- The Dockerfile, Compose configuration, and `.dockerignore` when related to the failure.
- The operating system and Docker environment (for example, Docker Desktop on Windows).
- The steps to reproduce the issue and what you expected to happen.

Avoid sharing access tokens, passwords, private registry credentials, connection strings, `.env` files, or unredacted inspect output. A small reproducible example is often more useful than a large bundle of unrelated logs.

## Further Reading

- [Docker Troubleshooting](https://docs.docker.com/)
- [Docker CLI Reference](https://docs.docker.com/reference/cli/docker/)
- [Docker Compose CLI Reference](https://docs.docker.com/reference/cli/docker/compose/)
- [Docker Compose Configuration](https://docs.docker.com/reference/cli/docker/compose/config/)
- [Docker Storage](https://docs.docker.com/engine/storage/)
- [Docker Networking](https://docs.docker.com/engine/network/)
- [Docker Engine Logging](https://docs.docker.com/engine/logging/)

## Next Chapter

This is the final chapter in the introductory guide sequence. Continue by running the practical examples in [`examples/`](../examples/) and reviewing the configuration and security recommendations across the handbook.
