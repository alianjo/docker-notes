# Docker Fundamentals

Docker is a platform for building, packaging, distributing, and running applications in containers. It helps developers create consistent environments across local development, testing, and deployment.

This guide introduces the fundamental Docker concepts and commands you need before moving on to images, containers, Dockerfiles, networking, and persistent storage.

## Table of Contents

- [What Is Docker?](#what-is-docker)
- [Why Use Docker?](#why-use-docker)
- [Containers vs. Virtual Machines](#containers-vs-virtual-machines)
- [How Docker Works](#how-docker-works)
- [Core Docker Concepts](#core-docker-concepts)
- [Install and Verify Docker](#install-and-verify-docker)
- [Run Your First Container](#run-your-first-container)
- [Explore a Running Container](#explore-a-running-container)
- [Container Lifecycle](#container-lifecycle)
- [Common Docker Commands](#common-docker-commands)
- [Fundamental Best Practices](#fundamental-best-practices)
- [Common Misconceptions](#common-misconceptions)
- [Key Takeaways](#key-takeaways)
- [Further Reading](#further-reading)

## What Is Docker?

Docker provides tools for packaging applications and their dependencies into container images and running those images as containers.

For example, a Python application may require a particular Python runtime, several third-party packages, and specific system libraries. Without a consistent environment, differences between development and deployment machines can cause unexpected failures.

Docker allows developers to define and distribute an application environment so that it can be recreated on compatible systems.

A typical backend application might use separate containers for:

- A Python API built with Django or FastAPI.
- A PostgreSQL database.
- A Redis instance for caching or background processing.
- A reverse proxy that receives incoming HTTP requests.

Each component can have its own image, configuration, lifecycle, and resource requirements.

## Why Use Docker?

### Consistent Environments

Docker images package application files and dependencies. This reduces differences between development, testing, and deployment environments.

Consistency still depends on how images are built, configured, and versioned.

### Isolation

Containers isolate application processes and provide configurable boundaries for resources, filesystems, and networking.

This helps separate application components and reduces dependency conflicts. Container isolation is not, by itself, a complete security boundary.

### Portability

An image can be distributed through a container registry and run on compatible Docker environments.

The host architecture, operating system, configuration, permissions, and external dependencies can still affect portability.

### Efficient Resource Usage

Containers generally have less overhead than running a separate full guest operating system for every application component.

This makes them useful for local development, automated testing, continuous integration, and many deployment workflows.

### Reproducible Workflows

A Dockerfile and related configuration files can document how an application image is built.

When these files are version-controlled, team members and automated build systems can recreate the intended environment more consistently.

## Containers vs. Virtual Machines

Containers and virtual machines provide different approaches to isolation.

| Feature | Containers | Virtual Machines |
|---|---|---|
| Isolation model | Isolated processes and supporting kernel features | Virtualized hardware with a guest operating system |
| Operating system | Normally shares the kernel provided by its container host environment | Each VM runs its own guest OS |
| Typical overhead | Generally lower | Generally higher |
| Startup | Usually fast | Often slower |
| Filesystem | Image layers plus a container-specific writable layer | Virtual disk and guest filesystem |
| Common use cases | Application packaging and service deployment | Full OS environments and workloads needing VM-level isolation |

On Linux, containers normally share the host kernel. On Windows and macOS, Docker Desktop commonly runs Linux containers inside a lightweight Linux virtual machine.

Containers and virtual machines are not mutually exclusive. Containers frequently run inside virtual machines in cloud and production environments.

## How Docker Works

Docker uses a client-server architecture.

The main components are:

**Docker client**

The `docker` command-line interface sends requests to a Docker daemon.

**Docker daemon**

The `dockerd` process manages Docker objects, including images, containers, networks, and volumes.

**Docker Desktop**

On Windows and macOS, Docker Desktop provides an integrated environment for running the Docker engine and related development tools.

**Container registry**

A registry stores and distributes container images. Docker Hub is a commonly used public registry.

A typical workflow looks like this:

1. You enter a command such as `docker run nginx:alpine`.
2. The Docker client sends the request to the daemon.
3. Docker retrieves the image from a configured registry if it is not available locally.
4. Docker creates and starts a container using the image and requested configuration.
5. The application runs inside the container.

The client and daemon do not have to run on the same machine.

## Core Docker Concepts

Understanding the following terms will make the rest of this handbook easier to follow.

### Image

A container image is an immutable template containing the filesystem content and configuration needed to create a container.

Images are built from layers. Multiple images can reuse common layers, reducing duplicate storage and build work.

For example:

```powershell
docker pull nginx:alpine
docker image ls
docker image inspect nginx:alpine
```

The first command downloads the specified image when needed. The next commands list local images and inspect the selected image.

See [Images and Containers](02-images-and-containers.md) for more details.

### Container

A container is a runnable instance of an image, created with a specific configuration.

You can create, start, stop, inspect, and remove containers independently of the images from which they were created.

A running container has a writable layer on top of its image layers. Changes stored only in that writable layer are not a reliable way to preserve application data after the container is removed.

Use appropriate volumes or bind mounts when data must persist independently of a container's lifecycle.

### Dockerfile

A Dockerfile contains instructions for building an image.

For example:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

This is a simplified illustration, not a complete production-ready application. It assumes that `requirements.txt` and `app.py` exist and that the base image is suitable for the application.

The Dockerfile chapter will explain image construction, caching, instruction ordering, and security considerations.

### Volume

A volume is a storage mechanism managed by Docker. Volumes are useful when data needs to persist independently of an individual container.

Databases are a common example because their data should normally survive container recreation.

Learn more in [Volumes and Storage](05-volumes-and-storage.md).

### Network

Docker networks connect containers and control how they communicate with one another and with external systems.

For example, an API container might connect to PostgreSQL over a private Docker network rather than exposing the database port to the host.

See [Networking](04-networking.md) for network drivers, DNS, and port publishing.

### Compose

Docker Compose defines and manages multi-container applications using a YAML configuration file.

It is particularly useful for development environments containing an API, database, cache, and other supporting services.

Continue with [Docker Compose](07-docker-compose.md).

## Install and Verify Docker

Install Docker Desktop on Windows or macOS, or Docker Engine on Linux, using the official instructions.

See the [Docker installation guide](https://docs.docker.com/get-started/get-docker/).

After installation, open PowerShell or your preferred terminal and run:

```powershell
docker --version
docker compose version
docker info
```

These commands display the Docker CLI version, the Compose version, and information about the active Docker environment.

If `docker info` fails because the daemon is unavailable, check that Docker Desktop or the Docker Engine service is running.

The following command is a useful installation test:

```powershell
docker run --rm hello-world
```

Docker downloads the image if necessary, creates a container, runs the test program, and removes the container when it exits.

## Run Your First Container

Let's start a small Nginx web server.

### Step 1: Start the Container

Run this command in PowerShell:

```powershell
docker run --detach --publish 127.0.0.1:8080:80 --name docker-notes-web nginx:alpine
```

The options mean:

- `--detach` runs the container in the background.
- `--publish 127.0.0.1:8080:80` maps host port `8080` to container port `80`, bound to the host's loopback interface.
- `--name docker-notes-web` assigns a predictable container name.
- `nginx:alpine` identifies the image and its tag.

Binding to `127.0.0.1` limits this port mapping to the local host interface rather than publishing it on every host network interface.

### Step 2: Check the Container

```powershell
docker ps
```

You should see a running container named `docker-notes-web` with a port mapping similar to `127.0.0.1:8080->80/tcp`.

### Step 3: Open the Web Server

Open the following URL in your browser:

http://localhost:8080

You should see the default Nginx welcome page.

### Step 4: Inspect the Logs

```powershell
docker logs docker-notes-web
```

Docker displays the logs produced by the container's main process.

### Step 5: Stop the Container

```powershell
docker stop docker-notes-web
```

The container stops but remains available for inspection or a later restart.

### Step 6: Remove the Container

```powershell
docker rm docker-notes-web
```

This removes the stopped container. The `nginx:alpine` image remains available locally.

If you want to run the exercise again, repeat Step 1.

## Explore a Running Container

The following commands are useful when examining containers during development:

```powershell
# Display running containers
docker ps

# Display all containers, including stopped ones
docker ps --all

# Display logs
docker logs docker-notes-web

# Follow logs as they are produced
docker logs --follow docker-notes-web

# Inspect container configuration and state
docker inspect docker-notes-web

# Display resource usage for running containers
docker stats
```

Run commands that reference `docker-notes-web` while that container exists. After removing the container, those commands will no longer find it.

For commands such as `docker stats`, Docker displays resource usage for the selected running containers. Actual CPU and memory limits depend on the environment and configuration.

## Container Lifecycle

A common container lifecycle looks like this:

1. **Create or run:** Create a container from an image. The `docker run` command creates and starts it.
2. **Running:** The container's main process is executing.
3. **Stopped:** The main process has exited or the container has been stopped.
4. **Restart:** A stopped container can be started again if it still exists.
5. **Remove:** Delete the container after stopping it, if necessary.

Useful commands include:

```powershell
# Start a new container
docker run --name example-nginx nginx:alpine

# List containers
docker ps --all

# Start an existing stopped container
docker start example-nginx

# Stop a running container
docker stop example-nginx

# Remove a stopped container
docker rm example-nginx
```

The first command runs Nginx in the foreground. Press `Ctrl+C` to stop it, then use the remaining commands as appropriate.

The `docker run` command creates a new container; `docker start` starts an existing container. These commands are not interchangeable.

## Common Docker Commands

| Command | Purpose |
|---|---|
| `docker version` | Display client and server version information |
| `docker info` | Inspect Docker environment information |
| `docker ps` | List running containers |
| `docker ps -a` | List all containers |
| `docker image ls` | List local images |
| `docker pull IMAGE` | Download an image |
| `docker run IMAGE` | Create and start a container |
| `docker start CONTAINER` | Start an existing container |
| `docker stop CONTAINER` | Stop a running container |
| `docker logs CONTAINER` | Display container logs |
| `docker inspect OBJECT` | Inspect an image, container, or other supported object |
| `docker rm CONTAINER` | Remove a container |
| `docker rmi IMAGE` | Remove a local image when it is no longer needed |

Replace placeholders such as `IMAGE` and `CONTAINER` with an actual image name, container name, or ID. Avoid deleting images or containers that are still needed by other workloads.

## Fundamental Best Practices

- Use explicit image tags when reproducible builds matter. For stronger reproducibility, consider pinning image digests and managing updates deliberately.
- Prefer trusted, maintained images and review their provenance and configuration.
- Keep application configuration separate from the image.
- Do not store secrets in Dockerfiles or image layers.
- Use volumes or bind mounts when application data must outlive a container.
- Avoid running application processes as root when a non-root user is practical.
- Publish only the ports that need to be reachable.
- Remove unused resources carefully, especially volumes containing persistent data.
- Understand what a command changes before running destructive cleanup operations.
- Keep Docker, base images, and application dependencies updated.

For a deeper treatment of image construction and hardening, see the official [Docker build best practices](https://docs.docker.com/build/building/best-practices/).

## Common Misconceptions

**An image and a container are the same thing.**

An image is the template; a container is a created and configured instance of that template.

**Stopping a container deletes it.**

Stopping a container leaves it available for inspection or restarting. Removing it is a separate operation.

**Deleting a container always deletes its data.**

Data stored only in the container's writable layer is removed with the container. Data stored in a persistent volume can survive container removal, subject to the storage lifecycle and cleanup operations used.

**Docker containers are complete virtual machines.**

Containers normally isolate processes while sharing the host kernel provided by the container environment. Virtual machines run guest operating systems.

**A running container is necessarily healthy.**

A running container only indicates that its main process is running. The application might still be unable to serve requests or connect to its dependencies. Appropriate health checks and application-level monitoring can help detect these conditions.

**Publishing a port is the same as exposing it inside Docker.**

Port publishing creates a mapping between a host interface and a container port. The host binding address and firewall configuration affect reachability.

## Key Takeaways

- Docker packages applications and their dependencies into images.
- Containers are runnable instances of images.
- The Docker client communicates with the Docker daemon to manage resources.
- Registries store and distribute images.
- Container writable layers are not a substitute for persistent storage.
- Networks control communication between containers and external systems.
- Docker Compose manages multi-container applications.
- Reproducibility, least privilege, careful port publishing, and persistent storage are important design considerations.

## Further Reading

- [Docker Overview](https://docs.docker.com/get-started/docker-overview/)
- [What Is a Container?](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/)
- [What Is an Image?](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/)
- [What Is a Registry?](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-registry/)
- [Docker CLI Reference](https://docs.docker.com/reference/cli/docker/)

## Next Chapter

Continue with [Images and Containers](02-images-and-containers.md) to learn how images are built, tagged, inspected, and used to create containers.