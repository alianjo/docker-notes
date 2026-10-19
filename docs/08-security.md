# Docker Security

Docker security is not a single setting. It depends on the host, the Docker daemon, image provenance, container configuration, application behavior, network exposure, and how sensitive data is handled. This chapter introduces practical safeguards for local development and production workloads.

The examples are intended for learning and should be adapted to the application and environment. A command that works for one image may not work for another because applications have different filesystem, user, and capability requirements.

## Table of Contents

- [Security Principles](#security-principles)
- [Understand the Docker Security Boundary](#understand-the-docker-security-boundary)
- [Use Trusted and Maintained Images](#use-trusted-and-maintained-images)
- [Run Applications as a Non-Root User](#run-applications-as-a-non-root-user)
- [Reduce Container Privileges](#reduce-container-privileges)
- [Protect the Docker Daemon and Socket](#protect-the-docker-daemon-and-socket)
- [Handle Secrets Safely](#handle-secrets-safely)
- [Secure the Build Process](#secure-the-build-process)
- [Limit Network Exposure](#limit-network-exposure)
- [Keep the Filesystem and Resources Constrained](#keep-the-filesystem-and-resources-constrained)
- [Scan Images for Vulnerabilities](#scan-images-for-vulnerabilities)
- [Security in Docker Compose](#security-in-docker-compose)
- [Practical Security Checklist](#practical-security-checklist)
- [Common Mistakes](#common-mistakes)
- [Key Takeaways](#key-takeaways)
- [Further Reading](#further-reading)

## Security Principles

Use defense in depth: apply several complementary controls rather than relying on a single option.

- **Least privilege:** give each process and service only the permissions it needs.
- **Reduce attack surface:** remove unused packages, tools, ports, and services.
- **Protect secrets:** keep credentials out of source control, image layers, logs, and build arguments.
- **Patch regularly:** update base images, dependencies, Docker Engine, and supporting tools.
- **Limit exposure:** publish only required ports and restrict access where possible.
- **Verify changes:** inspect configurations, scan images, and test security controls as part of development and CI.

A running container is not automatically secure. Containers provide useful isolation, but they share the host kernel in common configurations and must be configured and maintained carefully.

## Understand the Docker Security Boundary

Docker relies on several operating-system features, including namespaces and control groups, to isolate processes and manage resources. Additional controls can include Linux capabilities, seccomp, AppArmor, SELinux, user namespace mapping, and rootless mode, depending on the platform and configuration.

A few important distinctions:

- Root inside a container is not identical to root on the host in every configuration, but a process with elevated container privileges can still create serious risk.
- Containers generally share the kernel supplied by the host environment. On Docker Desktop, Linux containers run inside a managed Linux environment.
- A compromised application can still expose data, credentials, or services that are accessible to it.
- Docker daemon access is highly privileged. A user who can control the daemon may be able to create containers that access sensitive host resources.

For these reasons, do not treat containers as a substitute for host security, application authorization, or careful deployment design.

## Use Trusted and Maintained Images

Choose images from trusted publishers and verify that they are appropriate for your application. Prefer maintained images, review their documentation, and update them when security fixes are available.

Pulling and inspecting an image:

```powershell
# Download an image from its configured registry
docker pull python:3.13-slim

# Review local image metadata
docker image inspect python:3.13-slim

# Review local image names, tags, and sizes
docker image ls
```

The example uses an explicit tag, but a tag can be moved to a different image over time. For stronger reproducibility, consider pinning an image by digest and deliberately updating that digest as part of maintenance.

Use the smallest suitable base image, but do not choose an image solely because it is small. Confirm that it is maintained and contains the runtime and libraries your application needs. Minimal images can reduce the attack surface, but they do not guarantee security.

## Run Applications as a Non-Root User

When an application does not require root privileges, configure it to run as a dedicated non-root user. This reduces the permissions available if the application is compromised.

Example Dockerfile for a Python application:

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system app && \
    useradd --system --gid app --create-home app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app . .
USER app

CMD ["python", "app.py"]
```

This is a starting point, not a universal production Dockerfile. It assumes the chosen base image includes the user-management commands shown, that `requirements.txt` exists, and that `app.py` is the correct entry point. Adapt it to the framework and deployment requirements.

Check the configured user for a built image:

```powershell
docker image inspect --format '{{.Config.User}}' my-app:local
```

An empty result can mean the image does not explicitly set a user; it does not, by itself, prove what the application does after startup.

## Reduce Container Privileges

Avoid `--privileged` unless a specific, justified use case requires it. It grants broad additional access and weakens several default isolation controls.

Where the application supports it, consider dropping Linux capabilities, preventing privilege escalation, and limiting process counts. For example:

```powershell
docker run --rm `
    --cap-drop=ALL `
    --security-opt=no-new-privileges=true `
    --pids-limit=100 `
    python:3.13-slim `
    python -c "print('Container started with reduced privileges')"
```

This is a short demonstration using a simple Python process. It is not a drop-in configuration for every application. Some software legitimately needs particular capabilities or writable paths; grant only what is justified and test the result.

Other considerations:

- Do not use host PID, host network, or host IPC namespaces without a clear reason.
- Keep Docker's default seccomp profile enabled unless a documented requirement justifies a change.
- Use the host's supported AppArmor or SELinux protections where available.
- Consider rootless Docker where it fits the environment and its operational requirements.
- Avoid granting devices or mounting host paths into a container unnecessarily.

## Protect the Docker Daemon and Socket

The Docker daemon can create containers, mount host directories, and access other powerful resources. Access to the Docker socket should therefore be treated as a privileged capability.

Avoid casually mounting the host socket into an application container:

```yaml
# Avoid this pattern for ordinary application containers.
services:
  app:
    image: my-app:local
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

A process with access to the socket may be able to instruct the daemon to create highly privileged containers or mount sensitive host paths. Do not expose an unauthenticated Docker API over TCP.

Recommended practices:

- Give Docker daemon access only to trusted users and automation.
- Review membership of the `docker` group on Linux; it is effectively highly privileged.
- Do not expose the daemon API to untrusted networks.
- Use secure transport and appropriate authentication if remote Docker access is required.
- Keep Docker Engine and Docker Desktop updated.
- Consider rootless mode when its compatibility and operational trade-offs are appropriate.

## Handle Secrets Safely

Secrets include database passwords, API tokens, private keys, signing keys, and certificates. They should not be committed to source control or embedded in an image.

### Avoid secrets in Dockerfiles

Do not write credentials as literal values in Dockerfile instructions:

```dockerfile
# Do not do this.
ENV DATABASE_PASSWORD="example-password"
```

Do not pass secret values through Dockerfile `ARG` for build-time authentication either. Build arguments and environment variables are not appropriate secret-delivery mechanisms because sensitive values can be exposed through build metadata, image configuration, logs, or layers depending on how they are used.

### Keep local configuration out of version control

Use `.gitignore` and `.dockerignore` to reduce accidental disclosure. For example:

```gitignore
.env
.env.*
!.env.example
secrets/
```

```dockerignore
.git
.env
.env.*
secrets/
__pycache__/
*.py[cod]
.venv/
venv/
node_modules/
```

Adapt both files to the repository. A `.gitignore` rule prevents matching files from being added to Git in normal workflows; `.dockerignore` prevents matching files from entering the Docker build context. Neither can remove a secret that has already been committed or leaked. Rotate exposed credentials and clean up affected history where appropriate.

An `.env.example` should contain variable names and safe placeholders only, never real credentials.

### Prefer Compose secrets when supported

Docker Compose supports granting selected secrets to specific services as mounted files. This can be preferable to passing sensitive values in environment variables, but local Compose secrets are not automatically a full external secrets-management platform. Protect source secret files, host permissions, backups, and deployment infrastructure too.

Example configuration:

```yaml
services:
  api:
    image: my-api:local
    secrets:
      - db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

The application can read the secret from `/run/secrets/db_password` inside the container. The secret file must exist, remain outside version control, and be accessible to the intended Docker environment. Support and behavior depend on the container platform and deployment mode.

For secrets needed only during image builds, use BuildKit secret mounts rather than `ARG` or `ENV`:

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine:3.22
RUN --mount=type=secret,id=artifact_token \
    token_file=/run/secrets/artifact_token && \
    test -s "$token_file" && \
    echo "Secret was mounted for this build step"
```

Build command example for a local file:

```powershell
docker build --secret id=artifact_token,src=secrets\artifact_token.txt -t example-build:local .
```

Use a valid relative or absolute path for `src`, such as `secrets\artifact_token.txt`. The example Dockerfile illustrates the mount mechanism only. It does not authenticate to a registry or use the token. BuildKit secret mounts make the secret temporarily available to the build instruction; your build command and Dockerfile must be configured to use the correct secret ID.

## Secure the Build Process

The build process is part of the application's security boundary. A Docker image may contain application source, installed dependencies, OS packages, metadata, and files copied from the build context.

Recommended practices:

- Review the files included in the build context.
- Keep credentials and local configuration out of the build context with `.dockerignore`.
- Use multi-stage builds when appropriate to keep compilers, temporary files, and build-only dependencies out of the final image.
- Prefer explicit base-image tags and use digests when stronger pinning is required.
- Keep dependencies and base images updated.
- Avoid running arbitrary scripts from untrusted sources during a build.
- Use BuildKit secret mounts for build-time credentials.
- Review the final image contents rather than assuming files were excluded just because they were deleted in a later layer.

A `.dockerignore` file does not replace careful Dockerfile design. For more detail, see the official [build best practices](https://docs.docker.com/build/building/best-practices/) and [build secrets](https://docs.docker.com/build/building/secrets/) documentation.

## Limit Network Exposure

Publish only the ports that need to be reachable. For a service intended only for local development, bind to the host loopback interface where possible:

```powershell
docker run --detach --publish 127.0.0.1:8080:80 --name local-web nginx:alpine
```

This maps host port `8080` to container port `80` and binds the host side to `127.0.0.1`. It is useful for a local-only test; it is not a complete production network policy.

Check published ports with:

```powershell
docker ps
```

For multi-container applications, put related services on an appropriate user-defined network. A database generally does not need a host-published port when only the API container needs to reach it. Network reachability should be combined with authentication, authorization, and service-level security.

## Keep the Filesystem and Resources Constrained

A read-only root filesystem can prevent an application from modifying parts of its container filesystem. Applications that need temporary files must be configured with suitable writable mounts.

Example command using a read-only root filesystem and a temporary writable directory:

```powershell
docker run --rm `
    --read-only `
    --tmpfs /tmp:rw,noexec,nosuid,size=64m `
    --cap-drop=ALL `
    --security-opt=no-new-privileges=true `
    --pids-limit=100 `
    python:3.13-slim `
    python -c "print('Read-only root filesystem example')"
```

This is a learning example. Applications may require other writable paths or capabilities. Test these controls before applying them to a real service.

Where appropriate, set and monitor CPU and memory constraints to reduce the impact of a runaway process. Resource limits and their exact behavior depend on the host, runtime, and configuration.

## Scan Images for Vulnerabilities

Image scanning helps identify known vulnerabilities in packages included in an image. Scanning is useful, but it does not prove that an image or application is secure. Review findings, assess severity and exploitability, and apply relevant updates.

If Docker Scout is available in your Docker environment, you can inspect image vulnerabilities with commands such as:

```powershell
docker scout --help
docker scout cves python:3.13-slim
```

Availability and behavior can depend on Docker tooling, authentication, image source, and product entitlements. Consult the [Docker Scout documentation](https://docs.docker.com/scout/) for current setup and usage instructions.

Other scanners can inspect OS packages, language dependencies, configuration, and source code. Choose tools that fit your CI process and review their output rather than relying on a single scan.

## Security in Docker Compose

Compose lets you define security-related settings alongside services. The following example illustrates several controls that may fit a simple web API:

```yaml
services:
  api:
    image: my-api:local
    read_only: true
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    pids_limit: 100
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=64m
```

This is illustrative configuration rather than a universal drop-in recipe. The image must support read-only operation, run without unnecessary capabilities, and have the required writable paths mounted. Test the configuration before adopting it.

Additional Compose practices:

- Avoid publishing internal database ports unless external access is needed.
- Do not store secret values directly in `compose.yaml`.
- Use Compose secrets or a dedicated secret manager as appropriate for the deployment environment.
- Avoid `privileged: true` for normal application containers.
- Be deliberate about host bind mounts and ensure their paths and permissions are appropriate.
- Keep the Compose file, Dockerfiles, and deployment configuration under review.

## Practical Security Checklist

Before sharing or deploying an image, check the following:

- [ ] The base image comes from a trusted source and is maintained.
- [ ] Dependencies and OS packages are reviewed and updated regularly.
- [ ] The application runs as a non-root user when practical.
- [ ] No credentials are embedded in the Dockerfile, image, repository, or build context.
- [ ] Build-time secrets use secret mounts rather than build arguments or environment variables.
- [ ] Only required ports are published, preferably on the intended host interface.
- [ ] The container does not use `--privileged` without a documented need.
- [ ] Unnecessary Linux capabilities are dropped when compatible.
- [ ] Docker socket access and host filesystem mounts are tightly controlled.
- [ ] Persistent data and secret files have appropriate permissions and backup handling.
- [ ] Image vulnerability findings are reviewed and remediated as applicable.
- [ ] The deployment's logging, monitoring, update, and incident-response practices are defined.

## Common Mistakes

**Running every application as root.** Prefer a dedicated non-root user unless the application requires otherwise.

**Embedding credentials in `ENV` or `ARG`.** Neither is a suitable secret store. Use appropriate secret-delivery mechanisms.

**Mounting the Docker socket into an ordinary application container.** This can grant extensive control over the daemon and host resources.

**Publishing every service port.** Databases and internal services should usually be reachable only by the services that need them.

**Assuming a small image is secure.** Small images can still contain vulnerable packages or unsafe application behavior.

**Treating a successful vulnerability scan as a security guarantee.** Scanners detect known issues within their scope and may not identify every risk.

**Enabling restrictive controls without testing.** Read-only filesystems, dropped capabilities, and process limits can break applications that rely on writable paths or specific privileges. Test and document required exceptions.

## Key Takeaways

- Docker security relies on several layers: trusted images, least privilege, a protected daemon, secure build practices, network controls, and safe secret handling.
- Prefer non-root processes and avoid unnecessary privileges.
- Keep secrets out of image layers, source control, and build arguments.
- Use BuildKit secret mounts for build-time credentials and Compose secrets or suitable external services for runtime secrets.
- Publish only required ports and restrict daemon access.
- Scan and update images, then investigate findings rather than assuming scanning alone is sufficient.
- Test security controls against the actual application before deployment.

## Further Reading

- [Docker Engine Security](https://docs.docker.com/engine/security/)
- [Rootless Mode](https://docs.docker.com/engine/security/rootless/)
- [Docker Build Best Practices](https://docs.docker.com/build/building/best-practices/)
- [Build Secrets](https://docs.docker.com/build/building/secrets/)
- [Manage Secrets in Docker Compose](https://docs.docker.com/compose/how-tos/use-secrets/)
- [Docker Scout](https://docs.docker.com/scout/)

## Next Chapter

Continue with [Production](09-production.md) after reviewing this chapter. For the multi-container workflow that supports these controls, see [Docker Compose](07-docker-compose.md).
