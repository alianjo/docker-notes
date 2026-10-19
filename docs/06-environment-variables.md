# Environment Variables in Docker

Environment variables let applications receive configuration without hardcoding every setting into source code or container images. They are commonly used to select an application mode, configure service URLs, set feature flags, and provide non-sensitive runtime options.

This chapter explains how environment variables work in Docker, how to pass them to containers, how Docker Compose loads and interpolates `.env` files, and how to avoid treating environment variables as a secure secret store.

## Table of Contents

- [Why Configuration Matters](#why-configuration-matters)
- [Where Variables Are Used](#where-variables-are-used)
- [Set Variables with `docker run`](#set-variables-with-docker-run)
- [Use an Environment File with `docker run`](#use-an-environment-file-with-docker-run)
- [Understand `ARG` and `ENV` in a Dockerfile](#understand-arg-and-env-in-a-dockerfile)
- [Use Variables with Docker Compose](#use-variables-with-docker-compose)
- [`.env` Files and Interpolation](#env-files-and-interpolation)
- [Environment Variable Precedence in Compose](#environment-variable-precedence-in-compose)
- [Inspect Container Configuration](#inspect-container-configuration)
- [Handle Sensitive Values Safely](#handle-sensitive-values-safely)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Key Takeaways](#key-takeaways)
- [Further Reading](#further-reading)

## Why Configuration Matters

Applications often need different configuration in development, testing, and production. For example, a local API might use a development database, while a deployed API connects to a managed database service.

Hardcoding these settings into application code makes applications harder to reuse and increases the risk of accidentally committing local or sensitive values to source control.

Environment variables provide one way to separate configuration from application code:

```text
Application code
      |
      v
Reads configuration from environment variables
      |
      v
Runs with settings supplied by the environment
```

Environment variables are convenient for ordinary configuration, but they are not automatically encrypted, access-controlled, or hidden from processes that can inspect the container.

## Where Variables Are Used

Docker has several related, but distinct, variable mechanisms.

| Mechanism | Purpose | Does it automatically become a container variable? |
|---|---|---|
| Host shell variable | Stores a value in the terminal's environment | No. It must be passed into the container or used by Compose configuration. |
| `docker run -e` / `--env` | Sets a variable for a new container | Yes, for that container. |
| `docker run --env-file` | Loads variables from a file into a new container | Yes, for that container. |
| Dockerfile `ARG` | Supplies a build-time argument | No, not by itself. |
| Dockerfile `ENV` | Defines a default environment variable in an image | Yes, unless overridden at container creation. |
| Compose project `.env` | Provides values for Compose-file interpolation and some Compose CLI settings | No. A value must be referenced or passed into a service to be present in its environment. |
| Compose service `environment` | Defines environment variables for a service's containers | Yes. |
| Compose service `env_file` | Loads a file's variables into a service's container environment | Yes. |
| Compose `secrets` | Makes explicitly granted secret data available as files to a service | Available as a file, not automatically as an environment variable. |

Knowing which mechanism you are using prevents a common mistake: a variable can exist in a `.env` file on the host but still be absent from the application container.

## Set Variables with `docker run`

Use `--env` (or its short form `-e`) to set a variable when creating a container.

```powershell
# Set a variable explicitly for this container.
docker run --rm --env APP_MODE=development alpine:3.22 sh -c 'echo "$APP_MODE"'
```

The command prints `development` and removes the container after the command finishes.

You can provide more than one variable by repeating `--env`:

```powershell
docker run --rm `
    --env APP_MODE=development `
    --env LOG_LEVEL=debug `
    alpine:3.22 sh -c 'echo "$APP_MODE / $LOG_LEVEL"'
```

In PowerShell, the backtick at the end of a line is the line-continuation character. It must be the final character on the line; even a trailing space after it can break the command. You can also write the command on one line if you prefer.

### Pass a Variable from PowerShell

PowerShell stores environment variables using the `$env:` scope:

```powershell
$env:APP_MODE = "development"
docker run --rm --env APP_MODE alpine:3.22 sh -c 'echo "$APP_MODE"'
```

When `--env APP_MODE` has no explicit `=value`, Docker passes the value from the Docker CLI client's environment if it is defined there. If it is not defined, the variable is unset in the container.

The PowerShell variable belongs to the current PowerShell process and its child processes. It is not a permanent Windows system setting.

To remove it from the current PowerShell session:

```powershell
Remove-Item Env:APP_MODE
```

### Override an Image Default

If an image defines a default using Dockerfile `ENV`, a value supplied with `docker run --env` overrides that default for the newly created container:

```powershell
docker run --rm --env APP_MODE=testing my-app:local
```

This does not modify the image itself. A later container created without that override uses the image's default value, if one is configured.

## Use an Environment File with `docker run`

When several variables are needed, store them in a local environment file and pass it using `--env-file`.

For example, create `app.env`:

```dotenv
APP_MODE=development
LOG_LEVEL=debug
API_TIMEOUT_SECONDS=15
```

Run a container with the file:

```powershell
docker run --rm --env-file .\app.env alpine:3.22 sh -c 'echo "$APP_MODE / $LOG_LEVEL / $API_TIMEOUT_SECONDS"'
```

The path is interpreted relative to the current working directory. Run the command from the directory where `app.env` is located, or provide the correct path.

An environment file is typically a series of `NAME=value` entries. Do not assume that every environment-file format used by other tools has identical syntax or quoting rules. Consult Docker's documentation when using special characters or multi-line values.

**Important:** `--env-file` passes configuration into a container; it does not encrypt the file, make a password safe to commit, or prevent the value from being exposed to processes with sufficient access to inspect the container.

## Understand `ARG` and `ENV` in a Dockerfile

`ARG` and `ENV` are related but serve different purposes.

### `ARG`: Build-Time Arguments

A Dockerfile `ARG` defines a variable that can be supplied to the build process.

```dockerfile
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim
```

Build the image with an explicit argument:

```powershell
docker build --build-arg PYTHON_VERSION=3.13 -t python-app:local .
```

An `ARG` value is intended for configuring the image build. It is not automatically a runtime environment variable in containers created from the resulting image. Depending on how it is used, build metadata, image history, or build provenance may expose information about an argument.

Never pass passwords, tokens, or other secrets through `ARG`.

### `ENV`: Image and Runtime Defaults

A Dockerfile `ENV` sets an environment variable in the image configuration. Containers created from that image inherit the default unless it is overridden at runtime.

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
```

These variables configure Python behavior when a container runs. An `ENV` value can also be used by later Dockerfile instructions.

A build argument can be used to set a non-sensitive default if that is genuinely needed:

```dockerfile
ARG APP_MODE=production
ENV APP_MODE=${APP_MODE}
```

Be cautious with this pattern: the resulting `APP_MODE` is stored in the image configuration as an environment variable. Do not use it to embed secrets in an image.

### `ARG` vs. `ENV`

| Feature | `ARG` | `ENV` |
|---|---|---|
| Main purpose | Configure a build | Configure build-time instructions and provide image environment defaults |
| Set with `docker build --build-arg` | Yes | Not directly; the Dockerfile must define the value |
| Automatically available at container runtime | No | Yes |
| Appropriate for secrets | No | No |

For sensitive data required during a build, use BuildKit secret mounts rather than `ARG` or `ENV`. See [Build secrets](https://docs.docker.com/build/building/secrets/).

## Use Variables with Docker Compose

Docker Compose can define container environment variables in a `compose.yaml` file.

```yaml
services:
  api:
    image: python-api:local
    environment:
      APP_MODE: development
      LOG_LEVEL: debug
```

The values under `environment` are passed into the service containers. They are not automatically added to the host's environment.

You can use list syntax as well:

```yaml
services:
  api:
    image: python-api:local
    environment:
      - APP_MODE=development
      - LOG_LEVEL=debug
```

Mapping syntax is usually easier to read when the configuration contains several variables.

### Load a Service Environment File

Use the service-level `env_file` attribute to load variables into the container environment:

```yaml
services:
  api:
    image: python-api:local
    env_file:
      - ./app.env
```

Here, the service receives the variables from `app.env`. This is different from a project-level `.env` file used for Compose interpolation. Keep the two purposes separate when designing the project.

### Interpolate Values into Compose Configuration

A project-level `.env` file next to `compose.yaml` can provide values used by `${VARIABLE}` expressions in the Compose file.

For example, `.env`:

```dotenv
IMAGE_TAG=local
APP_MODE=development
```

And `compose.yaml`:

```yaml
services:
  api:
    image: "python-api:${IMAGE_TAG}"
    environment:
      APP_MODE: "${APP_MODE}"
```

When you run `docker compose up`, Compose substitutes the values while processing the configuration. `IMAGE_TAG` selects the image tag; `APP_MODE` is also explicitly passed into the service because it appears under `environment`.

A value in the project `.env` file does not become a container environment variable solely because it is present in that file. It needs to be referenced in the Compose service configuration, or loaded through the service's `env_file` attribute.

Inspect the resolved Compose configuration before starting services:

```powershell
docker compose config
```

Remember that this command may display resolved configuration values in the terminal. Avoid using it carelessly with sensitive values or sharing its output publicly.

### Use an Explicit Environment File

To choose a different interpolation file, use the Compose CLI's `--env-file` option:

```powershell
docker compose --env-file .env.development config
```

The path is relative to the directory from which the command is run. This option selects the file used to supply interpolation variables; it does not replace the service-level `env_file` attribute.

## `.env` Files and Interpolation

There are two common uses of files named `.env` in a Compose workflow:

1. **Project-level `.env`:** supplies values to Compose for interpolation and configuration of the Compose CLI.
2. **Service-level `env_file`:** specifies a file whose variables are placed inside the service container.

A file can be used in different ways depending on the Compose configuration, but the mechanisms are not interchangeable.

### Provide Safe Defaults

Compose supports default-value expressions. For example:

```yaml
services:
  api:
    image: "python-api:${IMAGE_TAG:-local}"
    environment:
      LOG_LEVEL: "${LOG_LEVEL:-info}"
```

If `IMAGE_TAG` is not defined for interpolation, Compose uses `local`. If `LOG_LEVEL` is not defined, the container receives `info` through the service's `environment` setting.

For variables that must be supplied, Compose supports required-variable expressions:

```yaml
services:
  api:
    image: "python-api:${IMAGE_TAG:?Set IMAGE_TAG before starting the application}"
```

If the required value is missing or empty, Compose reports an error instead of silently using an empty value.

### Keep Local Configuration Out of Git

A typical project might contain:

```text
project/
├── compose.yaml
├── .env.example
├── .gitignore
└── .env
```

The `.env.example` file should contain documented placeholders or safe defaults, not working credentials:

```dotenv
# Copy this file to .env and adjust it for your local environment.
APP_MODE=development
LOG_LEVEL=debug
DATABASE_HOST=db
DATABASE_PORT=5432
DATABASE_NAME=app_db
DATABASE_USER=app_user
DATABASE_PASSWORD=replace-with-a-local-value
```

Add the real local file to `.gitignore`:

```gitignore
.env
.env.*
!.env.example
```

Review this pattern if your project intentionally versions other `.env` files. Do not blindly ignore or commit environment files without checking what values they contain.

## Environment Variable Precedence in Compose

The same variable can be defined in several places. Compose applies a precedence order to determine the final value in the container.

The general order from highest to lowest is:

1. A value supplied through `docker compose run -e` for that one-off run.
2. Values supplied through `environment` or service `env_file` after interpolation from the shell or a Compose interpolation file.
3. Values set directly under the service's `environment` attribute.
4. Values loaded by the service's `env_file` attribute.
5. The image's Dockerfile `ENV` default.

The exact result depends on how a value is declared and whether it is interpolated. A variable in the host shell or project `.env` file does not, on its own, enter a service container unless the Compose configuration uses it.

When the same setting is defined in multiple sources, simplify the configuration where possible. Too many overlapping sources make behavior harder to debug.

For the full precedence rules and examples, see [Environment variables precedence in Docker Compose](https://docs.docker.com/compose/how-tos/environment-variables/envvars-precedence/).

## Inspect Container Configuration

To view the environment configured for a container, use `docker inspect`. Environment values can include sensitive information, so do not post the output in public issues or chat messages without reviewing it first.

```powershell
# Print the configured environment entries for an existing container.
docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' <container_name>
```

Replace `<container_name>` with the name or ID of an existing container. The output reflects its configured environment, including image defaults and container-level overrides. It does not guarantee that the application has read or correctly applied every value.

For a temporary test, print a non-sensitive variable from inside a container:

```powershell
docker exec <container_name> printenv APP_MODE
```

The command works only if the container is running and the executable is available in the container image. Minimal images may not include every diagnostic utility.

## Handle Sensitive Values Safely

Environment variables are useful for configuration, but they are not a complete secrets-management system. Values may be visible to the application process, privileged users, container inspection tools, logs, diagnostic output, or orchestration metadata.

Follow these rules:

- Never commit real passwords, production tokens, private keys, or certificates to Git.
- Do not put secrets in Dockerfile `ARG` or `ENV` instructions.
- Do not assume a `.env` file is encrypted or protected simply because it is hidden in a local project.
- Restrict access to local configuration files and CI/CD variables.
- Avoid printing environment values in application logs or debugging output.
- Prefer your deployment platform's secrets-management feature for production credentials.
- Use Docker Compose secrets when the service and runtime support them and when file-mounted secrets fit the application.

### Docker Compose Secrets

Compose secrets can make a secret available to an explicitly authorized service as a file under `/run/secrets/` in supported Linux-container scenarios.

A simplified local example is:

```yaml
services:
  api:
    image: python-api:local
    secrets:
      - db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

In this example, the API service is granted access to a file-backed secret. The application must read `/run/secrets/db_password`; Docker does not automatically convert that file into an environment variable.

This example illustrates Compose syntax, not a complete production secret-management solution. Secure the host file, keep it out of version control, and understand the guarantees and limitations of the deployment environment. Compose implementations and platforms may differ in their secret support.

See [Manage secrets securely in Docker Compose](https://docs.docker.com/compose/how-tos/use-secrets/) for details.

## Troubleshooting

### A Variable Is Empty Inside the Container

Check where the variable was defined and how it is passed into the container.

For `docker run`, specify it explicitly or use an environment file:

```powershell
docker run --rm --env APP_MODE=development alpine:3.22 sh -c 'echo "$APP_MODE"'
```

For Compose, verify that the variable is referenced in `environment`, loaded using the service's `env_file`, or otherwise explicitly supplied to the container.

### Compose Reports That a Variable Is Not Set

Run:

```powershell
docker compose config
```

Check the spelling, the directory from which Compose is run, the location of the interpolation file, and whether the variable exists in your current shell. Avoid sharing resolved output if it contains credentials.

### A Changed `.env` Value Does Not Affect an Existing Container

Changing a host-side file does not automatically change the environment of an already-created container. Recreate the service container after validating the resolved configuration:

```powershell
docker compose up -d --force-recreate api
```

Use the actual service name from your Compose file. Recreating a container can interrupt the service, so consider the impact before doing this in a shared or production environment.

### The Wrong Value Is Used

Inspect all possible sources: the image's `ENV`, the Compose `environment` and `env_file` settings, interpolation values, shell variables, and command-line overrides. Reduce duplicate definitions where possible.

## Best Practices

- Use environment variables for runtime configuration that should vary between environments.
- Keep configuration names consistent and document required variables.
- Provide a safe `.env.example` file when local setup requires environment values.
- Add real local environment files to `.gitignore` and verify that secrets are not tracked.
- Distinguish Compose interpolation files from service-level `env_file` files.
- Use explicit defaults only when a safe default exists; fail clearly when a required setting is missing.
- Understand variable precedence before overriding the same value in multiple places.
- Do not treat `ARG`, `ENV`, or `.env` files as secure storage for production secrets.
- Prefer secrets mechanisms for credentials where supported by the runtime.
- Inspect resolved configuration carefully because diagnostic output can expose values.

## Key Takeaways

- `docker run --env` sets a variable for a container; `--env-file` loads variables from a file.
- PowerShell uses `$env:NAME` to set environment variables in the current session.
- Dockerfile `ARG` is primarily for build-time configuration; Dockerfile `ENV` provides image environment defaults.
- A Compose project `.env` file supplies values for interpolation; it does not automatically inject every value into containers.
- Compose service `environment` and service `env_file` are explicit ways to configure container environments.
- Compose has defined precedence rules when values are provided from several sources.
- Environment variables and Dockerfile build arguments are not suitable for protecting secrets.
- Use appropriate secrets-management mechanisms for sensitive credentials.

## Further Reading

- [Docker run: Environment variables](https://docs.docker.com/reference/cli/docker/container/run/)
- [Docker build variables](https://docs.docker.com/build/building/variables/)
- [Docker Compose: Set environment variables](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/)
- [Docker Compose: Variable interpolation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/)
- [Docker Compose: Environment variable precedence](https://docs.docker.com/compose/how-tos/environment-variables/envvars-precedence/)
- [Docker Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/)
- [Docker build secrets](https://docs.docker.com/build/building/secrets/)

## Next Chapter

Continue with [Docker Compose](07-docker-compose.md) to learn how to define and run multi-container applications using a declarative configuration file.
