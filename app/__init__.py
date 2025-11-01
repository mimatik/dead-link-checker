"""Flask application factory"""

import os

from flask import Flask, send_from_directory
from flask_cors import CORS


def create_app(config=None):
    """Create and configure Flask application"""
    app = Flask(__name__, static_folder="../frontend/dist", static_url_path="")

    # Apply config
    if config:
        app.config.update(config)

    # Enable CORS for development
    if app.config.get("ENV") != "production":
        CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register API blueprint
    from app.api import api_bp

    app.register_blueprint(api_bp)

    # Serve frontend for production
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        """Serve React frontend or fallback to index.html"""
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, "index.html")

    return app
