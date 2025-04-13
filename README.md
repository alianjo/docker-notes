# Docker Learning Notes

These are my personal notes from going through the Docker scenario-based tutorials.

---

## 🐳 ADD or COPY
*Feel the difference between ADD and COPY*

**Notes:**
##  `COPY` vs `ADD` in Dockerfile

When building a Docker image, both `COPY` and `ADD` instructions are used to transfer files into the image. However, they have different behaviors and use cases. Understanding the differences will help you write cleaner and more predictable Dockerfiles.

---

###  `COPY` — Simple and Explicit

The `COPY` instruction is used to copy **local files and directories** from the host machine into the Docker image. It does not perform any other operations like extracting files or downloading from URLs.

####  Syntax:
```dockerfile
COPY <source> <destination>
 Use cases:
Copying application source code, configuration files, or requirements files into the image.

When you want a predictable and secure behavior.

 Example:
dockerfile

COPY requirements.txt /app/
This copies the requirements.txt file from your local directory into the /app/ folder inside the image.

 ADD — More Powerful, Less Predictable
The ADD instruction can also copy local files and directories, but it comes with additional features:

It can automatically extract compressed archive files like .tar, .tar.gz, .tgz, etc.

It can download files from a remote URL directly into the image.

 Syntax:
dockerfile

ADD <source> <destination>
 Use cases:
When you need to download a file from the internet during the build process.

When you want to automatically extract an archive into a directory inside the image.

 Examples:
Extracting a .tar.gz file:

dockerfile

ADD archive.tar.gz /app/
The archive will be automatically extracted into /app/.

Downloading from a URL:

dockerfile

ADD https://example.com/app.zip /downloads/
This downloads the remote file and saves it in /downloads/.

## ⚖️ Summary Table

| Feature                             | COPY             | ADD                             |
|-------------------------------------|------------------|----------------------------------|
| Copy local files/folders            | ✅               | ✅                               |
| Download from URL                   | ❌               | ✅                               |
| Automatically extract archives      | ❌               | ✅ (`.tar`, etc.)                |
| Behavior                            | Simple & explicit| Flexible but implicit           |

> ✅ **Best Practice:**
>
> Use `COPY` by default because it’s straightforward and does exactly what it says.  
> Only use `ADD` when you need one of its extra features (like extracting archives or downloading from URLs).



- 

---

## 🏗️ Building a Docker Image

### 🔍 What is a Docker Image?

A **Docker image** is a lightweight, stand-alone, executable package that includes everything needed to run a piece of software.

It contains:
- The code
- Runtime
- Libraries
- Environment variables
- Configuration files

Think of it as a **blueprint** for creating Docker containers.

### ✅ Why Build a Docker Image?

- Ensures consistent, portable environments
- Makes sharing and deployment easier
- Enables reproducibility and automation

### ⚙️ Prerequisites

1. Install Docker → [Get Docker](https://www.docker.com/get-started)  
2. Create a `Dockerfile` in your project

---

### 🔨 Step-by-step: Build an Image

#### 📄 Step 1: Dockerfile Example
```dockerfile
FROM python:3.9

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
```

#### 🛠️ Step 2: Build the Image
```bash
docker build -t my_image_name .
```

#### 🧪 Step 3: Verify Image Creation
```bash
docker images
```

#### 🚀 Step 4: Run the Image
```bash
docker run -d -p 5000:5000 my_image_name
```

---

---

## 📜 CMD vs ENTRYPOINT

Both `CMD` and `ENTRYPOINT` define the default command that runs when a container starts. However, they behave differently.

### 🔸 CMD

- Acts as a **default** command.
- Can be overridden by user input when using `docker run`.

#### ✅ Example:
```dockerfile
CMD ["python", "app.py"]
```

Running with an override:
```bash
docker run my_image python other_script.py
```

### 🔸 ENTRYPOINT

- Defines the **main executable** for the container.
- Cannot be overridden (unless `--entrypoint` is used).

#### ✅ Example:
```dockerfile
ENTRYPOINT ["python", "app.py"]
```

### 🤝 Using Both Together

```dockerfile
ENTRYPOINT ["python", "app.py"]
CMD ["--help"]
```

> Default behavior: runs `python app.py --help`  
> Can override CMD: `docker run my_image --version` → `python app.py --version`

---

## ✍️ Dockerfile Best Practices

### ✅ 1. Use Minimal Base Images

```dockerfile
FROM python:3.11-alpine
```

### ✅ 2. Use .dockerignore

Example `.dockerignore`:
```
.git
__pycache__/
*.pyc
node_modules/
.env
```

### ✅ 3. Order Instructions by Volatility

```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

### ✅ 4. Combine RUN Instructions

```dockerfile
RUN apt-get update && apt-get install -y     curl     git  && apt-get clean  && rm -rf /var/lib/apt/lists/*
```

### ✅ 5. Use --no-cache with pip

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

### ✅ 6. Define ENTRYPOINT and CMD clearly

```dockerfile
ENTRYPOINT ["python", "app.py"]
CMD ["--help"]
```

---

## 🌐 Docker Network Drivers

Docker supports various built-in network drivers:

| Driver     | Description                                                                |
|------------|----------------------------------------------------------------------------|
| `bridge`   | Default for standalone containers. Creates an internal isolated network.  |
| `host`     | Shares the host's network stack (no isolation).                           |
| `none`     | Disables networking completely.                                            |
| `overlay`  | Used for multi-host communication (Swarm).                                 |
| `macvlan`  | Assigns a real IP from host’s network.                                     |

---

## 🌉 Bridge Network (Default)

### ⚙️ Features:

- Isolated from host
- Containers communicate via IP (not name)
- Allows outbound internet
- Limited service discovery (use user-defined bridge for that)

```bash
docker run -d --name my_nginx nginx
docker network inspect bridge
```

---

## 🛠️ Custom Bridge Network

```bash
docker network create --driver bridge my_custom_net

docker run -d --name web --network my_custom_net nginx
docker run -d --name backend --network my_custom_net my_app
```

> Now `backend` can reach `web` by name.

---

---

## 📂 Using Bind Mounts

### 🔍 What is a Bind Mount?

Bind mounts map a file or directory on the **host machine** into the container.  
Any changes made reflect **in both directions**.

### 📦 When to Use

- Local development (live-edit without rebuilding)
- Log storage
- Config or dataset sharing

### 🔧 Syntax

#### Legacy:
```bash
docker run -v /host/path:/container/path image_name
```

#### Recommended modern syntax:
```bash
docker run --mount type=bind,source=/host/path,target=/container/path image_name
```

---

## ⚙️ Using Environment Variables

### 🔹 With `docker run`

```bash
docker run -e APP_MODE=production my_app
docker run --env APP_MODE=production my_app
```

### 📁 Using `.env` File

Create a `.env` file:
```
APP_MODE=development
SECRET_KEY=abc123
```

Then run:
```bash
docker run --env-file .env my_app
```

### 🛠️ In Docker Compose

```yaml
services:
  app:
    image: my_app
    env_file:
      - .env
```

Or inline:
```yaml
services:
  app:
    image: my_app
    environment:
      - APP_MODE=production
      - SECRET_KEY=abc123
```

### 📦 Access in Code

**Python:**
```python
import os
os.getenv("APP_MODE")
```

**Node.js:**
```js
process.env.APP_MODE
```

---

## 🔄 Updating a Containerized App

### 1️⃣ Make Code Changes

Edit your app files (`.py`, `.js`, etc.)

### 2️⃣ Rebuild the Image

```bash
docker build -t my_app:v2 .
```

### 3️⃣ Stop and Remove Old Container

```bash
docker stop my_container
docker rm my_container
```

### 4️⃣ Run Updated Container

```bash
docker run -d --name my_container -p 8080:80 my_app:v2
```

### 🔁 With Docker Compose

```bash
docker-compose build
docker-compose up -d
```

---

## 📦 Volume Mounts

### 🔍 What is a Volume?

Volumes are persistent data stores managed by Docker itself. Unlike bind mounts, they are isolated from the host FS.

### 🔧 Syntax

```bash
docker run -v my_volume:/data image_name
docker run --mount type=volume,source=my_volume,target=/data image_name
```

### 🧪 Example

```bash
docker run -d -v /my/local/mysql_data:/var/lib/mysql mysql
```

---

## ✅ Summary of Mount Types

| Feature        | Volume                         | Bind Mount                    |
|----------------|--------------------------------|--------------------------------|
| Managed by     | Docker                         | You (host)                     |
| Persistence    | Across container deletion      | Tied to host directory         |
| Portability    | Easy to migrate/share          | Host-dependent                 |
| Use Case       | Databases, logs                | Live-editing, config sharing   |

---

## 🙌 Credits

- Based on [Play with Docker Scenarios](https://github.com/nicolaslevshakov/dockerlabs)  
- Maintainer: [Nikolai Levshakov](https://github.com/nikolailevshakov)

---

Feel free to fork, improve, and share these notes with your team! 🚀
