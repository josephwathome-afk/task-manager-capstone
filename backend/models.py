import os
import uuid
from datetime import datetime, timezone

# psycopg2 and pymongo are imported lazily inside class constructors.
# This allows the test suite to inject fakes without needing real drivers.

class Task:
    VALID_STATUSES = {"pending", "in_progress", "done"}
    def __init__(
        self,
        title: str,
        description: str = "",
        status: str = "pending",
        task_id: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        if not title or not title.strip():
            raise ValueError("Title must not be empty.")
        if status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of {self.VALID_STATUSES}."
            )

        self.id: str = task_id or str(uuid.uuid4())
        self.title: str = title.strip()
        self.description: str = description.strip()
        self.status: str = status
        self.created_at: datetime = created_at or datetime.now(timezone.utc)
        self.updated_at: datetime = updated_at or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_row(cls, row: dict) -> "Task":
        return cls(
            task_id=str(row["id"]),
            title=row["title"],
            description=row.get("description", ""),
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r} status={self.status}>"


class TaskRepository:
    def __init__(self, database_url: str | None = None):
        import psycopg2 as _psycopg2
        import psycopg2.extras as _extras
        self._psycopg2 = _psycopg2
        self._extras = _extras
        self._dsn: str = database_url or os.environ["DATABASE_URL"]
        self._ensure_schema()

    def _connect(self):
        return self._psycopg2.connect(
            self._dsn, cursor_factory=self._extras.RealDictCursor
        )

    def _ensure_schema(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS tasks (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title       TEXT        NOT NULL,
            description TEXT        NOT NULL DEFAULT '',
            status      TEXT        NOT NULL DEFAULT 'pending',
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
            conn.commit()

    def get_all(self) -> list[Task]:
        sql = "SELECT * FROM tasks ORDER BY created_at DESC;"
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
        return [Task.from_row(r) for r in rows]

    def get_by_id(self, task_id: str) -> Task | None:
        sql = "SELECT * FROM tasks WHERE id = %s;"
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (task_id,))
                row = cur.fetchone()
        return Task.from_row(row) if row else None

    def create(self, title: str, description: str = "") -> Task:
        task = Task(title=title, description=description)
        sql = """
        INSERT INTO tasks (id, title, description, status, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING *;
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        task.id,
                        task.title,
                        task.description,
                        task.status,
                        task.created_at,
                        task.updated_at,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
        return Task.from_row(row)

    def update_status(self, task_id: str, new_status: str) -> Task | None:
        if new_status not in Task.VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{new_status}'. Must be one of {Task.VALID_STATUSES}."
            )
        now = datetime.now(timezone.utc)
        sql = """
        UPDATE tasks
        SET    status = %s, updated_at = %s
        WHERE  id = %s
        RETURNING *;
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (new_status, now, task_id))
                row = cur.fetchone()
            conn.commit()
        return Task.from_row(row) if row else None

    def delete(self, task_id: str) -> bool:
        sql = "DELETE FROM tasks WHERE id = %s RETURNING id;"
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (task_id,))
                deleted = cur.fetchone()
            conn.commit()
        return deleted is not None

class ActivityLogger:

    COLLECTION = "activity_logs"

    def __init__(self, mongo_url: str | None = None, db_name: str | None = None):
        from pymongo import MongoClient as _MongoClient
        url = mongo_url or os.environ["MONGO_URL"]
        db = db_name or os.environ.get("MONGO_DB", "taskdb")
        self._collection = _MongoClient(url)[db][self.COLLECTION]

    def log_create(self, task: Task) -> None:
        self._write(
            action="create",
            task_id=task.id,
            description=f"Task created: '{task.title}'",
        )

    def log_update(self, task: Task, old_status: str) -> None:
        self._write(
            action="update",
            task_id=task.id,
            description=(
                f"Task '{task.title}' status changed: "
                f"'{old_status}' → '{task.status}'"
            ),
        )

    def log_delete(self, task_id: str, title: str) -> None:
        self._write(
            action="delete",
            task_id=task_id,
            description=f"Task deleted: '{title}' (id={task_id})",
        )

    def _write(self, action: str, task_id: str, description: str) -> None:
        self._collection.insert_one(
            {
                "action": action,
                "task_id": task_id,
                "description": description,
                "timestamp": datetime.now(timezone.utc),
            }
        )