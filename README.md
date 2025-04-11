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

⚖️ Summary Table
Feature	COPY	ADD
Copy local files/folders	✅	✅
Download from URL	❌	✅
Automatically extract archives	❌	✅ (.tar, etc.)
Behavior	Simple & explicit	Flexible but implicit
✅ Best Practice
Use COPY by default because it’s straightforward and does exactly what it says.
Only use ADD when you need one of its extra features (extracting archives or downloading from URLs).



- 

---

## 🏗️ Building an image
*Build a container from scratch*

**Notes:**
## What is a Docker Image?

A **Docker image** is a lightweight, stand-alone, executable package that includes everything needed to run a piece of software, including the code, runtime, libraries, environment variables, and configuration files. Docker images are used to create Docker containers, which are instances of these images running on a Docker engine.

In simple terms, a Docker image is like a blueprint for creating containers. It's a snapshot of a filesystem with the application and its dependencies packed into a single file.

## Why Build a Docker Image?

Building a Docker image allows you to:
- Package your application and all of its dependencies in a consistent and portable environment.
- Ensure that your application will run the same way, regardless of where it is deployed (locally, on a server, or in the cloud).
- Share your application with others through a container registry like Docker Hub or your own private registry.
- Automate the deployment process by creating reproducible environments.

## Prerequisites

Before building a Docker image, ensure you have:
1. **Docker installed**: You can download and install Docker from [here](https://www.docker.com/get-started).
2. A **Dockerfile**: This file contains instructions on how the image should be built. It's like a recipe for creating your image.

## Building a Docker Image

To build a Docker image, you'll need a `Dockerfile` in the root of your project. This file contains a series of instructions on how to assemble your image. Below is a typical process for building an image.

### Step 1: Create a Dockerfile

Here is an example of a simple `Dockerfile`:

```Dockerfile
# Use an official Python runtime as a base image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any dependencies that are listed in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define the command to run your app
CMD ["python", "app.py"]
Step 2: Build the Image
Once you have your Dockerfile set up, you can build the Docker image using the docker build command. Open a terminal or command prompt, navigate to the directory where your Dockerfile is located, and run the following command:


docker build -t my_image_name .
Explanation:
docker build: This is the command used to build a Docker image.

-t my_image_name: The -t flag allows you to tag your image with a name (my_image_name). You can use this tag to refer to your image later.

.: The dot represents the build context, which is the current directory where the Dockerfile and application files are located.

Step 3: Verify the Image
After the build completes, you can verify that your image was created successfully by running:


docker images
This command will list all Docker images available locally, and you should see your newly built image listed there with the name my_image_name.

Step 4: Run the Image as a Container
Now that the Docker image is built, you can run it as a container using the docker run command. For example:


docker run -d -p 5000:5000 my_image_name
Explanation:
-d: Runs the container in detached mode, meaning it will run in the background.

-p 5000:5000: This maps port 5000 on the container to port 5000 on your host machine, making your application accessible at localhost:5000.

my_image_name: The name of the image you want to run.

To check if your container is running, you can use:


docker ps
This will show a list of running containers.

Dockerfile Instructions
Here are some of the most commonly used Dockerfile instructions:

FROM: Defines the base image to use for your Docker image. Every Dockerfile must begin with the FROM instruction.

Dockerfile

FROM ubuntu:20.04
WORKDIR: Sets the working directory inside the container.

Dockerfile

WORKDIR /app
COPY: Copies files from your local machine into the container.

Dockerfile

COPY . /app
RUN: Executes commands inside the container. Typically used for installing dependencies or setting up the environment.

Dockerfile

RUN apt-get update && apt-get install -y python3
CMD: Defines the command that will run when the container starts.

Dockerfile

CMD ["python", "app.py"]
Best Practices for Writing a Dockerfile
Use specific tags for base images: Instead of using a generic FROM python:latest, specify a version to ensure consistency across builds.

Dockerfile
FROM python:3.9
Minimize layers: Each Dockerfile instruction creates a new layer in the image. To reduce image size and build time, try to combine multiple RUN commands into one when possible.

Use .dockerignore: Just like .gitignore, a .dockerignore file helps you exclude files and directories from being added to the image (e.g., .git folder, node_modules, etc.).

Clean up unnecessary dependencies: After installing dependencies, use RUN commands to clean up temporary files and reduce image size:

Dockerfile

RUN apt-get clean && rm -rf /var/lib/apt/lists/*
Conclusion
Building a Docker image is an essential skill for packaging your applications into portable containers. By writing a proper Dockerfile and following best practices, you can ensure that your applications are easily deployable, reproducible, and consistent across different environments.
- 

---

## 📜 CMD or ENTRYPOINT
*Feel the difference between CMD and ENTRYPOINT*

**Notes:**
In Docker, both the `CMD` and `ENTRYPOINT` instructions are used to define the command that will be executed when a container starts. However, there are key differences between the two, and understanding these differences is essential for creating Docker containers that behave as expected.

## CMD

The **CMD** instruction in a Dockerfile specifies the default command that will be run when the container starts. If a user provides a command when running the container, that command will override the `CMD`.

### Syntax:
```Dockerfile
CMD ["executable", "param1", "param2"]
If the user runs the container with a command (e.g., docker run my_image_name python another_app.py), the CMD will be overridden by the user's command.

Example:
Dockerfile

CMD ["python", "app.py"]
This will run python app.py when the container starts, unless overridden by the user.

ENTRYPOINT
The ENTRYPOINT instruction in a Dockerfile specifies a command that will always be executed when the container starts. Unlike CMD, the ENTRYPOINT cannot be overridden by the user when running the container. However, additional arguments can be passed using CMD or via the docker run command.

Syntax:
Dockerfile

ENTRYPOINT ["executable", "param1", "param2"]
Example:
Dockerfile

ENTRYPOINT ["python", "app.py"]
This will always run python app.py when the container starts, and cannot be overridden by user input.

Using CMD and ENTRYPOINT Together
When both CMD and ENTRYPOINT are used together, CMD provides default arguments to the ENTRYPOINT. This allows you to define a default behavior but still allow users to pass arguments if necessary.

Example:
Dockerfile
ENTRYPOINT ["python", "app.py"]
CMD ["--help"]
In this case:

By default, the container will run python app.py --help.

If the user provides additional arguments (e.g., docker run my_image_name --version), the CMD part will be replaced, and the container will run python app.py --version.

Summary of Differences
CMD: Specifies the default command to run when the container starts, and it can be overridden by the user when running the container.

ENTRYPOINT: Specifies the command that will always be run when the container starts, and it cannot be overridden by the user.

Using Both: You can use ENTRYPOINT to define a fixed command and CMD to provide default arguments that can be overridden by the user.

This distinction allows you to have a flexible and customizable container execution flow while maintaining predictable behavior when necessary.
- 

---

## ✍️ Dockerfile best practices
*Write Dockerfile the right way*

**Notes:**
Writing a clean and efficient Dockerfile is essential for building fast, small, and maintainable Docker images. Below are some best practices:

### 1. Use a Minimal Base Image
Use lightweight images like `alpine` to reduce size and build time.

```Dockerfile
FROM python:3.11-alpine
2. Use a .dockerignore File
Exclude unnecessary files from the build context to avoid bloated images.

Example .dockerignore:


.git
__pycache__/
*.pyc
node_modules/
.env
3. Order Instructions by Volatility
Place less frequently changing instructions at the top and more volatile ones (like copying source code) at the bottom to leverage Docker’s layer caching.

Dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
4. Combine RUN Commands
To reduce the number of layers and keep images smaller:

Dockerfile

RUN apt-get update && apt-get install -y \
    curl \
    git \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
5. Use --no-cache Where Possible
Avoid caching dependencies that aren’t needed after installation.

Dockerfile
RUN pip install --no-cache-dir -r requirements.txt
6. Define Clear ENTRYPOINT and CMD
Use ENTRYPOINT to define the main command and CMD to set default arguments that can be overridden.

Dockerfile

ENTRYPOINT ["python", "app.py"]
CMD ["--help"]
🧠 Cached Layers in Docker
Docker builds images in layers, and each instruction in the Dockerfile creates a new layer. These layers are cached, which means if a layer hasn't changed since the last build, Docker will reuse it to speed up the build process.

✅ Example:
Dockerfile

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
If only your source code changes but requirements.txt stays the same, Docker will reuse the cached layer for pip install, speeding up the build significantly.

🔁 Key Tip:
Avoid placing volatile instructions (like COPY . .) too early in the Dockerfile. Doing so invalidates all cached layers below it, making the build slower.

📚 Summary
Best Practice	Why It Matters
Use minimal base images	Smaller, faster images
Add .dockerignore	Avoid unnecessary files in image
Order instructions smartly	Improves caching and build speed
Combine RUN steps	Reduces image size
Avoid cache for temporary dependencies	Keeps images clean and efficient
Use CMD and ENTRYPOINT properly	Better control over container behavior
- 

---

## 🌐 Network drivers
*Run container in different kinds of network*

**Notes:**
Network drivers in Docker define how containers communicate with each other, the host, and external networks.

Docker provides several built-in network drivers:

| Driver      | Description                                                                 |
|-------------|-----------------------------------------------------------------------------|
| `bridge`    | Default for standalone containers. Creates an isolated internal network.    |
| `host`      | Shares the host's networking stack. No network isolation.                   |
| `none`      | Disables all networking. Useful for security or manual configuration.       |
| `overlay`   | Enables communication across multiple Docker hosts (used in Swarm/K8s).     |
| `macvlan`   | Assigns a real IP from the physical network. Appears as a physical device.  |

---

## 🌉 Bridge Network (Default Network)

The **bridge** network is Docker's default network driver for containers that are not explicitly attached to any user-defined network.

When you run a container without specifying a network, Docker connects it to the default `bridge` network.

### ⚙️ Features:
- Containers can communicate via **IP addresses** (not by names).
- Containers are **isolated** from the host network.
- Outbound internet access is allowed.
- Not suitable for service discovery via names — use custom bridge networks for that.

---

## 🧪 Running Containers in the Default Bridge Network

```bash
docker run -d --name my_nginx nginx
This starts a container in the default bridge network. You can inspect the network with:


docker network inspect bridge
You can also connect another container to this same network manually:


docker run -d --name my_app --network bridge my_image
🛠️ Creating and Using a Custom Bridge Network
Creating your own bridge network allows name-based communication between containers:


docker network create --driver bridge my_custom_network
Attach containers to it:


docker run -d --name web --network my_custom_network nginx
docker run -d --name backend --network my_custom_network my_app
Now backend can access web via container name web.

🧾 Summary
Concept	Description
bridge network	Default network for standalone containers
host network	Shares network with host — no isolation
none network	No networking at all
Custom bridge network	Enables name-based discovery and better control
overlay / macvlan	Advanced use-cases like multi-host networking
- 

---

## 🔁 Port-forwarding in Docker
*Open ports in Docker containers*

**Notes:**
When you run a container, it is **isolated from your host machine** by default — meaning no ports are accessible unless you explicitly **publish** them.

**Port forwarding** allows you to map a port on your host machine to a port inside the container, so outside clients can communicate with your app.

---

## 📦 Syntax: Publish a Port

```bash
docker run -p <host_port>:<container_port> image_name
✅ Example:

docker run -d -p 8080:80 nginx
This tells Docker to:

Listen on port 8080 on the host machine.

Forward all traffic to port 80 inside the container (used by nginx).

Now you can access your app in the browser at:
👉 http://localhost:8080

📘 Difference Between EXPOSE and -p
Command	Purpose
EXPOSE	Documents which port the container uses, no actual port mapping
-p	Actively maps a host port to a container port (enables external access)
Example in Dockerfile:
Dockerfile
EXPOSE 80
But to actually access it, you still need to run:


docker run -p 8080:80 my_app
🔐 Limiting Binding to Specific IPs
You can restrict which interface Docker binds the port to:

Command	Behavior
-p 8080:80	Accessible on all interfaces (0.0.0.0)
-p 127.0.0.1:8080:80	Accessible only on localhost
-p 192.168.1.100:8080:80	Accessible only on specific IP
🧪 Testing Port Binding
You can inspect running containers and their published ports using:


docker ps
You'll see a column like:

nginx
PORTS
0.0.0.0:8080->80/tcp
This means the container port 80 is forwarded to 8080 on the host.

🧾 Summary
Concept	Description
Port forwarding	Exposes a container's port to the host or external network
-p option	Maps host port to container port
EXPOSE keyword	Documents the port (no functional effect)
Host IP bindings	Can limit access to localhost or specific IP addresses
For more info, check the official Docker port mapping docs.


- 

---

## 🔄 Updating containerized application
*Rebuild image*

**Notes:**
## 🚀 Why Do You Need to Rebuild?

When you're running an application inside a Docker container, the code is packaged into a **Docker image**.  
If you update your application code, **Docker doesn't know** unless you rebuild the image.

---

## 🔁 Typical Update Workflow

Here’s the standard process to update a containerized application:

### 1. 🛠️ Make Code Changes
Edit your application source code (e.g., `app.py`, `main.js`, `index.html`, etc.).

---

### 2. 🧱 Rebuild the Image
Use the `docker build` command to create a new image:

```bash
docker build -t my_app:v2 .
Best practice: Tag your image with a version or meaningful tag.

3. 🧹 Stop & Remove the Old Container

docker stop my_container
docker rm my_container
You must remove the old container to run a new one from the updated image.

4. 🚀 Run a New Container with the Updated Image

docker run -d --name my_container -p 8080:80 my_app:v2
Now your app runs with the latest code and image.

⚙️ With docker-compose
If you're using docker-compose, simply run:

docker-compose build
docker-compose up -d
This will rebuild your services and start them with the updated code.

🧾 Summary
Step	Command Example
Update code	Edit files in your app
Rebuild image	docker build -t my_app:v2 .
Stop & remove old	docker stop / docker rm
Run updated container	docker run -d -p 8080:80 my_app:v2
Compose rebuild	docker-compose build && docker-compose up
For automated workflows, consider using CI/CD tools like GitHub Actions, Jenkins, or GitLab CI to handle rebuilds and deployments automatically.



- 

---

## 📂 Using bind mounts
*Start a container with bind mount*

**Notes:**
## 🔍 What Is a Bind Mount?

A **bind mount** allows you to attach a file or directory from your **host machine** into a **container**.  
Changes in the mount are reflected **both ways** — if you change a file on the host, it's immediately updated inside the container and vice versa.

---

## 🧱 When to Use Bind Mounts?

- During **local development**, so you can edit files live without rebuilding the image.
- To **store logs or output** from the container on the host.
- For **sharing config files** or datasets with the container.

---

## 📦 Syntax

### 🔸 Legacy style:
```bash
docker run -v /path/on/host:/path/in/container image_name
🔸 Recommended modern style:

docker run --mount type=bind,source=/path/on/host,target=/path/in/container image_name
🧪 Example
Mount your local project directory into a container:


docker run --mount type=bind,source=/home/user/projects/flask-app,target=/app python:3.10-slim
This means:

The local folder /home/user/projects/flask-app is available at /app inside the container.

Any code you edit in your IDE will immediately reflect inside the container.

⚠️ Important Notes
The host path must exist before running the container.

Docker does not copy the contents of the container path to the host — the host path takes over.

Bind mounts can override container content, so use them carefully.

🧾 Summary
Feature	Description
Two-way sync	Changes on host and container reflect in both places
Development use	Great for live-reload and avoiding image rebuilds
Command format	--mount type=bind,source=/path/on/host,target=/path/in/container
Tip	Use absolute paths on the host (no ~ or relative paths)


- 

---

## ⚙️ Using environment variables
*Run docker container with environment variables*

**Notes:**
- 
Environment variables (env vars) are used to pass configuration settings, secrets, and other dynamic data into your Docker containers **without hardcoding them into your code**.

---

## 🛠️ Pass Environment Variables on `docker run`

You can use the `-e` or `--env` flag to pass env vars at runtime:

```bash
docker run -e APP_MODE=production my_app
Or:

docker run --env APP_MODE=production my_app
📁 Use a .env File
Create a .env file with multiple variables:

dotenv

# .env
APP_MODE=development
SECRET_KEY=abc123
Then pass it to Docker:


docker run --env-file .env my_app
⚙️ With Docker Compose

version: "3"
services:
  app:
    image: my_app
    env_file:
      - .env
You can also define environment variables inline:


services:
  app:
    image: my_app
    environment:
      - APP_MODE=production
      - SECRET_KEY=abc123
📦 Accessing Environment Variables Inside the Container
Inside your app, you can access them using your language's standard tools.

In Python:
python
import os
mode = os.getenv("APP_MODE")
In Node.js:
js

const mode = process.env.APP_MODE;
⚠️ Best Practices
Keep secrets like API keys, DB credentials, and tokens outside the code.

Don’t hardcode sensitive data inside your Dockerfile.

Use .env files (and exclude them from version control with .gitignore).

✅ Summary
Feature	Command / Usage Example
Single env var	docker run -e VAR=value image
Multiple from file	docker run --env-file .env image
Compose with .env	env_file: [".env"]
Access inside code	os.getenv() in Python, process.env in Node

---

## 📦 Using volume mounts
*Run container with mounted volume*

**Notes:**
- 
A **volume mount** allows you to persist data generated by and used in Docker containers. Volumes are managed by Docker and are stored outside of the container, ensuring data is not lost even if the container is deleted.

---

## 🧱 What Is a Volume?

A **volume** is a persistent data storage mechanism in Docker. Unlike bind mounts, volumes are completely managed by Docker, and they are not dependent on the host filesystem.

---

## 📦 Mounting Volumes

### 🔸 Syntax:

```bash
docker run -v /path/on/host:/path/in/container image_name
Or with the --mount flag:


docker run --mount type=volume,source=my_volume,target=/path/in/container image_name
-v or --mount: Mounts a volume to the container.

source: Path on the host machine or the name of the Docker volume.

target: Path inside the container where the data will be mounted.

🧪 Example
To run a MySQL container with a mounted volume:


docker run -d -v /my/local/mysql_data:/var/lib/mysql mysql
In this example:

/my/local/mysql_data: The local directory on your host where MySQL data is stored.

/var/lib/mysql: The directory inside the container where MySQL stores its data.

⚙️ Volume vs Bind Mount
Feature	Volume	Bind Mount
Management	Managed by Docker	Managed by the user
Data Persistence	Data persists even if the container is deleted	Data is directly linked to the host directory
Portability	Easily shareable between containers	Host-dependent
Use Case	Database storage, persistent logs	Local development, shared config
🧾 Summary
Command	Description
Mount a volume	docker run -v /path/on/host:/path/in/container image_name
Mount a named volume	docker run --mount type=volume,source=my_volume,target=/path/in/container image_name

---

## Credits
Docker training scenarios from: [Play with Docker Scenarios](https://github.com/nicolaslevshakov/dockerlabs)

Maintainer: [Nikolai Levshakov](https://github.com/nikolailevshakov)

---

Feel free to fork and add your own examples or notes!
