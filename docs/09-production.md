# Running Docker Workloads in Production

Running a container locally is only one part of operating an application reliably. Production workloads also need repeatable builds, controlled configuration, appropriate security boundaries, health checks, logs, resource limits, durable data, backups, and a deployment and rollback process.

This chapter is a practical checklist for preparing containerized applications for production. The right configuration depends on the application, the host, the threat model, and the deployment platform. Treat the examples as starting points to review and test, not as a universal production configuration.

## Table of Contents

- [What Production Readiness Means](#what-production-readiness-means)
- [Build Repeatable Images](#build-repeatable-images)
- [Choose and Manage Image Tags](#choose-and-manage-image-tags)
- [Configure Applications at Runtime](#configure-applications-at-runtime)
- [Run with Least Privilege](#run-with-least-privilege)
- [Health Checks and Readiness](#health-checks-and-readiness)
- [Restart Policies and Graceful Shutdown](#restart-policies-and-graceful-shutdown)
- [Resource Limits](#resource-limits)
- [Logging and Observability](#logging-and-observability)
- [Networking and TLS](#networking-and-tls)
- [Persistent Data and Backups](#persistent-data-and-backups)
- [Deploying with Docker Compose](#deploying-with-docker-compose)
- [Continuous Integration and Delivery](#continuous-integration-and-delivery)
- [Rollback and Recovery](#rollback-and-recovery)
- [Production Readiness Checklist](#production-readiness-checklist)
- [Common Mistakes](#common-mistakes)
- [Further Reading](#further-reading)

## What Production Readiness Means

A production deployment should be designed for change and failure. Containers may be recreated, hosts may restart, dependencies may become unavailable, and new application versions may need to be rolled back.

A production-ready setup should answer these questions:

- Can the same source revision and build instructions produce a traceable image?
- Are configuration and credentials kept separate from the image?
- Does the application run with only the privileges it needs?
- Can operators tell whether the service is working, not merely running?
- Are logs retained and resource usage observable?
- Is important data stored and backed up independently of a replaceable container?
- Is there a documented deployment and rollback procedure?

Docker provides useful building blocks, but a Docker image or Compose file alone does not provide a complete high-availability platform, secret-management system, monitoring stack, or backup strategy.

## Build Repeatable Images

Build images from version-controlled source and a reviewed Dockerfile. Keep the build context small, install only required runtime dependencies, and avoid copying local development artifacts into the image.

A `.dockerignore` file for a Python application might contain:

```text
.git/
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.env
.env.*
!.env.example
coverage/
dist/
build/
```

Adjust the list to match the application. Do not exclude files that the build actually requires, and never rely on `.dockerignore` as the only protection for secrets already committed to version control.

For an application with compiled assets or build-only dependencies, consider a multi-stage Dockerfile so the final image contains only the runtime files and dependencies it needs.

```dockerfile
# Example only: adapt dependencies and startup command to the application.
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=10001:10001 . .
USER 10001:10001

EXPOSE 8000
CMD ["python", "app.py"]
```

This example assumes the application has a compatible `requirements.txt` and `app.py`. A real Django or FastAPI service should use its intended production server command and should be tested with its actual dependencies. The numeric user must also be compatible with the base image and any mounted files.

Build and inspect the image locally:

```powershell
# Run from the directory containing the Dockerfile.
docker build --tag example-api:local .
docker image inspect example-api:local
docker image ls
```

For production, build through a repeatable CI process and record the source revision and image identifier. Do not use a developer's unreviewed local image as the only release artifact.

## Choose and Manage Image Tags

Avoid relying on a mutable tag such as `latest` to identify a release. A tag is a readable label, but the tag can point to a different image later.

A practical release process can use versioned tags such as:

```text
registry.example.com/team/api:1.4.2
registry.example.com/team/api:git-a1b2c3d
```

These are illustrative names, not real registry locations. In CI, tag an image with the release version and/or source revision, and promote the exact artifact that was tested. For stronger identity guarantees, record or deploy by image digest where supported.

Choose maintained base images from trusted publishers, update them deliberately, rebuild when security updates are needed, and scan both application dependencies and container images. Do not assume that a smaller image is automatically safe or that a successful build means the image is vulnerability-free.

## Configure Applications at Runtime

Keep environment-specific configuration outside the image. The same image should be deployable to different environments by changing runtime configuration rather than rebuilding it for each environment.

Configuration may include a log level, public service URL, feature flag, or database connection settings. Credentials such as database passwords, API tokens, and private keys require stronger handling than ordinary configuration.

For example, a Compose service can receive non-sensitive settings at runtime:

```yaml
services:
  api:
    image: registry.example.com/team/api:1.4.2
    environment:
      APP_ENV: production
      LOG_LEVEL: info
```

Do not put real secrets in a committed Compose file, Dockerfile, image label, command-line argument, or public example. Environment variables can be exposed through process inspection, diagnostic output, crash reports, or application logs. Use the secret-management mechanism supported by your deployment platform and restrict who can read it.

See [Environment Variables](06-environment-variables.md) for variable syntax, `.env` files, interpolation, and precedence.

## Run with Least Privilege

A production container should have only the permissions it requires.

- Run the application as a non-root user when practical.
- Avoid `privileged: true` and broad Linux capabilities unless a reviewed requirement justifies them.
- Do not mount the Docker socket into an application container unless the design explicitly requires Docker API access and its risk is understood.
- Avoid mounting sensitive host directories into containers.
- Publish only required ports, preferably on the intended host interface.
- Consider a read-only root filesystem and narrowly scoped writable mounts when the application supports them.
- Keep the host, Docker Engine, base images, and application dependencies patched.

A read-only filesystem or non-root user can expose assumptions in an application that writes to arbitrary directories. Test these restrictions before production and provide explicit writable paths for temporary files, uploads, or generated data when required.

See [Docker Security](08-security.md) for a more detailed security guide.

## Health Checks and Readiness

A container being in the `running` state does not necessarily mean its application is ready to serve traffic. The main process can run while the HTTP server is not accepting requests, a database connection is unavailable, or startup tasks have failed.

Where appropriate, implement an application health endpoint and configure a health check that matches the image. The probe command must exist in the image; do not assume tools such as `curl` or `wget` are installed.

Example Compose configuration for an API image that includes Python and exposes `/health/`:

```yaml
services:
  api:
    image: registry.example.com/team/api:1.4.2
    healthcheck:
      test:
        - CMD
        - python
        - -c
        - "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/', timeout=2)"
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 20s
```

This sample assumes the application implements `/health/` and that Python is available in the runtime image. Adapt the endpoint and probe to the application. Avoid a health check that depends on an external service if a transient external outage should not mark the whole process unhealthy.

Distinguish between:

- **Liveness:** whether the process should continue running or be restarted.
- **Readiness:** whether it should receive application traffic now.

Docker health status does not automatically provide a load balancer, remove traffic from every routing layer, or restart a container simply because the health status becomes `unhealthy`. Confirm how your deployment platform uses health information.

## Restart Policies and Graceful Shutdown

Restart policies can bring a container back after certain exits or Docker daemon restarts. For a long-running service, a policy such as `unless-stopped` is a common starting point:

```yaml
services:
  api:
    image: registry.example.com/team/api:1.4.2
    restart: unless-stopped
```

Restart policies do not fix a broken application, repair bad configuration, or replace monitoring. A process that repeatedly crashes may enter a restart loop and still require operator intervention.

Applications should handle termination signals and shut down cleanly. On shutdown, a service may need to stop accepting new requests, finish in-flight work within a reasonable timeout, close database connections, and flush logs. Use an appropriate container entry point and process model so the application receives termination signals correctly.

When configuring `stop_grace_period` in Compose or `--stop-timeout` for `docker stop`, choose a duration based on the application's shutdown behavior and workload.

Official reference: [Start containers automatically](https://docs.docker.com/engine/containers/start-containers-automatically/).

## Resource Limits

A container without configured limits can consume more host resources than intended. Measure realistic workloads before setting limits: overly restrictive values can cause failed requests, slow responses, process termination, or application instability.

Example runtime limits:

```powershell
docker run --detach `
    --name api-limited `
    --memory 512m `
    --cpus 1.0 `
    nginx:alpine
```

This is a demonstration using Nginx, not a universal sizing recommendation. Choose CPU and memory settings based on measurements and host capacity. Resource-limit behavior depends on support from the Docker host and its kernel or virtualization layer.

Review actual usage with:

```powershell
docker stats
docker inspect api-limited
```

If you run the example, clean it up afterward:

```powershell
docker stop api-limited
docker rm api-limited
```

Avoid setting production limits by guesswork. Observe normal traffic, startup peaks, scheduled tasks, and failure behavior before settling on limits.

## Logging and Observability

Prefer application logs written to standard output and standard error so the container runtime can collect them. Include useful context such as timestamps, severity, request or trace identifiers, and service name, while excluding credentials and sensitive personal data.

Useful commands during an incident include:

```powershell
docker logs --tail 200 api-container
docker logs --follow api-container
docker stats
docker inspect api-container
```

Replace `api-container` with the actual container name or ID.

Production operations should define log retention, storage capacity, access control, alerting, and a way to search logs across instances. Docker logging driver behavior and delivery capabilities vary by driver and configuration. Configure rotation or use a centralized logging system so noisy services do not consume all available disk space.

Metrics and traces complement logs. Monitor application-specific signals such as request rate, latency, error rate, queue depth, database connection failures, and saturation of CPU, memory, and storage.

See [Configure logging drivers](https://docs.docker.com/engine/logging/configure/) for Docker's logging options.

## Networking and TLS

Expose only the ports that must be reachable. A backend database usually does not need a public host port if only an API container should access it on a private Docker network.

For example, to bind a local development service only to the host loopback interface:

```powershell
docker run --detach `
    --name local-nginx `
    --publish 127.0.0.1:8080:80 `
    nginx:alpine
```

This example is for local access and should not be confused with a complete production ingress setup. Remove the test container after use:

```powershell
docker stop local-nginx
docker rm local-nginx
```

For public HTTP services, plan how TLS certificates are issued, renewed, and loaded; where the reverse proxy or load balancer runs; and how internal services are isolated. Do not assume that a port is private merely because the application is running in a container. See [Docker Networking](04-networking.md).

## Persistent Data and Backups

Containers should be replaceable, while important state should be kept in appropriate persistent storage. Databases commonly use named volumes or externally managed storage, but persistence alone is not a backup.

Define and test:

- What data is critical and who owns it.
- Backup frequency and retention.
- Encryption and access controls for backup artifacts.
- Recovery procedures and target recovery time and data-loss limits.
- Restore tests in an isolated environment.

A backup is only useful if it can be restored. For databases, use database-aware backup and recovery methods appropriate to the engine and consistency requirements. Do not assume that copying a live data directory is always a valid backup.

Before deleting a volume or running a cleanup command, identify which services use it and whether the data has been backed up. See [Volumes and Storage](05-volumes-and-storage.md).

## Deploying with Docker Compose

Docker Compose is useful for defining a group of related services on a single Docker host. It can make configuration reviewable and deployments repeatable, but it is not by itself a complete multi-host orchestration or high-availability system.

A simplified production-oriented Compose fragment might look like this:

```yaml
services:
  api:
    image: registry.example.com/team/api:1.4.2
    restart: unless-stopped
    init: true
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      APP_ENV: production
      LOG_LEVEL: info
    healthcheck:
      test:
        - CMD
        - python
        - -c
        - "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/', timeout=2)"
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 20s
```

This fragment is a template, not a complete production deployment. It assumes the image contains Python, listens on port 8000, and implements `/health/`. The loopback port binding assumes a local reverse proxy or another trusted ingress process on the same host. Adapt ports, health checks, environment configuration, resource controls, secrets, and ingress to your deployment environment.

Before deploying, validate the resolved Compose configuration and check the image reference:

```powershell
docker compose config
docker compose pull
docker compose up --detach
```

Use `docker compose up --detach` only after deciding how the new image was built, pushed, and tested. A deployment workflow should also define migrations, readiness checks, rollback, and data compatibility between application versions.

## Continuous Integration and Delivery

A CI/CD pipeline should use a controlled sequence appropriate to the application:

1. Check out a specific source revision.
2. Run linting, unit tests, and application-level checks.
3. Build the container image using the version-controlled Dockerfile.
4. Scan dependencies and the image using the organization's chosen tooling.
5. Tag and publish the tested image to an authenticated registry.
6. Deploy the exact image reference to the target environment.
7. Verify health and key application behavior.
8. Stop or roll back the release if verification fails, following a documented procedure.

Do not put registry credentials or deployment secrets in repository files or build arguments. Use the CI platform's secret store and short-lived credentials where supported. Restrict who can publish images and trigger production deployments, and protect the release workflow as carefully as application code.

## Rollback and Recovery

Before every production release, know how to return to a previous known-good image. Record the version or digest that was deployed and keep release artifacts available according to the project's retention policy.

Rollback may require more than changing the image. Database schema changes, data migrations, message formats, and external integrations can make older application versions incompatible. Prefer backward-compatible changes where practical and document recovery steps for migrations that cannot be reversed safely.

A rollback plan should specify:

- Who is authorized to initiate it.
- How the previous image and configuration are selected.
- Which health and business checks must pass afterward.
- How database or uploaded-file state is protected.
- How the incident and follow-up actions are documented.

## Production Readiness Checklist

Use this checklist during release review:

- [ ] The image is built from a reviewed, version-controlled Dockerfile.
- [ ] The image reference is versioned and the released artifact is traceable.
- [ ] Base images and dependencies are maintained and scanned according to policy.
- [ ] The application runs with least privilege and without unnecessary capabilities.
- [ ] Secrets are managed outside the source code and image layers.
- [ ] Only required ports are reachable from intended networks.
- [ ] Health checks, readiness behavior, and graceful shutdown are understood.
- [ ] CPU and memory needs have been measured and reasonable limits applied where supported.
- [ ] Logs, metrics, alerts, and retention are configured.
- [ ] Persistent data is stored appropriately and backups have been restore-tested.
- [ ] Deployment, database migrations, and rollback have documented procedures.
- [ ] The release has been verified in an environment representative of production.

Not every workload needs identical controls. Record justified exceptions and revisit them when the application or threat model changes.

## Common Mistakes

**Using `latest` as the only record of a release.** Mutable tags make it harder to identify exactly what was deployed. Use release tags and record the image digest when possible.

**Treating a running container as proof that an application is healthy.** Check application-level health and real requests, not just process state.

**Assuming restart policies replace monitoring.** Restarts do not explain why a service failed or ensure that it is functioning correctly afterward.

**Logging secrets.** Redact sensitive values from logs, error messages, traces, and diagnostic output.

**Deleting volumes during cleanup without review.** A volume may contain irreplaceable production data. Verify ownership and backup status before removing it.

**Deploying without a rollback plan.** Keep a known-good image reference and account for database and data compatibility before a release.

**Assuming Compose alone provides production high availability.** Evaluate host failure, traffic routing, deployment coordination, backups, and recovery requirements separately.

## Further Reading

- [Docker Build Best Practices](https://docs.docker.com/build/building/best-practices/)
- [Docker Engine Security](https://docs.docker.com/engine/security/)
- [Start Containers Automatically](https://docs.docker.com/engine/containers/start-containers-automatically/)
- [Resource Constraints](https://docs.docker.com/engine/containers/resource_constraints/)
- [Configure Logging Drivers](https://docs.docker.com/engine/logging/configure/)
- [Control Startup and Shutdown Order in Compose](https://docs.docker.com/compose/how-tos/startup-order/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

## Next Chapter

Continue with [Troubleshooting](10-troubleshooting.md) to learn practical techniques for diagnosing failed builds, stopped containers, networking problems, storage issues, and application errors.
