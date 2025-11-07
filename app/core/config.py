"""Application configuration and global settings"""

import os

# Project root directory (3 levels up from this file: app/core/config.py)
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# Detect Railway environment
IS_RAILWAY = os.environ.get("RAILWAY_ENVIRONMENT") is not None

if IS_RAILWAY:
    # Use Railway volume mount
    VOLUME_PATH = "/data"
    CONFIG_DIR = os.path.join(VOLUME_PATH, "custom_config_json")
    REPORTS_DIR = os.path.join(VOLUME_PATH, "reports")
    DATA_DIR = os.path.join(VOLUME_PATH, ".data")
else:
    # Local development paths
    CONFIG_DIR = os.path.join(PROJECT_ROOT, "custom_config_json")
    REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
    DATA_DIR = os.path.join(PROJECT_ROOT, ".data")

# Files
JOBS_FILE = os.path.join(DATA_DIR, "jobs.json")

# Job management settings
MAX_JOBS_TO_KEEP = int(os.environ.get("MAX_JOBS_TO_KEEP", "10"))

# Ensure directories exist
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
