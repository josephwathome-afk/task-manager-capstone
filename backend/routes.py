"""
Endpoints:
  GET    /tasks          → list all tasks            (200)
  POST   /tasks          → create a task             (201 | 400)
  PATCH  /tasks/<id>     → update task status        (200 | 404)
  DELETE /tasks/<id>     → delete a task             (200 | 404)
"""

from flask import Blueprint, jsonify, request, current_app

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


def _repo():
    return current_app.config["TASK_REPO"]


def _logger():
    return current_app.config["ACTIVITY_LOGGER"]

@tasks_bp.get("/")
def list_tasks():
    tasks = _repo().get_all()
    return jsonify([t.to_dict() for t in tasks]), 200


@tasks_bp.post("/")
def create_task():
    body = request.get_json(silent=True) or {}

    title = body.get("title", "").strip()
    if not title:
        return jsonify({"error": "Field 'title' is required and must not be blank."}), 400

    description = body.get("description", "")

    task = _repo().create(title=title, description=description)
    _logger().log_create(task)

    return jsonify(task.to_dict()), 201

@tasks_bp.patch("/<task_id>")
def update_task_status(task_id: str):
    body = request.get_json(silent=True) or {}
    new_status = body.get("status", "").strip()

    if not new_status:
        return jsonify({"error": "Field 'status' is required."}), 400

    existing = _repo().get_by_id(task_id)
    if existing is None:
        return jsonify({"error": f"Task '{task_id}' not found."}), 404

    old_status = existing.status

    try:
        updated = _repo().update_status(task_id, new_status)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if updated is None:
        # Guard against a race-condition delete between the two calls
        return jsonify({"error": f"Task '{task_id}' not found."}), 404

    _logger().log_update(updated, old_status)

    return jsonify(updated.to_dict()), 200


@tasks_bp.delete("/<task_id>")
def delete_task(task_id: str):
    # Fetch title before deletion so we can log it meaningfully
    existing = _repo().get_by_id(task_id)
    if existing is None:
        return jsonify({"error": f"Task '{task_id}' not found."}), 404

    deleted = _repo().delete(task_id)
    if not deleted:
        return jsonify({"error": f"Task '{task_id}' not found."}), 404

    _logger().log_delete(task_id, existing.title)

    return jsonify({"message": f"Task '{task_id}' deleted successfully."}), 200