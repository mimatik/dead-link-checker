"""Gunicorn configuration for production deployment"""

import os

# Bind to PORT from environment (Railway sets this automatically)
bind = f"0.0.0.0:{os.environ.get('PORT', '5555')}"

# Worker processes
workers = 2
worker_class = "sync"

# Timeout settings
timeout = 120
keepalive = 5

# Logging
errorlog = "-"  # Log to stdout
accesslog = "-"  # Log to stdout
loglevel = "info"

# Preload application before forking workers
preload_app = True
