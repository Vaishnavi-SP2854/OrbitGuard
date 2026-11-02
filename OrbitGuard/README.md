# OrbitGuard

## Prerequisites

Before running this project, ensure you have the following installed:
* **Docker Desktop** (includes Docker Compose)
* A terminal or command-line interface

---

## Local Development with Docker Compose

We use Docker Compose to manage this application's multi-container environment. Below are the standard commands required to build, run, and manage the services.

### 1. Build the Image
To build or rebuild the Docker images defined in the configuration, run:
```bash
docker compose build
```
* **What it does:** It reads the `docker-compose.yml` file, looks for any services with a `build` property, and executes their respective `Dockerfile` configurations.
* **When to use it:** Use this when you have made changes to your source code, configuration files, or dependency manifests (e.g., `package.json`, `requirements.txt`, `Gemfile`) and need those updates compiled into a fresh image. It does **not** start the containers.

### 2. Start Services in the Foreground
To build (if missing) and start all containers in your terminal window, run:
```bash
docker compose up
```
* **What it does:** It creates the necessary networks, volumes, and containers, then starts up the application. Your terminal will remain attached to the processes, streaming all container log outputs directly to your screen.
* **When to use it:** Use this during active development when you need to closely monitor real-time logs, error stack traces, or console outputs. 
* **How to stop it:** Press `Ctrl + C` in the terminal window to safely stop the running containers.

### 3. Start Services in the Background (Detached Mode)
To start the entire application suite silently in the background, run:
```bash
docker compose up -d
```
* **What it does:** The `-d` flag stands for **detached mode**. It launches all containers exactly like the standard `up` command, but immediately releases control of your terminal prompt.
* **When to use it:** Use this when you want the application running stably in the background while you use the same terminal window for other commands (e.g., running tests, navigating directories).

---

## Managing the Containers

If you started your application using detached mode (`-d`), use these commands to manage it:

* **View Logs:** `docker compose logs -f` (Streams background logs to your terminal).
* **Check Status:** `docker compose ps` (Lists all running project containers and their ports).
* **Stop Services:** `docker compose down` (Stops the containers and safely removes the internal networks created by the project).
* **Remove Services/Images:** `docker compose down --rmi all` (Stops the containers, safely removes the internal networks, images and containers created by the project)
