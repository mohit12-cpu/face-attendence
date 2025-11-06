import os

# Database configuration
DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')  # Options: 'sqlite', 'mysql', 'postgresql'
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_NAME = os.environ.get('DB_NAME', 'attendance_db')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')

# For SQLite (default)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "attendance.db")
KNOWN_FACES_DIR = os.path.join(SCRIPT_DIR, "known_faces")