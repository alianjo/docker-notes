# Volumes and Storage

Containers are designed to be replaceable. By default, files written by an application into a container's writable layer are tied to that container's lifecycle. When the container is removed, that writable layer is removed as well.

Docker provides storage mounts so that data can live outside an individual container. This chapter explains the main mount types, how to use them, and how to avoid accidental data loss when managing backend services such as PostgreSQL.

## Table of Contents

- [Why Storage Matters](#why-storage-matters)
- [The Three Main Mount Types](#the-three-main-mount-types)
- [Docker Volumes](#docker-volumes)
- [Bind Mounts](#bind-mounts)
- [tmpfs Mounts](#tmpfs-mounts)
- [Choose the Right Mount Type](#choose-the-right-mount-type)
- [Hands-on Exercise: Persist Data with a Named Volume](#hands-on-exercise-persist-data-with-a-named-volume)
- [Hands-on Exercise: Share a Host Directory](#hands-on-exercise-share-a-host-directory)
- [Inspect and Manage Volumes](#inspect-and-manage-volumes)
- [Storage in Docker Compose](#storage-in-docker-compose)
- [Databases and Persistent Data](#databases-and-persistent-data)
- [Backups and Recovery](#backups-and-recovery)
- [Common Mistakes](#common-mistakes)
- [Security and Best Practices](#security-and-best-practices)
- [Key Takeaways](#key-takeaways)
- [Further Reading](#further-reading)
- [Next Chapter](#next-chapter)

## Why Storage Matters

Imagine running a PostgreSQL container with no persistent storage configuration. PostgreSQL writes its database files into the container's writable layer. If the container is removed and recreated, the old writable layer is gone, and the database data stored there is lost.

A storage mount places data at a location outside the container's writable layer. The container can access that mounted location at a path inside its filesystem, such as `/var/lib/postgresql/data`.

Storage mounts are useful for:

- Database files that must survive container recreation.
- Uploaded files or generated reports that need to persist.
- Sharing source code between a development machine and a container.
- Providing configuration files to a service.
- Temporary data that should not be kept in the container's writable layer.

A mount does not replace a backup strategy. Persistent storage protects data from some container lifecycle events, but not from every host failure, accidental deletion, corruption, or application error.

## The Three Main Mount Types

Docker commonly uses three types of mounts for container data: volumes, bind mounts, and `tmpfs` mounts.

| Feature | Volume | Bind mount | `tmpfs` mount |
|---|---|---|---|
| Storage location | Managed by Docker | A specific host path | Memory on the Linux host |
| Typical use | Persistent application data | Source code and host files | Temporary, non-persistent data |
| Survives container removal | Yes, unless the volume is removed separately | Host files remain, subject to host filesystem actions | No |
| Directly managed with Docker volume commands | Yes | No | No |
| Depends on a specific host path | No for normal use | Yes | No source path |
| Availability | Linux and Windows container scenarios, subject to platform details | Platform and file-sharing configuration dependent | Supported for Linux containers; not available in the same way on Docker Desktop's Windows containers |

Choose a mount based on the data's lifecycle and who needs to access it. Do not choose a bind mount simply because it is familiar, or a volume simply because a path is easier to type.

## Docker Volumes

A volume is a data store created and managed by Docker. Docker manages the volume's storage location, and containers can mount it at a path in their filesystem.

Volumes are generally a good default for persistent container data because they are not tied to one container's writable layer and do not require the application to know the host's storage path.

### Create a named volume

```powershell
docker volume create app-data
docker volume ls
docker volume inspect app-data
```

A named volume has an explicit name, such as `app-data`, making it easier to identify and reuse.

### Mount a volume into a container

The `--mount` syntax is explicit about the mount type, source, and destination:

```powershell
docker run --rm --mount source=app-data,target=/data alpine:3.22 sh -c "echo 'hello from a volume' > /data/message.txt"
```

This command writes a file into the volume. The container is removed after its process exits because `--rm` was supplied, but the named volume remains.

Read the file from a new container:

```powershell
docker run --rm --mount source=app-data,target=/data alpine:3.22 cat /data/message.txt
```

Expected output:

```text
hello from a volume
```

The two containers are different instances, but both mount the same named volume.

### Named and anonymous volumes

A **named volume** has a name you choose, such as `app-data`. This makes it straightforward to mount the same volume again and inspect it later.

An **anonymous volume** is created without an explicit reusable name. Docker assigns it a generated name. Anonymous volumes can be useful in some image and container workflows, but named volumes are often easier to manage for important application data.

### Volume lifecycle

A volume exists independently of any one container. Removing a container does not normally remove a named volume.

```powershell
docker volume ls
docker volume inspect app-data
docker volume rm app-data
```

The final command permanently removes `app-data` if no container is using it. **Do not run it on a volume containing data you need.** Confirm the volume name and make a verified backup before deleting important data.

## Bind Mounts

A bind mount connects a specific file or directory on the host to a path inside a container. Unlike a volume, Docker does not manage the source directory's lifecycle; you choose the host path.

Bind mounts are especially useful for local development, where source-code changes on the host need to be visible inside a container.

### Create a host directory on Windows

Run these commands in PowerShell from your project directory:

```powershell
New-Item -ItemType Directory -Force -Path .\bind-data | Out-Null
Set-Content -Path .\bind-data\message.txt -Value "Hello from the Windows host"
$sourcePath = (Resolve-Path .\bind-data).Path
```

Mount that directory into a container in read-only mode:

```powershell
docker run --rm --mount "type=bind,source=$sourcePath,target=/data,readonly" alpine:3.22 cat /data/message.txt
```

Expected output:

```text
Hello from the Windows host
```

The source path is resolved to an absolute path before it is passed to Docker. Docker Desktop must be able to share or access that path.

### Observe the host-container relationship

Change the file on the host:

```powershell
Set-Content -Path .\bind-data\message.txt -Value "Updated on the host"
```

Run the container command again. It should display the updated content because the host directory is mounted into the container.

The mount above is read-only from the container's perspective. Remove `readonly` only when the container genuinely needs to modify the host files.

### Bind-mount considerations

- The source path must exist or be handled deliberately. With `--mount type=bind`, Docker reports an error when the source path does not exist.
- Bind mounts depend on the directory structure and permissions of the host.
- A writable bind mount lets a process in the container modify host files. This can damage source code or host data if permissions are too broad.
- Mounting over a non-empty directory in the container obscures the image's existing files at that path for as long as the mount is active.
- Prefer absolute paths when defining bind mounts in scripts and documentation.

## `tmpfs` Mounts

A `tmpfs` mount stores temporary files in memory on a Linux host instead of persisting them in a volume or container writable layer. When the container stops, the contents of the `tmpfs` mount are removed.

For a compatible Linux container environment, an example is:

```powershell
docker run --rm --mount type=tmpfs,dst=/tmp/runtime-data,tmpfs-size=16777216 alpine:3.22 sh -c "echo temporary-data > /tmp/runtime-data/example.txt && cat /tmp/runtime-data/example.txt"
```

This requests a 16 MiB tmpfs mount. Availability and behavior depend on the Docker host and container platform. Docker Desktop setups that run Linux containers use a Linux environment, but `tmpfs` should not be assumed to work the same way for Windows containers.

Use `tmpfs` for data that should be temporary, such as intermediate processing files. Do not use it for data that must survive container restart or removal. Its memory usage counts toward the container's memory accounting, and `tmpfs` is not a substitute for secure secret management.

## Choose the Right Mount Type

Use these rules of thumb:

| Requirement | Recommended starting point | Reason |
|---|---|---|
| Persist database files across container recreation | Named volume | Storage lifecycle is separate from the container |
| Edit application source code on the host and run it inside a container | Bind mount | Host changes are visible in the mounted directory |
| Provide a host configuration file to a container | Read-only bind mount where appropriate | The container can read the file without needing to change it |
| Keep temporary working files in memory on a Linux container host | `tmpfs` | The data is not retained as a normal persistent volume |
| Keep data only for the lifetime of a disposable container | Container writable layer may be sufficient | No additional mount is needed if persistence is not required |

These are starting points, not universal rules. Performance, access control, operating system, orchestration platform, and backup requirements can affect the final design.

## Hands-on Exercise: Persist Data with a Named Volume

This exercise demonstrates that data in a named volume survives container removal.

### Step 1: Create a volume

```powershell
docker volume create docker-notes-data
```

If the volume already exists, Docker returns its name rather than creating a second volume with that same name.

### Step 2: Write a file into the volume

The following command uses a container named `docker-notes-volume-writer`. If you have run this exercise before and that container still exists, remove that specific demonstration container first.

```powershell
docker run --name docker-notes-volume-writer --mount source=docker-notes-data,target=/data alpine:3.22 sh -c "echo 'This file survives container removal' > /data/message.txt"
```

The command exits after writing the file, but the container remains because `--rm` was not used.

### Step 3: Remove the container

```powershell
docker rm docker-notes-volume-writer
```

Only the container is removed. The named volume is not removed by this command.

### Step 4: Read the saved file from a new container

```powershell
docker run --rm --mount source=docker-notes-data,target=/data alpine:3.22 cat /data/message.txt
```

Expected output:

```text
This file survives container removal
```

### Step 5: Inspect the volume

```powershell
docker volume inspect docker-notes-data
```

You can now see the volume metadata. On Docker Desktop, the volume's actual storage is maintained inside Docker's environment rather than necessarily appearing as an ordinary directory at a convenient Windows path.

### Cleanup

Remove the demonstration volume only after you have finished inspecting it and confirmed that it contains no data you need:

```powershell
docker volume rm docker-notes-data
```

This is a destructive operation for the data stored in that volume. Skip it if you want to keep the exercise data.

## Hands-on Exercise: Share a Host Directory

This exercise uses the `bind-data` directory created earlier. From the same PowerShell working directory, run:

```powershell
$sourcePath = (Resolve-Path .\bind-data).Path
docker run --rm --mount "type=bind,source=$sourcePath,target=/data,readonly" alpine:3.22 ls -la /data
docker run --rm --mount "type=bind,source=$sourcePath,target=/data,readonly" alpine:3.22 cat /data/message.txt
```

Compare the file content shown by the container with the file on Windows:

```powershell
Get-Content .\bind-data\message.txt
```

They should match. The container mount is read-only, so the commands above do not modify the host file.

When finished, you can remove the test directory if you no longer need it:

```powershell
Remove-Item -Recurse -Force .\bind-data
```

Run this cleanup command only if `bind-data` is the exercise directory created for this guide and it contains no files you need.

## Inspect and Manage Volumes

Useful commands include:

```powershell
# List volumes

docker volume ls

# Inspect a specific volume
docker volume inspect docker-notes-data

# Display volumes used by a container
docker inspect --format '{{json .Mounts}}' <container_name>

# Display Docker disk usage, including volume information
docker system df -v
```

Replace `<container_name>` with the name or ID of an existing container. The last command reports Docker disk usage details; it does not itself delete data.

### Removing unused volumes

Docker can remove volumes that are not used by containers:

```powershell
docker volume prune
```

Treat prune commands with care. Review the CLI prompt and the volumes that may be removed, and verify that important data has a backup before cleanup. Do not automate destructive pruning as a routine substitute for storage lifecycle management.

## Storage in Docker Compose

Docker Compose can declare named volumes and attach them to services. The following is an illustrative `compose.yaml` fragment for a database service:

```yaml
services:
  database:
    image: postgres:17
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in your environment}
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
```

This fragment demonstrates the storage declaration, but it is not a complete production deployment. Set `POSTGRES_PASSWORD` in the environment before starting Compose, and use an appropriate secrets mechanism for production credentials. The selected PostgreSQL image version and mount destination must match the application's supported database version and image documentation.

Compose creates the named volume if needed and mounts it into the database container. The logical volume name may be prefixed by the Compose project name unless an explicit external volume or name configuration is used.

Common commands include:

```powershell
# Check the rendered configuration
docker compose config

# Start services from compose.yaml
docker compose up -d

# View service status
docker compose ps

# Stop and remove services, containers, and networks
docker compose down
```

By default, `docker compose down` does not remove named volumes declared by the Compose project. Adding `-v` requests removal of the project's declared named volumes and attached anonymous volumes. Do not use `-v` if you intend to keep the database data.

## Databases and Persistent Data

Databases need deliberate storage planning. A named volume is often appropriate for a database's data directory, but persistence alone does not guarantee recoverability or data integrity.

For database containers:

- Use a volume dedicated to the database's persistent data directory.
- Read the official image documentation to confirm its expected data path and supported configuration for the exact image version.
- Do not assume that removing or recreating a container also resets its data volume.
- Do not assume that deleting a container backs up or securely deletes its data.
- Coordinate backups with the database's consistency requirements. A raw copy of files while a database is writing may not be a valid backup.
- Test restoration procedures, not just backup creation.
- Restrict access to volumes because they may contain credentials, personal information, or other sensitive application data.

The same considerations apply to file uploads and generated artifacts: define ownership, retention, backup, restore, and migration procedures appropriate to the application.

## Backups and Recovery

Volumes protect data from the normal removal of an individual container, but they are not backups by themselves. A volume can still be deleted, corrupted, lost with the host or Docker storage environment, or modified by an application bug.

A robust process should identify:

1. Which data must be preserved.
2. How to take a consistent backup for the relevant application or database.
3. Where backups are stored independently of the original volume and host failure domain.
4. How long backups are retained and who can access them.
5. How to restore the backup into a separate test environment.
6. How restoration is verified before relying on the backup.

For relational databases, prefer database-native backup and restore tools where appropriate. For general file volumes, a file archive can be suitable if the source data is in a consistent state and permissions and ownership are handled correctly.

## Common Mistakes

**Writing important data only to the container writable layer.**

A container can be removed and recreated, taking that writable layer with it. Use a named volume or another appropriate persistent storage system for data that must survive.

**Confusing bind mounts with named volumes.**

A bind mount references a particular host path. A named volume is created and managed by Docker. Choose based on whether the host needs direct access to a known directory and how the data should be managed.

**Assuming `docker compose down` always deletes database data.**

Named volumes generally remain after `docker compose down`. The `-v` option requests their removal when they are managed by the project. Read the command's behavior before running cleanup.

**Assuming a volume is a backup.**

A volume is persistent storage, not a separate recoverable copy. Maintain and test independent backups.

**Mounting an empty host directory over an application directory.**

The mount obscures the image's existing content at that destination while active. Confirm the destination and source before starting the container.

**Giving a container a writable mount unnecessarily.**

Use read-only mounts when the application only needs to read the files. This can reduce accidental changes, though it is not a replacement for broader access controls.

## Security and Best Practices

- Use named volumes for persistent data managed by Docker.
- Use bind mounts only where host-directory access is needed, and prefer read-only mounts when possible.
- Do not mount sensitive host directories into untrusted containers.
- Limit which services can mount or access database and upload volumes.
- Understand UID/GID, filesystem permissions, and platform-specific behavior when applications run as non-root users.
- Avoid sharing one writable data directory across unrelated services unless concurrent access is explicitly supported.
- Keep secrets out of images, source control, and ordinary configuration files committed to the repository.
- Use tested backups and restoration procedures for important state.
- Inspect volume names and consequences before deleting volumes or running prune commands.
- Consider storage performance and capacity limits when deploying stateful workloads.

## Key Takeaways

- A container's writable layer is tied to the container's lifecycle.
- Named volumes are managed by Docker and are a common choice for persistent application data.
- Bind mounts connect a chosen host path to a container path and are especially useful for development.
- `tmpfs` provides temporary memory-backed storage in supported Linux container environments.
- Removing a container is different from removing its named volume.
- Persistent storage does not replace backups, restore testing, access controls, or monitoring.
- Compose can declare and reuse named volumes, but `docker compose down -v` can remove persistent data.

## Further Reading

- [Docker Storage Overview](https://docs.docker.com/engine/storage/)
- [Docker Volumes](https://docs.docker.com/engine/storage/volumes/)
- [Bind Mounts](https://docs.docker.com/engine/storage/bind-mounts/)
- [`tmpfs` Mounts](https://docs.docker.com/engine/storage/tmpfs/)
- [Compose Volumes](https://docs.docker.com/reference/compose-file/volumes/)

## Next Chapter

Continue with [Environment Variables](06-environment-variables.md) to learn how to configure containerized applications without hardcoding environment-specific settings or secrets into images.
