# Dockerfile: Build Reliable Images

A `Dockerfile` is a text file containing instructions that Docker uses to build an image. A well-designed Dockerfile makes application builds easier to understand, repeat, cache, and maintain.

This chapter covers the most common instructions, build context, layer caching, `.dockerignore`, a practical Python example, multi-stage builds, and security-oriented practices.

## Table of Contents

- [What Is a Dockerfile?](#what-is-a-dockerfile)
- [The Build Context](#the-build-context)
- [Core Dockerfile Instructions](#core-dockerfile-instructions)
- [Build an Image](#build-an-image)
- [Use a .dockerignore File](#use-a-dockerignore-file)
- [Understand Layer Caching](#understand-layer-caching)
- [A Practical Python Dockerfile](#a-practical-python-dockerfile)
- [Multi-Stage Builds](#multi-stage-builds)
- [Common Mistakes](#common-mistakes)
- [Dockerfile Best Practices](#dockerfile-best-practices)
- [Useful Commands](#useful-commands)
- [Key Takeaways](#key-takeaways)
- [Further Reading](#further-reading)

## What Is a Dockerfile?

A Dockerfile describes how to assemble an image from a base image, files, dependencies, and configuration. Docker processes the instructions in order as part of the image build.

For example:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

This example assumes that `requirements.txt` and `app.py` exist in the build context. It is an introductory example, not a complete production template: for a real service, also consider a suitable non-root user, dependency pinning, health checks where appropriate, and secrets handling.

## The Build Context

The **build context** is the set of files that the builder can access when building an image. In the following command, the final `.` selects the current directory as the build context:

```powershell
docker build -t notes-demo:local .
```

A `COPY` instruction can only copy files that are available in the build context, subject to ignore rules. A path outside that context cannot normally be copied into the image by writing `COPY ../some-file ...`.

Keep the context as small as practical. Large or unnecessary contexts slow builds, can reduce cache efficiency, and may expose files to the build process that do not need to be there.

## Core Dockerfile Instructions

### `FROM`

Selects the base image for a build stage. Most Dockerfiles begin with `FROM`.

```dockerfile
FROM python:3.13-slim
```

Choose an appropriate, maintained image for your application. A tag such as `3.13-slim` is more specific than `latest`, but it can still point to a newer image over time. For stricter reproducibility, consider pinning an image digest and plan how to update it safely.

### `WORKDIR`

Sets the working directory for subsequent relevant instructions, including `RUN`, `COPY`, `ADD`, `CMD`, and `ENTRYPOINT`.

```dockerfile
WORKDIR /app
```

Docker creates the directory if it does not exist. Using an explicit working directory is clearer than relying on the image's default directory.

### `COPY`

Copies files or directories from the build context, or from another build stage, into the image.

```dockerfile
COPY requirements.txt .
COPY app.py .
```

Prefer `COPY` for ordinary local files because its behavior is explicit.

### `ADD`

`ADD` can do more than copy local files: depending on the source, it can automatically extract local tar archives and support remote sources. Prefer `COPY` unless you need a specific `ADD` behavior. Explicit download and verification steps are often easier to review than an implicit remote download.

### `RUN`

Executes a command during the image build, such as installing dependencies or creating directories.

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

A `RUN` instruction affects the built image. It is different from a command executed after the container starts.

For Debian-based images, package installation is often written as a single instruction so package indexes are refreshed and cleaned in the same layer:

```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
```

Use commands appropriate to the selected base image. The example above is for Debian-based images and is not suitable for Alpine without changes.

### `CMD`

Defines the default command or arguments used when a container starts. A Dockerfile can have only one effective `CMD`; if more than one appears, the last one takes effect.

```dockerfile
CMD ["python", "app.py"]
```

The JSON-array form is known as **exec form**. It runs the executable directly and is generally preferred for application processes.

### `ENTRYPOINT`

Defines the executable that the container is intended to run. It is often combined with `CMD` to provide default arguments.

```dockerfile
ENTRYPOINT ["python"]
CMD ["app.py"]
```

With this combination, the default command is `python app.py`. Arguments provided to `docker run` replace the default `CMD` arguments while retaining the exec-form entrypoint.

`CMD` and `ENTRYPOINT` serve different purposes. Choose their combination based on how you expect users or orchestration tools to invoke the image.

### `EXPOSE`

Documents the port on which the application is expected to listen inside the container.

```dockerfile
EXPOSE 8000
```

`EXPOSE` does **not** publish the port to the host by itself. Use `docker run -p` or the appropriate Compose port configuration to publish a port.

### `ENV`

Sets environment variables that are available to later build instructions and to containers created from the image.

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
```

Do not use `ENV` to embed passwords, tokens, or other secrets in an image. Environment values can be exposed through image metadata or container configuration.

### `ARG`

Defines a build-time variable that can be passed with `docker build --build-arg`.

```dockerfile
ARG APP_VERSION=dev
LABEL org.opencontainers.image.version=$APP_VERSION
```

`ARG` is useful for non-secret build-time settings. It is not a safe mechanism for passing secrets because build arguments may be exposed through build metadata or other build artifacts. Use BuildKit secret mounts for build-time secrets when needed.

### `USER`

Selects the user and, optionally, group used for subsequent instructions and the default container process.

```dockerfile
USER app
```

The user must exist in the image. For application images, running as a dedicated non-root user is a sensible default whenever the application supports it.

### `LABEL`

Adds metadata to an image in key-value form.

```dockerfile
LABEL org.opencontainers.image.title="Notes Demo"
```

Labels are useful for documenting ownership, source repositories, versions, and other image metadata.

## Build an Image

Create a directory containing a `Dockerfile` and the files it references. From that directory, run:

```powershell
docker build -t notes-demo:1.0 .
```

Breakdown:

- `docker build` starts an image build.
- `-t notes-demo:1.0` sets the image name and tag.
- `.` sets the build context to the current directory.

List the resulting image:

```powershell
docker image ls notes-demo
```

Inspect its metadata:

```powershell
docker image inspect notes-demo:1.0
```

Run it only after confirming that the example application and its expected command exist:

```powershell
docker run --rm notes-demo:1.0
```

If the application is a web server, use an appropriate port mapping, for example `-p 127.0.0.1:8000:8000`, and ensure the application listens on `0.0.0.0` inside the container. A service listening only on the container's loopback interface may not be reachable through a published port.

## Use a `.dockerignore` File

A `.dockerignore` file excludes matching paths from the build context. Place it at the root of the build context.

For a Python project, a starting point could be:

```text
.git/
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.coverage
.env
.env.*
!.env.example
```

Review these patterns for your project. For example, a file named `.env.example` can be useful documentation if it contains only placeholders, while real `.env` files should generally stay out of the context. Never assume `.dockerignore` is a substitute for checking what gets copied into an image.

Ignoring `.git`, local virtual environments, test caches, and real environment files can reduce the build context and help prevent accidental inclusion of local files. The exact patterns should reflect the files your application needs at build time.

## Understand Layer Caching

Docker can reuse cached results from earlier builds when the relevant instructions and inputs have not changed. Cache reuse often shortens rebuilds significantly.

Consider this dependency installation pattern:

```dockerfile
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

Application source files are copied after dependencies are installed. If only a source file changes, the dependency-installation step can often be reused. If `requirements.txt` changes, the dependency step normally needs to run again.

Compare that with this less cache-friendly order:

```dockerfile
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
```

A source-code change can invalidate the earlier `COPY` and cause the dependency installation step to run again.

Cache behavior depends on the instruction, its inputs, the base image, and the builder. Avoid treating the cache as a guarantee; use it as an optimization for builds that remain semantically correct.

## A Practical Python Dockerfile

The following example assumes a project directory containing these files:

```text
python-api/
├── Dockerfile
├── .dockerignore
├── requirements.txt
└── app.py
```

Use this basic Dockerfile for a simple Python application:

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

This example is intentionally minimal and assumes the application can run with `python app.py`. It does not define a framework-specific production server, create a non-root user, or pin dependencies. Those decisions should be made for the actual application rather than guessed in a generic example.

From the project directory, build and run it with:

```powershell
docker build -t python-api:local .
docker run --rm python-api:local
```

For a real HTTP API, confirm the app's listening port and command, then publish the appropriate port. Do not copy production `.env` files or credentials into the build context.

## Multi-Stage Builds

A multi-stage build uses more than one `FROM` instruction. It lets you keep build-time tools or intermediate artifacts out of the final runtime image by copying only the required output from an earlier stage.

This is especially useful when an application must compile assets or native extensions, or when its build environment contains tools that are unnecessary at runtime.

A simplified example for a compiled application might look like this:

```dockerfile
FROM golang:1.26 AS build
WORKDIR /src
COPY . .
RUN mkdir -p /out && go build -o /out/app ./cmd/app

FROM debian:bookworm-slim AS runtime
WORKDIR /app
COPY --from=build /out/app ./app
CMD ["./app"]
```

This illustration assumes a Go project with a `./cmd/app` package and dependencies compatible with the selected runtime image. Verify and select maintained versions appropriate for your project before using it. Applications with native library dependencies may require those runtime libraries in the final stage.

The key instruction is `COPY --from=build`, which copies the compiled artifact from the build stage into the runtime stage. Only what the final application needs should be copied into the final image.

## Common Mistakes

### Copying the Entire Project Too Early

Copying every file before installing dependencies can invalidate the dependency layer whenever a source file changes. Copy dependency manifests first when that allows better cache reuse.

### Assuming `EXPOSE` Publishes a Port

`EXPOSE 8000` is image documentation. Publish a host port with `docker run -p` or Compose when access from the host is required.

### Using `latest` Without a Versioning Strategy

A mutable tag can point to different image content over time. Use intentional versioning, review updates, and pin digests when the workflow requires stronger reproducibility.

### Running as Root Without a Reason

Root privileges inside a container can increase impact if the application is compromised. Create and use a dedicated non-root user where practical, and check filesystem permissions.

### Copying Secrets into an Image

Files copied into an image can remain in its layers even if later instructions delete them. Keep secrets out of the build context and use appropriate runtime secret mechanisms or BuildKit secret mounts for build-time credentials.

### Treating Build Arguments as Secrets

Build arguments are for build configuration, not secret storage. Use dedicated secret mechanisms for sensitive values.

### Installing Unnecessary Packages

Unneeded build tools and packages can increase image size and maintenance work. Use multi-stage builds when they provide a clear benefit, and install only the packages required by each stage.

## Dockerfile Best Practices

- Choose a maintained, suitable base image and manage updates intentionally.
- Prefer explicit `COPY` instructions for ordinary local files.
- Use `.dockerignore` to keep the build context focused.
- Place relatively stable dependency inputs before frequently changing source files when it improves cache reuse.
- Combine related package-manager operations when doing so avoids unnecessary layers or leftover package indexes.
- Use exec-form `CMD` and `ENTRYPOINT` for application processes unless there is a specific reason to use shell form.
- Do not place secrets in Dockerfiles, build arguments, image layers, or source control.
- Use a non-root user when practical.
- Use multi-stage builds when separating build tools from runtime dependencies reduces the final image or attack surface.
- Document assumptions and test the resulting image.

## Useful Commands

```powershell
# Build an image from the current directory
docker build -t notes-demo:local .

# Build without using the normal build cache
docker build --no-cache -t notes-demo:local .

# Show image details
docker image inspect notes-demo:local

# Show image layers and history
docker image history notes-demo:local

# List images
docker image ls
```

The `--no-cache` option forces build steps to run without reusing the normal layer cache, but it does not automatically mean every base image is freshly pulled. Use `--pull` as well when you intentionally want Docker to check for a newer version of a mutable base-image tag:

```powershell
docker build --pull --no-cache -t notes-demo:local .
```

Be aware that rebuilding against a mutable tag may change the resulting image. For repeatable builds, choose and document an appropriate image-versioning policy.

## Key Takeaways

- A Dockerfile defines how an image is assembled.
- The build context determines which local files are available to `COPY` and related build operations.
- `.dockerignore` helps keep unnecessary files out of the build context.
- Instruction order affects cache reuse and rebuild time.
- `CMD` defines defaults, while `ENTRYPOINT` defines the intended executable.
- `EXPOSE` documents a container port; it does not publish that port by itself.
- Multi-stage builds can separate build-time requirements from the final runtime image.
- Secrets must be handled through appropriate secret mechanisms rather than embedded in images.

## Further Reading

- [Dockerfile reference](https://docs.docker.com/reference/dockerfile/)
- [Docker build context](https://docs.docker.com/build/concepts/context/)
- [Docker build best practices](https://docs.docker.com/build/building/best-practices/)
- [Optimize build cache usage](https://docs.docker.com/build/cache/optimize/)
- [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)

## Next Chapter

Continue with [Networking](04-networking.md) after completing the Dockerfile and image-building fundamentals. You can also review [Images and Containers](02-images-and-containers.md) before moving on.
