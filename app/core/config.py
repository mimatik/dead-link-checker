"""Application configuration and global settings"""

import os

# Project root directory (3 levels up from this file: app/core/config.py)
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# Directories
CONFIG_DIR = os.path.join(PROJECT_ROOT, "custom_config_json")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
DATA_DIR = os.path.join(PROJECT_ROOT, ".data")

# Files
JOBS_FILE = os.path.join(DATA_DIR, "jobs.json")

# Ensure directories exist
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
