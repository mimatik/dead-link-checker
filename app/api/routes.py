"""Flask API routes for dead link crawler"""

import csv
import os
from typing import Optional
from urllib.parse import urlparse

from flask import Blueprint, jsonify, request, send_file

from app.core import config_store, jobs
from app.core.config import REPORTS_DIR

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
        if not os.path.exists(REPORTS_DIR):
            return jsonify([]), 200

        reports = []
        for filename in os.listdir(REPORTS_DIR):
            if filename.endswith(".csv"):
                filepath = os.path.join(REPORTS_DIR, filename)
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
        filepath = os.path.join(REPORTS_DIR, filename)

        # Security: prevent directory traversal
        if not os.path.abspath(filepath).startswith(os.path.abspath(REPORTS_DIR)):
            return jsonify({"error": "Invalid filename"}), 400

        if not os.path.exists(filepath):
            return jsonify({"error": f"Report '{filename}' not found"}), 404

        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/reports/<filename>", methods=["DELETE"])
def delete_report(filename: str):
    """Delete a report file and update jobs.json"""
    try:
        filepath = os.path.join(REPORTS_DIR, filename)

        # Security: prevent directory traversal
        if not os.path.abspath(filepath).startswith(os.path.abspath(REPORTS_DIR)):
            return jsonify({"error": "Invalid filename"}), 400

        if not os.path.exists(filepath):
            return jsonify({"error": f"Report '{filename}' not found"}), 404

        # Delete the file
        os.remove(filepath)

        # Update jobs.json - remove report_path from jobs that reference this file
        all_jobs = jobs.list_jobs(limit=10000)  # Get all jobs
        updated = False
        for job in all_jobs:
            if job.get("report_path") == filename:
                jobs.update_job(job["id"], {"report_path": None})
                updated = True

        message = f"Report '{filename}' deleted"
        if updated:
            message += " and updated in jobs"

        return jsonify({"message": message}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/reports/<filename>/data", methods=["GET"])
def get_report_data(filename: str):
    """Get report data as JSON"""
    try:
        filepath = os.path.join(REPORTS_DIR, filename)

        # Security: prevent directory traversal
        if not os.path.abspath(filepath).startswith(os.path.abspath(REPORTS_DIR)):
            return jsonify({"error": "Invalid filename"}), 400

        if not os.path.exists(filepath):
            return jsonify({"error": f"Report '{filename}' not found"}), 404

        # Try to find config_id for this report
        config_id = _find_config_id_by_report(filename)

        # Read CSV and convert to JSON
        entries = []
        with open(filepath, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                entries.append(
                    {
                        "error_type": row.get("error_type", ""),
                        "link_url": row.get("link_url", ""),
                        "link_text": row.get("link_text", ""),
                        "source_page": row.get("source_page", ""),
                        "resolved": False,  # Will be updated when marking as resolved
                    }
                )

        # Calculate stats
        total_entries = len(entries)
        error_types = {}
        for entry in entries:
            error_type = entry["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1

        return jsonify(
            {
                "filename": filename,
                "entries": entries,
                "config_id": config_id,  # Include config_id if found
                "stats": {
                    "total": total_entries,
                    "resolved": 0,  # Will be tracked separately
                    "error_types": error_types,
                },
            }
        ), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _extract_status_code(error_type: str) -> Optional[int]:
    """Extract HTTP status code from error_type string"""
    if error_type and error_type.startswith("HTTP "):
        try:
            return int(error_type.split()[1])
        except (ValueError, IndexError):
            pass
    return None


def _is_error_type_without_code(error_type: str) -> bool:
    """Check if error_type is Timeout or Connection Error (no status code)"""
    error_lower = error_type.lower()
    return "timeout" in error_lower or "connection error" in error_lower


def _find_config_id_by_report(filename: str) -> Optional[str]:
    """Find config_id by searching jobs for matching report filename"""
    all_jobs = jobs.list_jobs(limit=1000)

    # Normalize filename by removing _incomplete suffix for comparison
    def normalize_filename(fn: str) -> str:
        """Remove _incomplete suffix if present"""
        if fn and fn.endswith("_incomplete.csv"):
            return fn.replace("_incomplete.csv", ".csv")
        return fn

    normalized_filename = normalize_filename(filename)

    for job in all_jobs:
        job_report_path = job.get("report_path")
        if job_report_path:
            # Compare normalized filenames (with or without _incomplete)
            normalized_job_path = normalize_filename(job_report_path)
            if normalized_job_path == normalized_filename:
                config_id = job.get("config_id")
                if config_id:
                    return config_id
    return None


def _find_config_id_by_domain(domain: str) -> Optional[str]:
    """Find config_id by matching domain with config start_url"""
    all_configs = config_store.list_configs()
    for config in all_configs:
        config_start_url = config.get("start_url", "")
        config_domain = urlparse(config_start_url).netloc.replace("www.", "")
        if config_domain == domain:
            return config.get("id")
    return None


@api_bp.route("/reports/<filename>/mark-resolved", methods=["POST"])
def mark_link_resolved(filename: str):
    """Mark a link as resolved and add domain rule to config"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        link_url = data.get("link_url")
        error_type = data.get("error_type")
        config_id = data.get("config_id")

        if not link_url:
            return jsonify({"error": "link_url is required"}), 400

        # Extract domain from link_url
        parsed_url = urlparse(link_url)
        domain = parsed_url.netloc.replace("www.", "")

        if not domain:
            return jsonify({"error": "Invalid URL"}), 400

        # Extract HTTP status code from error_type
        status_code = _extract_status_code(error_type)
        is_timeout_or_connection = _is_error_type_without_code(error_type)

        # For Timeout and Connection Error, set ignore_timeouts flag
        if not status_code and not is_timeout_or_connection:
            error_msg = (
                "Could not extract status code from error_type. "
                "Only HTTP errors, Timeout, and Connection Error are supported."
            )
            return jsonify({"error": error_msg}), 400

        # Find config_id if not provided
        if not config_id:
            config_id = _find_config_id_by_report(filename)
        if not config_id:
            config_id = _find_config_id_by_domain(domain)

        if not config_id:
            error_msg = (
                "Could not determine config_id. Please provide config_id in request."
            )
            return jsonify({"error": error_msg}), 400

        # Get config
        try:
            config = config_store.get_config(config_id)
        except FileNotFoundError:
            return jsonify({"error": f"Configuration '{config_id}' not found"}), 404

        # Add or update domain rule
        if "domain_rules" not in config:
            config["domain_rules"] = {}

        if domain not in config["domain_rules"]:
            config["domain_rules"][domain] = {
                "allowed_codes": [],
                "description": f"Manually resolved links for {domain}",
                "ignore_timeouts": False,
            }

        # Handle Timeout/Connection Error - set ignore_timeouts flag
        if is_timeout_or_connection:
            config["domain_rules"][domain]["ignore_timeouts"] = True
            message = (
                f"Link marked as resolved. "
                f"Added rule for {domain} to ignore timeouts and connection errors."
            )
        else:
            # Add status code to allowed_codes if not already present
            if status_code not in config["domain_rules"][domain]["allowed_codes"]:
                config["domain_rules"][domain]["allowed_codes"].append(status_code)
                config["domain_rules"][domain]["allowed_codes"].sort()
            message = (
                f"Link marked as resolved. "
                f"Added rule for {domain} with allowed code {status_code}."
            )

        # Update config
        config_store.update_config(config_id, config)

        return jsonify(
            {
                "message": message,
                "config_id": config_id,
                "domain": domain,
                "status_code": status_code,
                "ignore_timeouts": is_timeout_or_connection,
            }
        ), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/reports/<filename>/remove-rule", methods=["POST"])
def remove_domain_rule(filename: str):
    """Remove a specific domain rule (status code or ignore_timeouts) from config"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        link_url = data.get("link_url")
        error_type = data.get("error_type")
        config_id = data.get("config_id")

        if not link_url:
            return jsonify({"error": "link_url is required"}), 400

        # Extract domain from link_url
        parsed_url = urlparse(link_url)
        domain = parsed_url.netloc.replace("www.", "")

        if not domain:
            return jsonify({"error": "Invalid URL"}), 400

        # Extract HTTP status code from error_type
        status_code = _extract_status_code(error_type)
        is_timeout_or_connection = _is_error_type_without_code(error_type)

        # Find config_id if not provided
        if not config_id:
            config_id = _find_config_id_by_report(filename)
        if not config_id:
            config_id = _find_config_id_by_domain(domain)

        if not config_id:
            error_msg = (
                "Could not determine config_id. Please provide config_id in request."
            )
            return jsonify({"error": error_msg}), 400

        # Get config
        try:
            config = config_store.get_config(config_id)
        except FileNotFoundError:
            return jsonify({"error": f"Configuration '{config_id}' not found"}), 404

        # Check if domain_rules exist
        if "domain_rules" not in config or domain not in config["domain_rules"]:
            return jsonify({"error": f"No rule found for domain '{domain}'"}), 404

        domain_rule = config["domain_rules"][domain]

        # Handle Timeout/Connection Error - remove ignore_timeouts flag
        if is_timeout_or_connection:
            if domain_rule.get("ignore_timeouts", False):
                domain_rule["ignore_timeouts"] = False
                message = f"Removed ignore_timeouts rule for {domain}."
            else:
                error_msg = f"No ignore_timeouts rule found for domain '{domain}'"
                return jsonify({"error": error_msg}), 404
        elif status_code:
            # Remove specific status code from allowed_codes
            if (
                "allowed_codes" in domain_rule
                and status_code in domain_rule["allowed_codes"]
            ):
                domain_rule["allowed_codes"].remove(status_code)
                message = f"Removed allowed code {status_code} for domain {domain}."
            else:
                error_msg = (
                    f"Status code {status_code} not found in rules "
                    f"for domain '{domain}'"
                )
                return jsonify({"error": error_msg}), 404
        else:
            error_msg = "Could not determine what to remove from error_type"
            return jsonify({"error": error_msg}), 400

        # If domain_rule is now empty, remove it
        if not domain_rule.get("allowed_codes", []) and not domain_rule.get(
            "ignore_timeouts", False
        ):
            del config["domain_rules"][domain]
            message += f" Domain rule for {domain} removed completely."

        # Update config
        config_store.update_config(config_id, config)

        return jsonify(
            {
                "message": message,
                "config_id": config_id,
                "domain": domain,
                "status_code": status_code if status_code else None,
                "ignore_timeouts": is_timeout_or_connection,
            }
        ), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
