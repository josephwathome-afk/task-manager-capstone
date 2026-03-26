# Task Manager Capstone

A production-ready Task Manager application built with Flask, Vue.js,
PostgreSQL, and MongoDB.

## Tech Stack

| Layer     | Technology              |
|-----------|-------------------------|
| Backend   | Python 3.12 · Flask 3.1 |
| Database  | PostgreSQL 16           |
| Audit log | MongoDB 7               |
| Frontend  | Vue 3 (Composition API) |
| Container | Docker Compose          |
| Orchestr. | Kubernetes + Helm       |

## Quick Start (Docker Compose)
```bash
# 1. Clone
git clone https://github.com/<you>/task-manager-capstone.git
cd task-manager-capstone

# 2. Start all services
docker compose up --build

# 3. API is live at
open http://localhost:5000/tasks/

# 4. Frontend (run separately for now)
cd frontend/task-ui
npm install
npm run dev
```

## Run Tests
```bash
cd backend
pip install -r requirements.txt
pytest -v tests/test_tasks.py
```

## API Reference

| Method | Endpoint        | Description          | Success | Error       |
|--------|-----------------|----------------------|---------|-------------|
| GET    | /tasks/         | List all tasks       | 200     |             |
| POST   | /tasks/         | Create a task        | 201     | 400         |
| PATCH  | /tasks/\<id\>   | Update task status   | 200     | 400 · 404   |
| DELETE | /tasks/\<id\>   | Delete a task        | 200     | 404         |
| GET    | /health         | Health check         | 200     |             |

## Kubernetes
```bash
# Create secret first
kubectl create secret generic task-manager-secrets \
  --from-literal=database-url='postgresql://user:pass@host:5432/taskdb' \
  --from-literal=mongo-url='mongodb://host:27017'

kubectl apply -f k8s/
```

## Project Structure
task-manager-capstone/
├── backend/
│   ├── app.py            # Flask application factory
│   ├── models.py         # Task · TaskRepository · ActivityLogger
│   ├── routes.py         # REST API Blueprint
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
│       └── test_tasks.py
├── frontend/
│
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
├── docker-compose.yml
└── README.md