"""Flask API routes for dead link crawler"""

import os

from flask import Blueprint, jsonify, request, send_file

from app.core import config_store, jobs

api_bp = Blueprint("api", __name__, url_prefix="/api")


# Config endpoints
@api_bp.route("/configs", methods=["GET"])
def list_configs():
    """List all configurations"""
    try:
        configs = config_store.list_configs()
        return jsonify(configs), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/configs/<config_id>", methods=["GET"])
def get_config(config_id: str):
    """Get configuration by ID"""
    try:
        config = config_store.get_config(config_id)
        return jsonify(config), 200
    except FileNotFoundError:
        return jsonify({"error": f"Configuration '{config_id}' not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/configs", methods=["POST"])
def create_config():
    """Create new configuration"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        config_id = data.get("id")
        if not config_id:
            return jsonify({"error": "Config 'id' is required"}), 400

        # Remove id from data (will be set by create_config)
        config_data = {k: v for k, v in data.items() if k != "id"}

        config = config_store.create_config(config_id, config_data)
        return jsonify(config), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/configs/<config_id>", methods=["PUT"])
def update_config(config_id: str):
    """Update configuration"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Remove id from data (will be set by update_config)
        config_data = {k: v for k, v in data.items() if k != "id"}

        config = config_store.update_config(config_id, config_data)
        return jsonify(config), 200
    except FileNotFoundError:
        return jsonify({"error": f"Configuration '{config_id}' not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/configs/<config_id>", methods=["DELETE"])
def delete_config(config_id: str):
    """Delete configuration"""
    try:
        config_store.delete_config(config_id)
        return jsonify({"message": f"Configuration '{config_id}' deleted"}), 200
    except FileNotFoundError:
        return jsonify({"error": f"Configuration '{config_id}' not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Crawl endpoints
@api_bp.route("/crawl", methods=["POST"])
def start_crawl():
    """Start a new crawl job"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        config_id = data.get("configId")
        config_inline = data.get("config")

        # Use either stored config or inline config
        if config_id:
            config = config_store.get_config(config_id)
        elif config_inline:
            config = config_inline
        else:
            return jsonify({"error": "Either 'configId' or 'config' is required"}), 400

        # Validate config has start_url
        if not config.get("start_url"):
            return jsonify({"error": "Configuration must have 'start_url'"}), 400

        # Create and start job
        job_id = jobs.create_job(config, config_id)
        jobs.start_job(job_id)

        return jsonify({"jobId": job_id}), 201
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Job endpoints
@api_bp.route("/jobs", methods=["GET"])
def list_jobs():
    """List recent jobs"""
    try:
        limit = request.args.get("limit", 50, type=int)
        job_list = jobs.list_jobs(limit)
        return jsonify(job_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/jobs/<job_id>", methods=["GET"])
def get_job(job_id: str):
    """Get job status and details"""
    try:
        job = jobs.get_job(job_id)

        if not job:
            return jsonify({"error": f"Job '{job_id}' not found"}), 404

        return jsonify(job), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/jobs/<job_id>/cancel", methods=["POST"])
def cancel_job(job_id: str):
    """Cancel a running or queued job"""
    try:
        jobs.cancel_job(job_id)
        return jsonify({"message": f"Job '{job_id}' cancelled"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Report endpoints
@api_bp.route("/reports", methods=["GET"])
def list_reports():
    """List available reports"""
    try:
        reports_dir = "reports"

        if not os.path.exists(reports_dir):
            return jsonify([]), 200

        reports = []
        for filename in os.listdir(reports_dir):
            if filename.endswith(".csv"):
                filepath = os.path.join(reports_dir, filename)
                stat = os.stat(filepath)
                reports.append(
                    {
                        "filename": filename,
                        "size": stat.st_size,
                        "created_at": stat.st_ctime,
                    }
                )

        # Sort by creation time descending
        reports.sort(key=lambda x: x["created_at"], reverse=True)

        return jsonify(reports), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/reports/<filename>", methods=["GET"])
def download_report(filename: str):
    """Download a report file"""
    try:
        reports_dir = "reports"
        filepath = os.path.join(reports_dir, filename)

        # Security: prevent directory traversal
        if not os.path.abspath(filepath).startswith(os.path.abspath(reports_dir)):
            return jsonify({"error": "Invalid filename"}), 400

        if not os.path.exists(filepath):
            return jsonify({"error": f"Report '{filename}' not found"}), 404

        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
