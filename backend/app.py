import os
from flask import Flask, jsonify
from models import TaskRepository, ActivityLogger
from routes import tasks_bp
from flask_cors import CORS

def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes (for frontend integration) # but in production should be limmited to specific routes and origins.

    app.config["DATABASE_URL"] = os.environ.get("DATABASE_URL", "")
    app.config["MONGO_URL"] = os.environ.get("MONGO_URL", "")
    app.config["MONGO_DB"] = os.environ.get("MONGO_DB", "taskdb")

    if config:
        app.config.update(config)

    if "TASK_REPO" not in app.config:
        app.config["TASK_REPO"] = TaskRepository(
            database_url=app.config["DATABASE_URL"]
        )
    if "ACTIVITY_LOGGER" not in app.config:
        app.config["ACTIVITY_LOGGER"] = ActivityLogger(
            mongo_url=app.config["MONGO_URL"],
            db_name=app.config["MONGO_DB"],
        )

    app.register_blueprint(tasks_bp)

    @app.errorhandler(404)
    def not_found(exc):
        return jsonify({"error": "Resource not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(exc):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(500)
    def internal_error(exc):
        app.logger.exception("Unhandled exception: %s", exc)
        return jsonify({"error": "Internal server error."}), 500

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true",
    )