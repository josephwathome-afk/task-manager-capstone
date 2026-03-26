import sys
import os
import pytest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
from models import Task


# In-memory fakes (no real databases required)

class FakeTaskRepository:
    def __init__(self):
        self._store: dict[str, Task] = {}

    def get_all(self) -> list[Task]:
        return sorted(
            self._store.values(),
            key=lambda t: t.created_at,
            reverse=True,
        )

    def get_by_id(self, task_id: str) -> Task | None:
        return self._store.get(task_id)

    def create(self, title: str, description: str = "") -> Task:
        task = Task(title=title, description=description)
        self._store[task.id] = task
        return task

    def update_status(self, task_id: str, new_status: str) -> Task | None:
        task = self._store.get(task_id)
        if task is None:
            return None
        if new_status not in Task.VALID_STATUSES:
            raise ValueError(f"Invalid status '{new_status}'.")
        task.status = new_status
        task.updated_at = datetime.now(timezone.utc)
        return task

    def delete(self, task_id: str) -> bool:
        if task_id in self._store:
            del self._store[task_id]
            return True
        return False


class FakeActivityLogger:
    def __init__(self):
        self.logs: list[dict] = []

    def log_create(self, task: Task) -> None:
        self.logs.append({"action": "create", "task_id": task.id})

    def log_update(self, task: Task, old_status: str) -> None:
        self.logs.append(
            {"action": "update", "task_id": task.id, "old_status": old_status}
        )

    def log_delete(self, task_id: str, title: str) -> None:
        self.logs.append({"action": "delete", "task_id": task_id, "title": title})


@pytest.fixture()
def fake_repo():
    return FakeTaskRepository()


@pytest.fixture()
def fake_logger():
    return FakeActivityLogger()


@pytest.fixture()
def client(fake_repo, fake_logger):
    app = create_app(
        config={
            "TESTING": True,
            "DATABASE_URL": "not-used",
            "MONGO_URL": "not-used",
            "TASK_REPO": fake_repo,
            "ACTIVITY_LOGGER": fake_logger,
        }
    )
    with app.test_client() as c:
        yield c

def _seed(repo: FakeTaskRepository, title="Buy milk", description="") -> Task:
    """Insert a task directly into the fake repo."""
    return repo.create(title=title, description=description)


class TestGetTasks:
    def test_returns_empty_list_initially(self, client):
        res = client.get("/tasks/")
        assert res.status_code == 200
        assert res.get_json() == []

    def test_returns_all_tasks(self, client, fake_repo):
        _seed(fake_repo, "Task A")
        _seed(fake_repo, "Task B")
        res = client.get("/tasks/")
        assert res.status_code == 200
        assert len(res.get_json()) == 2

    def test_task_shape(self, client, fake_repo):
        _seed(fake_repo, "Shape test")
        data = client.get("/tasks/").get_json()
        task = data[0]
        for key in ("id", "title", "description", "status", "created_at", "updated_at"):
            assert key in task, f"Key '{key}' missing from response"

    def test_default_status_is_pending(self, client, fake_repo):
        _seed(fake_repo, "Pending task")
        data = client.get("/tasks/").get_json()
        assert data[0]["status"] == "pending"


class TestCreateTask:
    def test_creates_task_successfully(self, client):
        res = client.post("/tasks/", json={"title": "New task"})
        assert res.status_code == 201
        body = res.get_json()
        assert body["title"] == "New task"
        assert body["status"] == "pending"
        assert "id" in body

    def test_missing_title_returns_400(self, client):
        res = client.post("/tasks/", json={})
        assert res.status_code == 400

    def test_blank_title_returns_400(self, client):
        res = client.post("/tasks/", json={"title": "   "})
        assert res.status_code == 400

    def test_create_with_description(self, client):
        res = client.post(
            "/tasks/", json={"title": "With desc", "description": "Details here"}
        )
        assert res.status_code == 201
        assert res.get_json()["description"] == "Details here"

    def test_create_logs_activity(self, client, fake_logger):
        client.post("/tasks/", json={"title": "Logged task"})
        assert len(fake_logger.logs) == 1
        assert fake_logger.logs[0]["action"] == "create"

    def test_no_body_returns_400(self, client):
        res = client.post(
            "/tasks/",
            data="not json",
            content_type="application/json",
        )
        assert res.status_code == 400


class TestUpdateTask:
    def test_update_status_to_in_progress(self, client, fake_repo):
        task = _seed(fake_repo, "Update me")
        res = client.patch(f"/tasks/{task.id}", json={"status": "in_progress"})
        assert res.status_code == 200
        assert res.get_json()["status"] == "in_progress"

    def test_update_status_to_done(self, client, fake_repo):
        task = _seed(fake_repo, "Finish me")
        res = client.patch(f"/tasks/{task.id}", json={"status": "done"})
        assert res.status_code == 200
        assert res.get_json()["status"] == "done"

    def test_update_nonexistent_task_returns_404(self, client):
        res = client.patch(
            "/tasks/00000000-0000-0000-0000-000000000000",
            json={"status": "done"},
        )
        assert res.status_code == 404

    def test_invalid_status_returns_400(self, client, fake_repo):
        task = _seed(fake_repo, "Bad status")
        res = client.patch(f"/tasks/{task.id}", json={"status": "flying"})
        assert res.status_code == 400

    def test_missing_status_field_returns_400(self, client, fake_repo):
        task = _seed(fake_repo, "No status")
        res = client.patch(f"/tasks/{task.id}", json={})
        assert res.status_code == 400

    def test_update_logs_activity(self, client, fake_repo, fake_logger):
        task = _seed(fake_repo, "Log update")
        client.patch(f"/tasks/{task.id}", json={"status": "done"})
        update_logs = [l for l in fake_logger.logs if l["action"] == "update"]
        assert len(update_logs) == 1
        assert update_logs[0]["old_status"] == "pending"


class TestDeleteTask:
    def test_delete_existing_task(self, client, fake_repo):
        task = _seed(fake_repo, "Delete me")
        res = client.delete(f"/tasks/{task.id}")
        assert res.status_code == 200

    def test_delete_removes_task_from_list(self, client, fake_repo):
        task = _seed(fake_repo, "Gone soon")
        client.delete(f"/tasks/{task.id}")
        res = client.get("/tasks/")
        assert all(t["id"] != task.id for t in res.get_json())

    def test_delete_nonexistent_task_returns_404(self, client):
        res = client.delete("/tasks/00000000-0000-0000-0000-000000000000")
        assert res.status_code == 404

    def test_delete_logs_activity(self, client, fake_repo, fake_logger):
        task = _seed(fake_repo, "Log delete")
        client.delete(f"/tasks/{task.id}")
        delete_logs = [l for l in fake_logger.logs if l["action"] == "delete"]
        assert len(delete_logs) == 1
        assert delete_logs[0]["task_id"] == task.id

    def test_double_delete_returns_404(self, client, fake_repo):
        task = _seed(fake_repo, "Double delete")
        client.delete(f"/tasks/{task.id}")
        res = client.delete(f"/tasks/{task.id}")
        assert res.status_code == 404


class TestHealthCheck:
    def test_health_endpoint(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.get_json()["status"] == "ok"


class TestTaskModel:
    def test_valid_task_creation(self):
        task = Task(title="My task")
        assert task.title == "My task"
        assert task.status == "pending"
        assert task.id is not None

    def test_task_raises_on_empty_title(self):
        with pytest.raises(ValueError):
            Task(title="")

    def test_task_raises_on_invalid_status(self):
        with pytest.raises(ValueError):
            Task(title="Bad status", status="unknown")

    def test_to_dict_contains_all_fields(self):
        task = Task(title="Dict test", description="desc")
        d = task.to_dict()
        for key in ("id", "title", "description", "status", "created_at", "updated_at"):
            assert key in d