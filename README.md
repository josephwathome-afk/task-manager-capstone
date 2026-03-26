# Task Manager Capstone

A production-ready task management application built as a full-stack capstone project. It lets users create, update, filter, and delete tasks through a Vue 3 frontend backed by a Flask REST API, with PostgreSQL for task storage and MongoDB for audit logging. Designed for developers learning how to ship a complete application from local development through to Kubernetes.

---

## Tech Stack

| Layer          | Technology                        |
|----------------|-----------------------------------|
| Backend API    | Python 3.12, Flask 3.1            |
| Primary DB     | PostgreSQL 16                     |
| Audit log      | MongoDB 7                         |
| Frontend       | Vue 3 (Composition API, Vite)     |
| Containerising | Docker, Docker Compose            |
| Orchestration  | Kubernetes via minikube           |
| Package mgmt   | Helm 3                            |
| Testing        | pytest with in-memory fakes       |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Browser / Developer                  │
└───────────────┬─────────────────────────────────────┘
                │ HTTP  (port 5173 in dev)
┌───────────────▼─────────────────────────────────────┐
│          Vue 3 Frontend  (TaskBoard.vue)             │
│            npm run dev → localhost:5173              │
└───────────────┬─────────────────────────────────────┘
                │ REST calls  (port 5000)
┌───────────────▼─────────────────────────────────────┐
│        Flask Backend  (routes.py / models.py)        │
│                   localhost:5000                     │
│                                                      │
│  ┌─────────────────────┐  ┌────────────────────────┐│
│  │   TaskRepository    │  │    ActivityLogger      ││
│  │    (PostgreSQL)     │  │      (MongoDB)         ││
│  └──────────┬──────────┘  └───────────┬────────────┘│
└─────────────┼─────────────────────────┼─────────────┘
              │                         │
┌─────────────▼──────────┐  ┌───────────▼──────────────┐
│  PostgreSQL 16          │  │  MongoDB 7               │
│  tasks table            │  │  activity_logs           │
│  port 5432              │  │  port 27017              │
└────────────────────────┘  └──────────────────────────┘

Kubernetes (wraps the Flask backend):
  Deployment (2 replicas) ──► NodePort Service ──► port 30080
  Pods reach Postgres + Mongo via the host machine IP (192.168.49.1)
```

---

## Project Structure

```
task-manager-capstone/
├── backend/
│   ├── app.py              # Flask application factory
│   ├── models.py           # Task · TaskRepository · ActivityLogger
│   ├── routes.py           # REST API Blueprint
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
│       └── test_tasks.py   # 20+ pytest cases (no live DB needed)
├── frontend/
│   └── task-ui/            # Vue 3 (Vite + ESLint)
│       └── src/
│           ├── App.vue
│           └── components/
│               └── TaskBoard.vue
├── k8s/
│   ├── deployment.yaml     # 2-replica Deployment
│   └── service.yaml        # NodePort on 30080
├── helm/
│   └── task-manager/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── deployment.yaml
│           └── service.yaml
├── docker-compose.yml
└── README.md
```

---

## Prerequisites

Install all of these before starting. Verify each one with the check command shown.

| Tool | Version | Install | Check |
|------|---------|---------|-------|
| Docker Engine | 24+ | [docs.docker.com/engine/install](https://docs.docker.com/engine/install/#server) | `docker --version` |
| Docker Compose | v2 | Included with Docker Engine | `docker compose version` |
| Node.js | 20+ | [nodejs.org](https://nodejs.org/) | `node --version` |
| minikube | latest | [minikube.sigs.k8s.io](https://minikube.sigs.k8s.io/docs/start/) | `minikube version` |
| kubectl | latest | [kubernetes.io/docs/tasks/tools](https://kubernetes.io/docs/tasks/tools/) | `kubectl version --client` |
| Helm | 3+ | [helm.sh/docs/intro/install](https://helm.sh/docs/intro/install/) | `helm version` |

> **Linux users:** Install Docker Engine (not Docker Desktop). Docker Desktop on Linux hijacks the Docker socket in a way that conflicts with minikube.

---

## Running Tests

Tests use in-memory fakes — **no database or Docker required**.

```bash
cd backend
pip install -r requirements.txt
pytest -v tests/test_tasks.py
```

All tests should pass in under 2 seconds.

---

## Local Setup — Docker Compose

This is the fastest way to run the full application locally.

### Step 1 — Clone the repo

```bash
git clone https://github.com/<your-username>/task-manager-capstone.git
cd task-manager-capstone
```

### Step 2 — Start the backend stack

```bash
docker compose up -d
```

Wait about 15 seconds for Postgres to become healthy, then verify all three
containers are running and their ports are mapped to the host:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected output — all three must show `0.0.0.0:PORT->PORT`:

```
NAMES                              STATUS           PORTS
task-manager-capstone-backend-1    Up               0.0.0.0:5000->5000/tcp
task-manager-capstone-postgres-1   Up (healthy)     0.0.0.0:5432->5432/tcp
task-manager-capstone-mongo-1      Up               0.0.0.0:27017->27017/tcp
```

> **Troubleshooting:** If Postgres or Mongo show `5432/tcp` without `0.0.0.0:`
> the port is not exposed to the host. Make sure your `docker-compose.yml`
> has `ports: - "5432:5432"` under postgres and `ports: - "27017:27017"`
> under mongo, then run `docker compose down && docker compose up -d`.

### Step 3 — Verify the API

```bash
curl http://localhost:5000/health
# {"status": "ok"}

curl http://localhost:5000/tasks/
# []
```

### Step 4 — Run the frontend

Open a second terminal:

```bash
cd frontend/task-ui
npm install
npm run dev
```

Open `http://localhost:5173` in your browser. The task board should load and
connect to the API automatically.

---

## Kubernetes Deployment with Helm

> **Before starting:** make sure `docker compose up -d` is already running.
> The Kubernetes pods connect to Postgres and Mongo over the host machine IP.
> Do **not** mix `kubectl apply -f k8s/` with Helm on the same resources —
> Helm must be the sole owner of the deployment or scaling will be ignored.

### Step 1 — Start minikube

```bash
minikube start
```

### Step 2 — Find the minikube host IP

Minikube runs inside a container. Your host machine is reachable from inside
it at the gateway IP of its internal network:

```bash
minikube ssh -- ip route | grep default | awk '{print $3}'
# Typically prints: 192.168.49.1
```

Note this IP — pods use it to reach Postgres and Mongo running in Docker Compose.

### Step 3 — Confirm databases are reachable at that IP

```bash
# Both must say "succeeded" before continuing
minikube ssh -- nc -zv 192.168.49.1 5432
minikube ssh -- nc -zv 192.168.49.1 27017
```

> **If these fail:** your Docker Compose ports are not exposed to the host.
> Make sure `docker-compose.yml` has `ports: - "5432:5432"` under postgres
> and `ports: - "27017:27017"` under mongo, then run:
> `docker compose down && docker compose up -d`

### Step 4 — Update helm/task-manager/values.yaml with your host IP

Open `helm/task-manager/values.yaml` and confirm the `env` block uses the
IP from Step 2. If your IP is different, update it here:

```yaml
env:
  databaseUrl: "postgresql://taskuser:taskpass@192.168.49.1:5432/taskdb"
  mongoUrl: "mongodb://192.168.49.1:27017"
  mongoDb: taskdb
```

> **This is the only place you need to change the IP.** The Helm templates
> read from `values.yaml` automatically.

### Step 5 — Build the image inside minikube

Minikube has its own Docker daemon separate from your host. The image must
be built inside it so Kubernetes can find it with `imagePullPolicy: Never`.

```bash
# Switch Docker CLI to minikube's internal daemon
eval $(minikube docker-env)

# Build the image inside minikube
docker build -t task-manager-backend:latest ./backend

# Confirm it exists inside minikube
docker images | grep task-manager-backend
# task-manager-backend   latest   <hash>   Just now

# IMPORTANT: restore Docker CLI to your host daemon immediately after
eval $(minikube docker-env --unset)

# Verify Docker Compose is still running (must not be affected)
docker ps --format "table {{.Names}}\t{{.Status}}"
```

> **Why unset?** Leaving `eval $(minikube docker-env)` active redirects
> ALL docker commands — including `docker compose` — to minikube's daemon,
> which causes Compose to fail. Always unset right after the build.

### Step 6 — Validate the Helm chart

```bash
helm lint helm/task-manager/
# Expected: 1 chart(s) linted, 0 chart(s) failed
```

Preview what Helm will create without applying anything:

```bash
helm install task-manager helm/task-manager/ --dry-run --debug
```

Check the `COMPUTED VALUES` section in the output and confirm
`databaseUrl` and `mongoUrl` show `192.168.49.1`, not `postgres-service`
or `mongo-service`. If they show the old hostnames, re-check Step 4.

### Step 7 — Install with Helm

```bash
helm install task-manager helm/task-manager/
```

Expected output:
```
NAME: task-manager
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

Watch both pods until they show `1/1 Running` (takes ~20–30 seconds):

```bash
kubectl get pods -w
```

Expected:
```
NAME                                   READY   STATUS    RESTARTS   AGE
task-manager-backend-xxxxxxxxx-aaaaa   1/1     Running   0          25s
task-manager-backend-xxxxxxxxx-bbbbb   1/1     Running   0          25s
```

> **If pods show `Error` or `CrashLoopBackOff`:**
> ```bash
> kubectl logs <pod-name>
> ```
> The most common cause is the database IP being wrong or the ports not
> being exposed. Re-run Step 3 to verify, then fix Step 4 and reinstall:
> ```bash
> helm uninstall task-manager
> helm install task-manager helm/task-manager/
> ```

### Step 8 — Verify the deployment

```bash
# Shows desired vs ready replicas
kubectl get deployment task-manager-backend
# NAME                   READY   UP-TO-DATE   AVAILABLE
# task-manager-backend   2/2     2            2

# Shows all pods with their node and IP
kubectl get pods -o wide

# Shows everything — deployment, replicaset, pods, service
kubectl get all
```

### Step 9 — Scale replicas with Helm

Helm is the sole owner of this deployment. Always scale through Helm,
never with `kubectl scale`:

```bash
# Scale to 3 replicas
helm upgrade task-manager helm/task-manager/ --set replicaCount=3

# Watch the new pod appear in real time
kubectl get pods -w
# You should see a third pod go: Pending → ContainerCreating → Running

# Confirm 3/3 ready
kubectl get deployment task-manager-backend
# READY: 3/3

# Scale back down to 2
helm upgrade task-manager helm/task-manager/ --set replicaCount=2
```

Each `helm upgrade` increments `REVISION` — you can see the full history:

```bash
helm history task-manager
# REVISION  STATUS     DESCRIPTION
# 1         superseded Install complete
# 2         superseded Upgrade complete
# 3         deployed   Upgrade complete
```

### Step 10 — Get the service URL and test

Open a **dedicated terminal** and leave it running. Closing it kills the
tunnel and the URL stops working:

```bash
minikube service task-manager-service --url
# Prints: http://127.0.0.1:XXXXX
# ⚠ Do not close this terminal
```

In your original terminal:

```bash
curl http://127.0.0.1:<PORT>/health
# {"status": "ok"}

curl http://127.0.0.1:<PORT>/tasks/
# []

# Create a task
curl -X POST http://127.0.0.1:<PORT>/tasks/ \
     -H "Content-Type: application/json" \
     -d '{"title": "My first k8s task", "description": "It works!"}'
```

### Teardown

```bash`
helm uninstall task-manager
minikube stop
```

---

## API Reference

Base URL: `http://localhost:5000` (Docker Compose) or `http://127.0.0.1:<PORT>` (Kubernetes tunnel).

| Method   | Endpoint        | Request Body                                              | Success      | Errors      |
|----------|-----------------|-----------------------------------------------------------|--------------|-------------|
| `GET`    | `/tasks/`       | —                                                         | `200` array  | —           |
| `POST`   | `/tasks/`       | `{ "title": "string", "description": "string (opt)" }`   | `201` task   | `400`       |
| `PATCH`  | `/tasks/<id>`   | `{ "status": "pending" \| "in_progress" \| "done" }`     | `200` task   | `400`, `404`|
| `DELETE` | `/tasks/<id>`   | —                                                         | `200` msg    | `404`       |
| `GET`    | `/health`       | —                                                         | `200`        | —           |

### Example requests

```bash
# Create a task
curl -X POST http://localhost:5000/tasks/ \
     -H "Content-Type: application/json" \
     -d '{"title": "Write tests", "description": "Cover all routes"}'

# Update status
curl -X PATCH http://localhost:5000/tasks/<id> \
     -H "Content-Type: application/json" \
     -d '{"status": "in_progress"}'

# Delete
curl -X DELETE http://localhost:5000/tasks/<id>
```

---

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot connect to the Docker daemon at tcp://127.0.0.1:...` | `eval $(minikube docker-env)` is still set | Run `eval $(minikube docker-env --unset)` |
| `could not translate host name "postgres-service"` | k8s deployment uses Compose service name instead of host IP | Use `192.168.49.1` in `k8s/deployment.yaml` env vars |
| `Connection refused` at `192.168.49.1:5432` | Postgres port not exposed to host | Add `ports: - "5432:5432"` in `docker-compose.yml`, restart Compose |
| Pods stuck in `CrashLoopBackOff` | DB unreachable from inside minikube | Run `minikube ssh -- nc -zv 192.168.49.1 5432` to verify connectivity |
| URL from `minikube service --url` stops working | Tunnel process was killed | Open a dedicated terminal and re-run `minikube service task-manager-service --url` |
| `minikube service --url` prints a new port every run | Docker driver tunnels are ephemeral | Always use the freshly printed URL, not a saved one |

---