from waitress import serve
from app import app
import os
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_app():
    """
    Runs the Flask application using the Waitress production server,
    configured via environment variables.
    """
    # Use environment variables for configuration with sensible defaults
    host = os.environ.get('APP_HOST', '0.0.0.0')
    port = int(os.environ.get('APP_PORT', 8080))
    threads = int(os.environ.get('APP_THREADS', 8))

    logging.info("--- Starting CognAttendance Production Server ---")
    logging.info(f"Host: {host}")
    logging.info(f"Port: {port}")
    logging.info(f"Worker Threads: {threads}")
    logging.info("Access the application at http://127.0.0.1:%s or your local IP.", port)
    logging.info("Press Ctrl+C to stop the server.")
    serve(app, host=host, port=port, threads=threads)

if __name__ == "__main__":
    run_app()