# Images and Containers

Docker images and containers are closely related, but they serve different purposes. An **image** is the packaged template used to create a container. A **container** is an isolated, runnable instance created from an image with its own configuration and writable layer.

This guide explains how to download, inspect, tag, run, manage, and remove images and containers. All command examples use PowerShell-compatible syntax unless otherwise noted.

## Table of Contents

- [Images and Containers: The Difference](#images-and-containers-the-difference)
- [How Images Are Organized](#how-images-are-organized)
- [Pull and Inspect an Image](#pull-and-inspect-an-image)
- [Understanding Image Names and Tags](#understanding-image-names-and-tags)
- [Tag an Image Locally](#tag-an-image-locally)
- [Build an Image](#build-an-image)
- [Create and Run a Container](#create-and-run-a-container)
- [Inspect and Debug Containers](#inspect-and-debug-containers)
- [Container Lifecycle](#container-lifecycle)
- [Remove Containers and Images](#remove-containers-and-images)
- [Common Commands](#common-commands)
- [Common Mistakes](#common-mistakes)
- [Best Practices](#best-practices)
- [Key Takeaways](#key-takeaways)
- [Further Reading](#further-reading)

## Images and Containers: The Difference

A Docker **image** is a read-only template containing a filesystem and image configuration. It can be stored locally or distributed through a container registry.

A Docker **container** is a created instance of an image. When a container starts, Docker adds a writable layer on top of the image's read-only layers and applies the requested runtime configuration, such as environment variables, networks, port mappings, and mounted storage.

An image can be used to create many containers. Those containers can use the same image while having different names, port mappings, environment variables, or other runtime settings.

| Image | Container |
|---|---|
| A template used to create containers | A created and configured instance of an image |
| Image layers are read-only | Has a writable layer in addition to image layers |
| Can be tagged and pushed to a registry | Can be started, stopped, inspected, and removed |
| Created by pulling or building an image | Created and started using commands such as `docker run` |

For example, `nginx:alpine` is an image reference. A container created from it could be named `chapter2-nginx` and publish the web server on a host port.

## How Images Are Organized

### Image Layers

Docker images are built from layers. A Dockerfile instruction that changes the filesystem can produce a layer, while other instructions contribute configuration or metadata. The builder can reuse eligible cached results to avoid repeating unchanged build steps.

Layering can reduce duplicated storage when images share common layers. It also means that Dockerfile instruction order and the files copied into a build can affect build-cache reuse.

The next chapter, [Dockerfile](03-dockerfile.md), explains how to structure image builds and use the build cache effectively.

### Read-Only Image Content and the Writable Container Layer

Image layers are read-only. A running container receives a separate writable layer for changes made inside its container filesystem.

That writable layer is tied to the container's lifecycle. Do not use it as the only storage location for data that must survive container removal. Use a volume or bind mount for persistent data; see [Volumes and Storage](05-volumes-and-storage.md).

### Image Identity

An image has an image ID, and registry images can also be identified by digests. Tags such as `nginx:alpine` are convenient names, but a tag can be updated to point to a different image over time. A tag should not be treated as a guarantee that the image content will never change.

For deployments where exact image identity matters, consider recording or pinning a verified digest and have a deliberate process for reviewing updates.

## Pull and Inspect an Image

The following commands download the Nginx image if needed and display images available locally:

```powershell
docker image pull nginx:alpine
docker image ls
```

`docker image pull` retrieves an image from a registry. If the requested content already exists locally, Docker may reuse it rather than downloading every layer again.

Inspect image metadata:

```powershell
docker image inspect nginx:alpine
```

The output is JSON and includes details such as image configuration, architecture, operating system, and image ID. It may be extensive, so you can narrow it down with a PowerShell command if needed:

```powershell
docker image inspect nginx:alpine --format '{{.Id}}'
docker image inspect nginx:alpine --format '{{.Os}}/{{.Architecture}}'
```

Review the image's recorded build history:

```powershell
docker image history nginx:alpine
```

The history provides information about image layers and build instructions. It is useful for investigation, but it is not a complete substitute for reviewing the source Dockerfile or the provenance of an image.

## Understanding Image Names and Tags

A typical image reference has this structure:

```text
[REGISTRY_HOST[:PORT]/][NAMESPACE/]REPOSITORY[:TAG]
```

Examples:

- `nginx:alpine` — the `nginx` repository with the `alpine` tag, hosted on Docker Hub by default.
- `python:3.13-slim` — the `python` repository with the `3.13-slim` tag.
- `ghcr.io/owner/project:1.2.0` — the `project` image in a namespace on GitHub Container Registry.

If a registry host is omitted, Docker normally uses Docker Hub. If a tag is omitted, Docker defaults to the `latest` tag. The `latest` tag does not necessarily mean the newest software version according to semantic versioning; it is simply a tag name selected by the publisher.

Tags help people identify versions or variants, for example `my-api:1.0.0` and `my-api:1.1.0`. Choose a versioning convention and use it consistently.

## Tag an Image Locally

The `docker image tag` command creates another reference to an existing local image. It does not rebuild the image or duplicate all its layers.

First, make sure `nginx:alpine` is available locally:

```powershell
docker image pull nginx:alpine
```

Create a second local tag:

```powershell
docker image tag nginx:alpine local-nginx:demo
docker image ls
```

You should see both `nginx:alpine` and `local-nginx:demo`. They will normally show the same image ID because both tags reference the same local image content.

Remove the additional tag when you no longer need it:

```powershell
docker image rm local-nginx:demo
```

This removes that tag. It does not mean Docker must delete the underlying image layers if they are still referenced by another tag or container.

## Build an Image

Images are often built from a Dockerfile. From a directory containing a file named `Dockerfile`, you can build and tag an image with:

```powershell
docker build -t my-app:1.0 .
```

In this command:

- `-t my-app:1.0` assigns the image repository name and tag.
- `.` specifies the build context: the directory whose files are available to the builder, subject to `.dockerignore` and build configuration.

This command only works as written when the current directory contains a suitable `Dockerfile` and the files referenced by it. It is a pattern, not a complete application example. Do not run it in this repository's root unless you have added a Dockerfile there.

To list and inspect the newly built image:

```powershell
docker image ls
docker image inspect my-app:1.0
```

The `my-app:1.0` image exists only after a successful build or pull that creates that tag.

For a complete explanation of Dockerfile instructions, build context, layer caching, and `.dockerignore`, continue to [Dockerfile](03-dockerfile.md).

## Create and Run a Container

The `docker run` command creates a new container from an image and starts it. If the image is not available locally, Docker generally tries to pull it first.

### Run a One-Time Command

```powershell
docker run --rm alpine:latest echo "Hello from a container"
```

This creates a container, runs the specified command, prints the message, and removes the container after it exits. The image remains cached locally.

The `--rm` option is useful for temporary tasks. It also removes anonymous volumes associated with the container when it is removed; named volumes are not removed by this option.

### Run a Web Server in the Background

Start an Nginx container with a predictable name and a local-only port mapping:

```powershell
docker run --detach --name chapter2-nginx --publish 127.0.0.1:8081:80 nginx:alpine
```

This command uses:

- `--detach` (or `-d`) to run the container in the background.
- `--name chapter2-nginx` to assign a recognizable container name.
- `--publish 127.0.0.1:8081:80` (or `-p`) to map host port `8081` to container port `80`, bound to the host loopback interface.
- `nginx:alpine` as the image reference.

The port mapping makes the service available from the same machine at [http://localhost:8081](http://localhost:8081). It does not publish the port on every host network interface. If port `8081` is already in use, choose another available host port.

Check the running container:

```powershell
docker ps
```

The `PORTS` column should show a mapping similar to `127.0.0.1:8081->80/tcp`.

## Inspect and Debug Containers

Use the following commands while `chapter2-nginx` exists:

```powershell
# List running containers
docker ps

# List all containers, including stopped containers
docker ps --all

# Read the container's logs
docker logs chapter2-nginx

# Follow new log output
docker logs --follow chapter2-nginx

# Inspect configuration and state
docker container inspect chapter2-nginx

# Display published port mappings
docker port chapter2-nginx
```

Press `Ctrl+C` to stop following logs; this stops the log command, not the Nginx container.

### Execute a Command Inside a Running Container

The `docker exec` command runs a new process inside an existing running container:

```powershell
docker exec -it chapter2-nginx sh
```

This opens a shell if the image includes `sh`. Enter `exit` to leave the shell. Exiting the shell does not stop Nginx because the shell is an additional process rather than the container's main process.

`docker exec` is useful for debugging, but routine application configuration should be managed through version-controlled configuration, environment settings, and image builds rather than relying on undocumented manual changes inside a running container.

## Container Lifecycle

A container's common lifecycle looks like this:

1. `docker run` creates and starts a new container.
2. The container runs while its main process is active.
3. `docker stop` asks the main process to stop gracefully, then forces termination if it does not stop within the configured timeout.
4. A stopped container remains available for inspection and can be started again with `docker start`.
5. `docker rm` removes a stopped container.

Try these commands after running the Nginx example:

```powershell
docker stop chapter2-nginx
docker ps --all
docker start chapter2-nginx
docker ps
docker restart chapter2-nginx
```

After the restart, open `http://localhost:8081` again. The container keeps its identity and configuration when it is stopped and started; a new `docker run` command creates a different container.

The `docker stop` command normally sends the configured stop signal to the main process and waits for a grace period before forcefully terminating it if necessary.

## Remove Containers and Images

When you have finished the Nginx exercise, stop and remove the container:

```powershell
docker stop chapter2-nginx
docker rm chapter2-nginx
```

The `nginx:alpine` image remains local and can be used to create another container later.

To remove a local image tag, first make sure it is no longer needed by a container or another workload:

```powershell
docker image rm nginx:alpine
```

Docker may refuse to remove an image that is still referenced by containers or other tags. Avoid force-removing images merely to clear space; first inspect which resources depend on them.

To review unused resources, use:

```powershell
docker container ls --all
docker image ls
docker system df
```

Prune commands can remove data or resources you intend to keep. In particular, volumes can contain persistent application data. Understand the command's scope before confirming a cleanup operation.

## Common Commands

| Command | Purpose |
|---|---|
| `docker image pull IMAGE` | Download an image from a registry |
| `docker image ls` | List local images |
| `docker image inspect IMAGE` | Inspect image metadata |
| `docker image history IMAGE` | Display image history |
| `docker image tag SOURCE TARGET` | Add another tag to a local image |
| `docker build -t NAME:TAG .` | Build an image from a Dockerfile in the current build context |
| `docker run IMAGE` | Create and start a container |
| `docker ps` | List running containers |
| `docker ps -a` | List all containers |
| `docker logs CONTAINER` | Display container logs |
| `docker exec -it CONTAINER sh` | Open a shell in a running container, if available |
| `docker stop CONTAINER` | Stop a running container gracefully, subject to timeout |
| `docker start CONTAINER` | Start an existing stopped container |
| `docker rm CONTAINER` | Remove a container |
| `docker image rm IMAGE` | Remove a local image tag or image when possible |

Replace placeholders such as `IMAGE`, `SOURCE`, `TARGET`, `NAME:TAG`, and `CONTAINER` with the actual names or IDs. Do not type the angle-bracket placeholders from earlier examples literally into a command.

## Common Mistakes

### Confusing an Image with a Container

`docker image ls` lists images, while `docker ps --all` lists containers. They are different types of Docker objects.

### Assuming `docker stop` Removes a Container

Stopping a container leaves it in place. Use `docker rm` after stopping it if you want to remove it.

### Assuming `latest` Always Means the Newest Version

`latest` is a tag chosen by the image publisher. It does not guarantee the newest stable or secure application release. Use an appropriate versioning and update policy.

### Forgetting to Publish a Port

A service listening on a container port is not automatically reachable through a host port. Configure port publishing where appropriate, and bind to the least-exposed host interface that meets your needs.

### Treating the Writable Layer as Persistent Storage

Data written only to a container's writable layer is tied to that container. Use volumes or bind mounts for data that must survive container removal.

### Removing Resources Without Checking Their Impact

Images, containers, and volumes have different lifecycles. Check what a cleanup command removes, especially when working with databases or other stateful services.

## Best Practices

- Prefer explicit, meaningful container names for repeatable learning exercises and development environments.
- Select an image tag intentionally, and use verified digests where exact image identity is required.
- Keep containers replaceable; put long-lived data in volumes or other appropriate storage systems.
- Publish only the ports that need to be reachable. Prefer a loopback binding for local-only development services.
- Inspect logs and container state before attempting random changes.
- Use `docker exec` primarily for inspection and debugging, not as a substitute for repeatable configuration.
- Understand the scope of cleanup commands before removing resources.
- Review the image's source, maintenance status, and security posture before using it in production.

## Key Takeaways

- An image is a template; a container is a configured instance of an image.
- Image layers are read-only, while a container has its own writable layer.
- Tags are convenient references and may be updated; a tag is not a permanent content identifier.
- `docker run` creates and starts a new container, while `docker start` starts an existing stopped container.
- Port publishing maps a host port to a container port.
- Logs, inspection, and `docker exec` are useful debugging tools.
- Persistent data should be stored in an appropriate volume or bind mount, not only in a container's writable layer.

## Further Reading

- [Build, tag, and publish an image](https://docs.docker.com/get-started/docker-concepts/building-images/build-tag-and-publish-an-image/)
- [Building images](https://docs.docker.com/get-started/docker-concepts/building-images/)
- [Docker image CLI reference](https://docs.docker.com/reference/cli/docker/image/)
- [Docker container run reference](https://docs.docker.com/reference/cli/docker/container/run/)
- [Docker container CLI reference](https://docs.docker.com/reference/cli/docker/container/)
- [Docker image history reference](https://docs.docker.com/reference/cli/docker/image/history/)

## Next Chapter

Continue with [Dockerfile](03-dockerfile.md) to learn how to define an image build, choose a base image, copy application files, install dependencies, and use build layers effectively.
