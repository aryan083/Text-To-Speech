import multiprocessing
import os

# Gunicorn configuration
bind = "0.0.0.0:" + os.getenv("PORT", "5000")
workers = multiprocessing.cpu_count() * 2 + 1
threads = 2
worker_class = "gthread"
timeout = 120
keepalive = 5
max_requests = 120
max_requests_jitter = 10

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# SSL (if needed)
# keyfile = "path/to/keyfile"
# certfile = "path/to/certfile"

# Server Mechanics
preload_app = True
reload = False  # Disable auto-reload in production

# Process Naming
proc_name = "text-to-speech-app"

# Server Hooks
def on_starting(server):
    server.log.info("Starting Text-to-Speech Application")

def on_exit(server):
    server.log.info("Shutting down Text-to-Speech Application")