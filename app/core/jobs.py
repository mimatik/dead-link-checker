"""Job management - tracking crawl jobs and their status"""

import json
import os
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from app.core import crawler

JOBS_FILE = ".data/jobs.json"
jobs_lock = threading.Lock()
active_jobs: Dict[str, Dict] = {}


def _ensure_data_dir():
    """Ensure data directory exists"""
    os.makedirs(".data", exist_ok=True)


def _load_jobs() -> Dict:
    """Load jobs from persistent storage"""
    _ensure_data_dir()

    if not os.path.exists(JOBS_FILE):
        return {}

    try:
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_jobs(jobs: Dict):
    """Save jobs to persistent storage"""
    _ensure_data_dir()

    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)


def create_job(config: Dict, config_id: Optional[str] = None) -> str:
    """
    Create a new crawl job

    Args:
        config: Configuration dictionary
        config_id: Optional config ID if using stored config

    Returns:
        Job ID
    """
    job_id = str(uuid.uuid4())

    with jobs_lock:
        jobs = _load_jobs()

        job = {
            "id": job_id,
            "status": "queued",
            "config": config,
            "config_id": config_id,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "report_path": None,
            "error": None,
            "stats": {
                "pages_crawled": 0,
                "links_checked": 0,
                "errors_found": 0,
            },
        }

        jobs[job_id] = job
        active_jobs[job_id] = job
        _save_jobs(jobs)

    return job_id


def get_job(job_id: str) -> Optional[Dict]:
    """
    Get job by ID

    Args:
        job_id: Job identifier

    Returns:
        Job dictionary or None if not found
    """
    with jobs_lock:
        # Check active jobs first
        if job_id in active_jobs:
            return active_jobs[job_id].copy()

        # Check persistent storage
        jobs = _load_jobs()
        return jobs.get(job_id)


def list_jobs(limit: int = 50) -> List[Dict]:
    """
    List recent jobs

    Args:
        limit: Maximum number of jobs to return

    Returns:
        List of job dictionaries
    """
    with jobs_lock:
        jobs = _load_jobs()

        # Sort by created_at descending
        sorted_jobs = sorted(
            jobs.values(), key=lambda x: x.get("created_at", ""), reverse=True
        )

        return sorted_jobs[:limit]


def update_job(job_id: str, updates: Dict):
    """
    Update job status and data

    Args:
        job_id: Job identifier
        updates: Dictionary of fields to update
    """
    with jobs_lock:
        jobs = _load_jobs()

        if job_id not in jobs:
            raise ValueError(f"Job '{job_id}' not found")

        jobs[job_id].update(updates)

        if job_id in active_jobs:
            active_jobs[job_id].update(updates)

        _save_jobs(jobs)


def _run_job_thread(job_id: str):
    """Run crawl job in background thread"""
    try:
        # Update status to running
        update_job(
            job_id,
            {
                "status": "running",
                "started_at": datetime.now().isoformat(),
            },
        )

        # Get job config
        job = get_job(job_id)
        if not job:
            return

        config = job["config"]

        # Progress callback to update job stats in real-time
        def progress_callback(event_type: str, data: dict):
            job = get_job(job_id)
            if job and job.get("status") == "cancelled":
                # Stop crawl if job was cancelled
                raise Exception("Job cancelled by user")

            if event_type in ["page_crawled", "link_checked", "complete"]:
                update_job(
                    job_id,
                    {
                        "stats": {
                            "pages_crawled": data.get("pages_crawled", 0),
                            "links_checked": data.get("links_checked", 0),
                            "errors_found": data.get("errors_found", 0),
                        }
                    },
                )

        # Run crawl
        result = crawler.run_crawl(config, progress_callback)

        # Update job as completed
        update_job(
            job_id,
            {
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "report_path": result.get("report_path"),
                "stats": {
                    "pages_crawled": result.get("pages_crawled", 0),
                    "links_checked": result.get("links_checked", 0),
                    "errors_found": result.get("errors_found", 0),
                },
            },
        )

    except Exception as e:
        # Update job as failed
        update_job(
            job_id,
            {
                "status": "failed",
                "completed_at": datetime.now().isoformat(),
                "error": str(e),
            },
        )

    finally:
        # Remove from active jobs
        with jobs_lock:
            if job_id in active_jobs:
                del active_jobs[job_id]


def start_job(job_id: str):
    """
    Start executing a queued job

    Args:
        job_id: Job identifier
    """
    job = get_job(job_id)

    if not job:
        raise ValueError(f"Job '{job_id}' not found")

    if job["status"] != "queued":
        raise ValueError(f"Job '{job_id}' is not in queued state")

    # Start job in background thread
    thread = threading.Thread(target=_run_job_thread, args=(job_id,), daemon=True)
    thread.start()


def cancel_job(job_id: str):
    """
    Cancel a running or queued job

    Args:
        job_id: Job identifier
    """
    job = get_job(job_id)

    if not job:
        raise ValueError(f"Job '{job_id}' not found")

    if job["status"] not in ["queued", "running"]:
        raise ValueError(
            f"Job '{job_id}' cannot be cancelled (status: {job['status']})"
        )

    # Update status to cancelled
    update_job(
        job_id,
        {
            "status": "cancelled",
            "completed_at": datetime.now().isoformat(),
        },
    )

    # Remove from active jobs
    with jobs_lock:
        if job_id in active_jobs:
            del active_jobs[job_id]
