
import sqlite3
import os
from datetime import datetime
import random

# Get the absolute path to the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define absolute paths for the database and faces directory
DB_FILE = os.path.join(SCRIPT_DIR, "attendance.db")
KNOWN_FACES_DIR = os.path.join(SCRIPT_DIR, "known_faces")

def get_db_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Create the necessary tables if they don't already exist."""
    conn = get_db_connection()
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                faculty TEXT,
                dob TEXT,
                email TEXT,
                address TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Insert default admin if not exists
        conn.execute('''
            INSERT OR IGNORE INTO admins (id, password) VALUES ('admin1', 'admin1')
        ''')
    conn.close()

def get_all_students():
    """Retrieve all students from the database."""
    conn = get_db_connection()
    students = conn.execute("SELECT * FROM students ORDER BY name").fetchall()
    conn.close()
    return [dict(row) for row in students]

def get_student_by_id(student_id):
    """Retrieve a single student by their ID."""
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    conn.close()
    return dict(student) if student else None

def get_attendance():
    """Retrieve all attendance records, joining with student names."""
    conn = get_db_connection()
    attendance = conn.execute('''
        SELECT a.id, s.id as student_id, s.name, a.date, a.time
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        ORDER BY a.date DESC, a.time DESC
    ''').fetchall()
    conn.close()
    return [dict(row) for row in attendance]

def get_student_attendance(student_id):
    """Retrieve attendance records for a specific student."""
    conn = get_db_connection()
    attendance = conn.execute('''
        SELECT a.id, s.id as student_id, s.name, a.date, a.time
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE s.id = ?
        ORDER BY a.date DESC, a.time DESC
    ''', (student_id,)).fetchall()
    conn.close()
    return [dict(row) for row in attendance]

def add_student(student_id, name, faculty, dob, email, address):
    """Add or update a student in the database."""
    conn = get_db_connection()
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO students (id, name, faculty, dob, email, address) VALUES (?, ?, ?, ?, ?, ?)",
            (student_id, name, faculty, dob, email, address)
        )
    conn.close()

def delete_student_by_id(student_id):
    """Delete a student and their corresponding face image."""
    conn = get_db_connection()
    with conn:
        conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.close()
    
    img_path = os.path.join(KNOWN_FACES_DIR, f"{student_id}.jpg")
    if os.path.exists(img_path):
        os.remove(img_path)
    return True

def mark_attendance_db(student_id):
    """Append attendance if not marked within the last 12 hours."""
    conn = get_db_connection()
    now = datetime.now()
    date, time = now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")

    last_entry = conn.execute(
        "SELECT date, time FROM attendance WHERE student_id = ? ORDER BY date DESC, time DESC LIMIT 1",
        (student_id,)
    ).fetchone()

    if last_entry:
        last_dt = datetime.strptime(f"{last_entry['date']} {last_entry['time']}", "%Y-%m-%d %H:%M:%S")
        if (now - last_dt).total_seconds() < 43200:  # 12 hours
            conn.close()
            return None

    with conn:
        conn.execute(
            "INSERT INTO attendance (student_id, date, time) VALUES (?, ?, ?)",
            (student_id, date, time)
        )
    conn.close()
    student_name = get_student_by_id(student_id)['name']
    return {'student_id': student_id, 'name': student_name, 'date': date, 'time': time}

def add_attendance_record(student_id, date, time):
    """Add a single attendance record to the database (for migration)."""
    conn = get_db_connection()
    with conn:
        conn.execute(
            "INSERT INTO attendance (student_id, date, time) VALUES (?, ?, ?)",
            (student_id, date, time)
        )
    conn.close()

def delete_attendance_by_id(attendance_id):
    """Delete an attendance record by its primary key."""
    conn = get_db_connection()
    with conn:
        conn.execute("DELETE FROM attendance WHERE id = ?", (attendance_id,))
    conn.close()
    return True

def get_next_student_id():
    """Generate a new, unique student ID."""
    conn = get_db_connection()
    existing_ids = {row['id'] for row in conn.execute("SELECT id FROM students").fetchall()}
    conn.close()
    
    for _ in range(10000):
        random_part = str(random.randint(10000, 99999))
        sid = '817' + random_part
        if sid not in existing_ids:
            return sid
    raise RuntimeError("Unable to generate a unique student ID.")

def verify_admin(admin_id, password):
    """Verify admin credentials."""
    conn = get_db_connection()
    admin = conn.execute("SELECT * FROM admins WHERE id = ? AND password = ?", (admin_id, password)).fetchone()
    conn.close()
    return admin is not None

def update_student(student_id, name, faculty, dob, email, address):
    """Update an existing student's information."""
    conn = get_db_connection()
    with conn:
        conn.execute(
            "UPDATE students SET name = ?, faculty = ?, dob = ?, email = ?, address = ? WHERE id = ?",
            (name, faculty, dob, email, address, student_id)
        )
    conn.close()

# Initialize the database and tables
create_tables()
