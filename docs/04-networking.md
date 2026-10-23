# Docker Networking

Docker networking determines how containers communicate with one another, with the Docker host, and with systems outside the host. Understanding networks and port publishing is essential when running APIs, databases, caches, reverse proxies, and other backend services.

This chapter introduces the common network drivers, explains container DNS and published ports, and provides PowerShell-friendly exercises you can run on a local Docker installation.

## Table of Contents

- [Networking Fundamentals](#networking-fundamentals)
- [Docker Network Drivers](#docker-network-drivers)
- [Inspect Existing Networks](#inspect-existing-networks)
- [Create a User-Defined Bridge Network](#create-a-user-defined-bridge-network)
- [Container-to-Container Communication](#container-to-container-communication)
- [Publish Container Ports](#publish-container-ports)
- [Networking in Docker Compose](#networking-in-docker-compose)
- [Network Isolation and Security](#network-isolation-and-security)
- [Troubleshooting Network Problems](#troubleshooting-network-problems)
- [Common Mistakes](#common-mistakes)
- [Key Takeaways](#key-takeaways)
- [Further Reading](#further-reading)

## Networking Fundamentals

A container has its own network namespace and network configuration. Docker connects containers to networks and configures connectivity according to the selected network driver and options.

A typical backend development setup may contain:

- An API container that handles HTTP requests.
- A PostgreSQL container that stores application data.
- A Redis container used for caching or background work.
- A reverse proxy that receives traffic from users and forwards it to the API.

These services do not all need to be exposed directly to the host or the public internet. Usually, only the entry point—such as the API or reverse proxy—needs a published port. Internal services can communicate over a Docker network without publishing their ports to the host.

### Important Terms

**Network:** A logical connection that controls which containers can communicate through a Docker network driver.

**Container port:** A port on which a process inside a container listens. Declaring or listening on a container port does not, by itself, publish that port on the host.

**Published port:** A mapping from a port on a host address to a port in a container, commonly configured with `-p` or `--publish`.

**DNS service discovery:** On user-defined bridge networks and Compose networks, containers can generally reach one another using container names or Compose service names rather than hard-coded IP addresses.

**Network isolation:** Separating unrelated services into different networks can reduce unnecessary connectivity. Network membership is one part of a broader security design, not a complete security boundary.

## Docker Network Drivers

Docker supports multiple network drivers for different scenarios.

| Driver | Typical purpose | Notes |
|---|---|---|
| `bridge` | Connect containers on one Docker host | Common choice for local development; user-defined bridge networks provide automatic name resolution between containers. |
| `host` | Use the host's network stack directly | Removes the usual network isolation; behavior and availability depend on the platform. |
| `none` | Disable external container networking | Useful for workloads that do not require network access. |
| `overlay` | Connect services across Docker hosts | Commonly used with Docker Swarm. |
| `macvlan` | Give containers their own MAC addresses on a physical network | Advanced networking; requires appropriate network infrastructure and configuration. |
| `ipvlan` | Connect containers using an IPvlan interface | Advanced networking for more direct control over addressing and network integration. |

For most single-host development setups, start with a user-defined `bridge` network. You generally do not need `host`, `macvlan`, `ipvlan`, or `overlay` for a typical API and database running on one computer.

## Inspect Existing Networks

List the networks known to Docker:

```powershell
docker network ls
```

Inspect the default bridge network:

```powershell
docker network inspect bridge
```

Inspect a particular network by name:

```powershell
docker network inspect <network_name>
```

Replace `<network_name>` with the name of an existing network. The output includes configuration and information about connected containers.

Docker normally creates built-in networks such as `bridge`, `host`, and `none`. Containers started without an explicit network are attached to the default `bridge` network, unless another network mode is configured.

## Create a User-Defined Bridge Network

A user-defined bridge is generally preferable to relying on the default bridge when you need multiple containers to communicate.

Create a network:

```powershell
docker network create docker-notes-net
```

Confirm that it exists:

```powershell
docker network ls
```

Inspect it:

```powershell
docker network inspect docker-notes-net
```

Containers attached to this network can communicate with one another through the network. Docker provides automatic DNS resolution for container names and network aliases on user-defined bridge networks.

### Why Prefer a User-Defined Bridge?

Compared with the default bridge, a user-defined bridge provides:

- Automatic resolution of container names and aliases through Docker's embedded DNS.
- Better separation between unrelated application groups when each group uses its own network.
- The ability to connect and disconnect running containers from the network.
- Network-specific configuration options.

Do not rely on hard-coded container IP addresses for routine application communication. Addresses can change when containers are recreated; use service or container names on the appropriate network instead.

## Container-to-Container Communication

The following exercise starts an Nginx web server on a dedicated network and then requests it from a temporary BusyBox container attached to the same network.

### Step 1: Create the Network

```powershell
docker network create docker-notes-net
```

If Docker reports that the network already exists, you can reuse it for this exercise.

### Step 2: Start the Web Container

```powershell
docker run --detach --name docker-notes-web --network docker-notes-net --publish 127.0.0.1:8080:80 nginx:alpine
```

This command:

- Runs Nginx in the background.
- Connects the container to `docker-notes-net`.
- Gives the container the name `docker-notes-web`.
- Publishes container port `80` to host port `8080`, bound to the host loopback interface.

### Step 3: Request Nginx by Container Name

Run a temporary BusyBox container on the same network:

```powershell
docker run --rm --network docker-notes-net busybox:1.36 wget -qO- http://docker-notes-web
```

The command should print the default Nginx HTML response. The temporary BusyBox container is removed after the command finishes because `--rm` was specified.

This demonstrates service discovery on a user-defined bridge: the client uses `docker-notes-web` as a hostname instead of knowing the web container's IP address.

If this command fails, confirm that the Nginx container is running and that both containers use the same user-defined network:

```powershell
docker ps
docker network inspect docker-notes-net
```

### Step 4: Test Access from the Host

Open the following URL in a browser on the Docker host:

http://localhost:8080

You should see the Nginx welcome page. The `127.0.0.1` binding means this published port is intended to be reachable from the host itself, rather than from other machines using the host's network interfaces.

### Step 5: Clean Up

Stop and remove the web container:

```powershell
docker stop docker-notes-web
docker rm docker-notes-web
```

After removing all containers connected to the test network, remove the network:

```powershell
docker network rm docker-notes-net
```

If the network is still in use, Docker will refuse to remove it. Disconnect or remove the connected containers first.

## Publish Container Ports

A process may listen on a container port without that port being published on the host. To allow host applications or external clients to reach a service through a bridge network, you normally publish the required port.

The general syntax is:

```powershell
docker run --publish <host_port>:<container_port> <image>
```

For example, the following command publishes Nginx's container port `80` on host port `8080`:

```powershell
docker run --detach --name nginx-example --publish 127.0.0.1:8080:80 nginx:alpine
```

The mapping is read as `host_address:host_port:container_port`.

### Binding to a Specific Host Address

For local development, binding a port to loopback is often safer:

```powershell
docker run --detach --name local-web --publish 127.0.0.1:8081:80 nginx:alpine
```

You can then open `http://localhost:8081` on the Docker host.

When the host address is omitted, such as with `-p 8080:80`, Docker normally publishes the port on all host addresses. Depending on the host's network and firewall configuration, the service may be reachable from other machines. Publish only the ports that need to be reachable, and choose the host binding deliberately.

### View Published Ports

List running containers and their mappings:

```powershell
docker ps
```

Inspect a specific container's port configuration:

```powershell
docker port nginx-example
```

Remove the example when you have finished:

```powershell
docker stop nginx-example
docker rm nginx-example
```

### Publishing Is Different from `EXPOSE`

The Dockerfile instruction `EXPOSE` documents the port on which an application is expected to listen. It does not publish the port to the host by itself. Port publishing is configured when creating or starting the container, for example with `docker run -p` or the Compose `ports` setting.

Containers on the same user-defined bridge network can normally reach each other's listening ports directly without publishing those ports to the host. This is a useful way to keep a database accessible to an API without exposing the database port externally.

## Networking in Docker Compose

Docker Compose creates a default network for a project and connects the project's services to it. Services on that network can discover each other by service name.

Consider this simplified example:

```yaml
services:
  api:
    build: .
    ports:
      - "127.0.0.1:8000:8000"
    depends_on:
      - db

  db:
    image: postgres:17
    environment:
      POSTGRES_DB: app_db
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD first}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

This is an illustrative configuration, not a complete standalone application. It assumes an API build context with a suitable Dockerfile, that the API listens on port `8000`, and that `POSTGRES_PASSWORD` is supplied through the environment or another appropriate configuration mechanism. Do not commit real passwords to source control.

Inside the Compose network, the API should use `db` as the database hostname and the container port `5432` as the database port. It should not use `localhost` to refer to PostgreSQL: from inside the API container, `localhost` refers to the API container itself.

Notice that the example does not publish PostgreSQL's port. The API can access PostgreSQL over the internal Compose network. If a host-based database client needs access during local development, publish the database port deliberately, preferably bound to `127.0.0.1` when remote access is not required.

`depends_on` controls dependency startup order, but short-form `depends_on` alone does not guarantee that the database is ready to accept connections. Applications should handle transient connection failures, and Compose health checks can be used when readiness-based startup behavior is required.

For more detail, see [Docker Compose](07-docker-compose.md).

## Network Isolation and Security

Networking is also an important security consideration.

- **Publish only required ports.** Avoid exposing database, cache, and administration ports unless there is a concrete requirement.
- **Bind local-only services to loopback.** For example, `127.0.0.1:8000:8000` restricts a published mapping to the host's IPv4 loopback address.
- **Separate unrelated application groups.** Use distinct user-defined networks to reduce unnecessary connectivity between stacks.
- **Do not treat a network as authentication.** Services still need appropriate credentials, access controls, and secure application configuration.
- **Avoid embedding secrets in images.** Use suitable secret-management mechanisms and deployment-specific configuration.
- **Understand host networking.** The `host` driver removes normal network isolation and does not use ordinary port publishing in the same way as bridge networking. Its support and behavior vary by platform.
- **Review firewall behavior.** Docker configures network rules for bridge networking. Understand the interaction with your host firewall, and avoid manually changing Docker-managed firewall rules without a clear plan.

See the official [Docker networking security and firewall documentation](https://docs.docker.com/engine/network/packet-filtering-firewalls/) for platform-specific details.

## Troubleshooting Network Problems

When a container cannot reach another service, check the problem step by step instead of changing multiple settings at once.

### 1. Check Container Status

```powershell
docker ps -a
```

A stopped container cannot serve new connections. Inspect its logs and exit status before debugging the network:

```powershell
docker logs <container_name>
docker inspect <container_name>
```

### 2. Check Network Membership

```powershell
docker network ls
docker network inspect <network_name>
```

Confirm that the relevant containers are connected to the expected network. Name-based discovery requires a network that supports the relevant DNS behavior, such as a user-defined bridge or a Compose network.

### 3. Check the Host-to-Container Port Mapping

```powershell
docker ps
docker port <container_name>
```

Confirm the application listens on the expected container port and that the host port is mapped correctly. A published port cannot help if the application process is not listening inside the container.

### 4. Use the Correct Hostname

- From the Docker host, use the published host address and port, such as `http://localhost:8080`.
- From another container on the same user-defined bridge, use the container name or network alias and the container's listening port.
- From one Compose service to another, use the Compose service name and the container port.

Do not use `localhost` from one container to refer to another container.

### 5. Verify the Application Is Listening

The application often needs to listen on `0.0.0.0` inside its container to accept connections through its container interface. If a web application listens only on `127.0.0.1` inside the container, other containers and published-port forwarding may be unable to reach it as intended.

For example, a development server might need to be started with a host binding of `0.0.0.0` inside the container. The exact command depends on the application framework.

### 6. Check Firewall and Platform Details

On Linux, Docker manages firewall rules for bridge-network behavior and port publishing. Docker Desktop adds a platform-specific networking layer on Windows and macOS. If all container configuration looks correct, consult the documentation for the Docker platform and host firewall in use.

## Common Mistakes

**Using container IP addresses as permanent configuration.** Container addresses can change after recreation. Prefer names or aliases on a shared user-defined network.

**Assuming `EXPOSE` publishes a port.** It does not create a host port mapping. Use `ports` in Compose or `-p` with `docker run` when host access is required.

**Publishing every service.** A database does not need a published host port just because an API needs to access it on an internal network.

**Using `localhost` for another container.** `localhost` refers to the current network namespace. Use the relevant service or container name instead.

**Assuming `depends_on` always means ready.** Startup order and application readiness are different concerns.

**Using the default bridge for every workload.** A user-defined bridge generally provides better name resolution and more deliberate grouping for standalone containers.

**Assuming a published port is private.** Without an explicit host address, Docker normally publishes to all host addresses. Check bindings and firewall policy before exposing a service.

## Key Takeaways

- Docker networks control connectivity between containers and external systems.
- User-defined bridge networks are a good default for communication between containers on one host.
- Containers on a shared user-defined bridge can normally resolve one another by name.
- Port publishing creates a host-to-container mapping; listening on a container port alone does not publish it.
- Binding published ports to `127.0.0.1` is useful for many local development workflows.
- Compose services use service names for internal communication and normally share a project network.
- Network isolation, limited port publishing, credentials, and host firewall configuration all contribute to security.

## Further Reading

- [Docker Network Drivers](https://docs.docker.com/engine/network/drivers/)
- [Bridge Network Driver](https://docs.docker.com/engine/network/drivers/bridge/)
- [Port Publishing and Mapping](https://docs.docker.com/engine/network/port-publishing/)
- [Networking in Docker Compose](https://docs.docker.com/compose/how-tos/networking/)
- [Packet Filtering and Firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/)

## Next Chapter

Continue with [Volumes and Storage](05-volumes-and-storage.md) to learn how to persist data beyond a container's lifecycle and when to use named volumes, bind mounts, and tmpfs mounts.
