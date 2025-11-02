"""Flask application factory"""

import os

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash

# HTTP Basic Authentication setup
auth = HTTPBasicAuth()

# Users dictionary with hashed passwords
users = {
    os.environ.get("AUTH_USERNAME", "preview"): generate_password_hash(
        os.environ.get("AUTH_PASSWORD", "pl34s3")
    )
}


@auth.verify_password
def verify_password(username, password):
    """Verify username and password"""
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None


def create_app(config=None):
    """Create and configure Flask application"""
    app = Flask(__name__, static_folder="../frontend/dist", static_url_path="")

    # Apply config
    if config:
        app.config.update(config)

    # Enable CORS for development
    if app.config.get("ENV") != "production":
        CORS(app, resources={r"/api/*": {"origins": "*"}})

    # HTTP Basic Auth for production
    @app.before_request
    def require_auth():
        """Require authentication in production environment"""
        if os.environ.get("FLASK_ENV") == "production":
            return auth.login_required(lambda: None)()

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
