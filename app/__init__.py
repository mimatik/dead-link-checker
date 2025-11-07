"""Flask application factory"""

import os

from flask import Flask, request, send_from_directory
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
    # Use absolute path for static folder to work correctly in Docker
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_folder = os.path.join(base_dir, "frontend", "dist")
    # Disable automatic static file serving
    # We'll handle it manually in catch-all route
    app = Flask(__name__, static_folder=None, static_url_path=None)

    # Apply config
    if config:
        app.config.update(config)

    # Enable CORS for development
    if app.config.get("ENV") != "production":
        CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Health check endpoint (no auth required for Railway)
    @app.route("/health")
    def health_check():
        """Health check endpoint for Railway deployment"""
        return {"status": "healthy", "service": "dead-link-crawler"}, 200

    # HTTP Basic Auth for production (excluding health endpoint)
    @app.before_request
    def require_auth():
        """Require authentication in production environment"""
        # Skip auth for health check endpoint
        if request.path == "/health":
            return None

        if os.environ.get("FLASK_ENV") == "production":
            return auth.login_required(lambda: None)()

    # Register API blueprint
    from app.api import api_bp

    app.register_blueprint(api_bp)

    # Store static folder path for manual serving
    app.config["FRONTEND_STATIC_FOLDER"] = static_folder

    # Serve frontend for production - catch-all route must be last
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        """Serve React frontend or fallback to index.html"""
        # Don't serve frontend for API routes - let Flask return 404
        if path.startswith("api/"):
            from flask import abort

            abort(404)

        static_folder_path = app.config["FRONTEND_STATIC_FOLDER"]

        # Check if requested path exists as static file (CSS, JS, images, etc.)
        if path:
            static_path = os.path.join(static_folder_path, path)
            if os.path.exists(static_path) and os.path.isfile(static_path):
                return send_from_directory(static_folder_path, path)

        # Fallback to index.html for SPA routing (React Router handles the rest)
        return send_from_directory(static_folder_path, "index.html")

    return app
