import os
from datetime import datetime
import random

# Load environment variables from .env file
try:
    from load_env import load_env_file
    load_env_file()
except ImportError:
    pass  # load_env module not available, continue with system environment variables

# Conditional imports for database drivers
MYSQL_AVAILABLE = False
POSTGRESQL_AVAILABLE = False

try:
    import mysql.connector  # type: ignore
    MYSQL_AVAILABLE = True
except ImportError:
    mysql = None
    MYSQL_AVAILABLE = False

try:
    import psycopg2
    POSTGRESQL_AVAILABLE = True
except ImportError:
    psycopg2 = None
    POSTGRESQL_AVAILABLE = False

# Database configuration from environment variables
DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')  # 'mysql', 'postgresql', or 'sqlite'
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_NAME = os.environ.get('DB_NAME', 'attendance_db')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')

# Print debug information
print(f"DB_TYPE: {DB_TYPE}")
print(f"DB_HOST: {DB_HOST}")
print(f"DB_PORT: {DB_PORT}")
print(f"DB_NAME: {DB_NAME}")
print(f"DB_USER: {DB_USER}")

# SQLite fallback (existing functionality)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "attendance.db")
KNOWN_FACES_DIR = os.path.join(SCRIPT_DIR, "known_faces")

def get_db_connection():
    """Establish a connection to the configured database."""
    if DB_TYPE == 'mysql':
        if not MYSQL_AVAILABLE:
            raise ImportError("MySQL driver not available. Please install mysql-connector-python")
        import mysql.connector  # type: ignore
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return connection
    elif DB_TYPE == 'postgresql':
        if not POSTGRESQL_AVAILABLE:
            raise ImportError("PostgreSQL driver not available. Please install psycopg2-binary")
        import psycopg2
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return connection
    else:  # sqlite (default)
        import sqlite3
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn

def create_tables():
    """Create the necessary tables if they don't already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DB_TYPE == 'mysql':
        # MySQL table creation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                faculty TEXT,
                dob DATE,
                email VARCHAR(255),
                address TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(255) NOT NULL,
                date DATE NOT NULL,
                time TIME NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id VARCHAR(255) PRIMARY KEY,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Insert default admin if not exists
        cursor.execute('''
            INSERT IGNORE INTO admins (id, password) VALUES ('admin1', 'admin1')
        ''')
    elif DB_TYPE == 'postgresql':
        # PostgreSQL table creation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                faculty TEXT,
                dob DATE,
                email VARCHAR(255),
                address TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                student_id VARCHAR(255) NOT NULL,
                date DATE NOT NULL,
                time TIME NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id VARCHAR(255) PRIMARY KEY,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Insert default admin if not exists (PostgreSQL)
        cursor.execute('''
            INSERT INTO admins (id, password) 
            VALUES ('admin1', 'admin1')
            ON CONFLICT (id) DO NOTHING
        ''')
    else:  # sqlite
        # SQLite table creation (existing functionality)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                faculty TEXT,
                dob TEXT,
                email TEXT,
                address TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Insert default admin if not exists
        cursor.execute('''
            INSERT OR IGNORE INTO admins (id, password) VALUES ('admin1', 'admin1')
        ''')
    
    conn.commit()
    conn.close()

def get_all_students():
    """Retrieve all students from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM students ORDER BY name")
    rows = cursor.fetchall()
    
    # Handle different row types based on database
    if cursor.description:
        columns = [desc[0] for desc in cursor.description]
        result = []
        for row in rows:
            # Convert row to dictionary using column indices
            row_dict = {}
            for i, column in enumerate(columns):
                # Safely access row elements
                try:
                    value = row[i]
                    row_dict[column] = value
                except (IndexError, TypeError):
                    row_dict[column] = None
            result.append(row_dict)
    else:
        result = []
    
    conn.close()
    return result

def get_student_by_id(student_id):
    """Retrieve a single student by their ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DB_TYPE in ['mysql', 'postgresql']:
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
    else:  # sqlite
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    row = cursor.fetchone()
    
    if row:
        # Build dictionary from row data using column names
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            result = {}
            for i, column in enumerate(columns):
                result[column] = row[i]
        else:
            result = None
    else:
        result = None
    
    conn.close()
    return result

def get_attendance():
    """Retrieve all attendance records, joining with student names."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DB_TYPE in ['mysql', 'postgresql']:
        cursor.execute('''
            SELECT a.id, s.id as student_id, s.name, a.date, a.time
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            ORDER BY a.date DESC, a.time DESC
        ''')
    else:  # sqlite
        cursor.execute('''
            SELECT a.id, s.id as student_id, s.name, a.date, a.time
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            ORDER BY a.date DESC, a.time DESC
        ''')
    
    # Handle different row types based on database
    rows = cursor.fetchall()
    if cursor.description:
        columns = [desc[0] for desc in cursor.description]
        result = []
        for row in rows:
            # Convert row to dictionary using column indices
            row_dict = {}
            for i, column in enumerate(columns):
                # Safely access row elements
                try:
                    value = row[i]
                    row_dict[column] = value
                except (IndexError, TypeError):
                    row_dict[column] = None
            result.append(row_dict)
    else:
        result = []
    
    conn.close()
    return result

def get_student_attendance(student_id):
    """Retrieve attendance records for a specific student."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First check if student exists
        if DB_TYPE in ['mysql', 'postgresql']:
            cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        else:  # sqlite
            cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        student_row = cursor.fetchone()
        
        if not student_row:
            conn.close()
            return []
        
        if DB_TYPE in ['mysql', 'postgresql']:
            cursor.execute('''
                SELECT a.id, s.id as student_id, s.name, a.date, a.time
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE s.id = %s
                ORDER BY a.date DESC, a.time DESC
            ''', (student_id,))
        else:  # sqlite
            cursor.execute('''
                SELECT a.id, s.id as student_id, s.name, a.date, a.time
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE s.id = ?
                ORDER BY a.date DESC, a.time DESC
            ''', (student_id,))
        
        # Handle different row types based on database
        rows = cursor.fetchall()
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            result = []
            for row in rows:
                # Convert row to dictionary using column indices
                row_dict = {}
                for i, column in enumerate(columns):
                    # Safely access row elements
                    try:
                        value = row[i]
                        row_dict[column] = value
                    except (IndexError, TypeError):
                        row_dict[column] = None
                result.append(row_dict)
        else:
            result = []
    except Exception as e:
        raise
    finally:
        conn.close()
    
    return result

def add_student(student_id, name, faculty, dob, email, address):
    """Add or update a student in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DB_TYPE == 'mysql':
        cursor.execute(
            "INSERT INTO students (id, name, faculty, dob, email, address) VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE name=%s, faculty=%s, dob=%s, email=%s, address=%s",
            (student_id, name, faculty, dob, email, address, name, faculty, dob, email, address)
        )
    elif DB_TYPE == 'postgresql':
        cursor.execute(
            "INSERT INTO students (id, name, faculty, dob, email, address) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET name=%s, faculty=%s, dob=%s, email=%s, address=%s",
            (student_id, name, faculty, dob, email, address, name, faculty, dob, email, address)
        )
    else:  # sqlite
        cursor.execute(
            "INSERT OR REPLACE INTO students (id, name, faculty, dob, email, address) VALUES (?, ?, ?, ?, ?, ?)",
            (student_id, name, faculty, dob, email, address)
        )
    
    conn.commit()
    conn.close()

def delete_student_by_id(student_id):
    """Delete a student and their corresponding face image."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DB_TYPE in ['mysql', 'postgresql']:
        cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
    else:  # sqlite
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    
    conn.commit()
    conn.close()
    
    img_path = os.path.join(KNOWN_FACES_DIR, f"{student_id}.jpg")
    if os.path.exists(img_path):
        os.remove(img_path)
    return True

def mark_attendance_db(student_id):
    """Append attendance if not marked within the last 12 hours."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now()
    date, time = now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")

    if DB_TYPE in ['mysql', 'postgresql']:
        cursor.execute(
            "SELECT date, time FROM attendance WHERE student_id = %s ORDER BY date DESC, time DESC LIMIT 1",
            (student_id,)
        )
    else:  # sqlite
        cursor.execute(
            "SELECT date, time FROM attendance WHERE student_id = ? ORDER BY date DESC, time DESC LIMIT 1",
            (student_id,)
        )
    last_entry = cursor.fetchone()

    if last_entry:
        try:
            last_dt = None
            # For all database types, safely access the date and time values
            if last_entry is not None and len(last_entry) >= 2:
                # Use a more explicit approach to avoid linter issues
                date_val = None
                time_val = None
                try:
                    date_val = last_entry[0]
                    time_val = last_entry[1]
                except (IndexError, TypeError):
                    # If we can't access by index, try other methods
                    if hasattr(last_entry, '__getitem__'):
                        try:
                            date_val = last_entry.__getitem__(0)
                            time_val = last_entry.__getitem__(1)
                        except (IndexError, TypeError):
                            pass
                
                if date_val is not None and time_val is not None:
                    last_dt = datetime.strptime(f"{date_val} {time_val}", "%Y-%m-%d %H:%M:%S")
            
            if last_dt is not None and (now - last_dt).total_seconds() < 43200:  # 12 hours
                conn.close()
                return None
        except (ValueError, TypeError, IndexError):
            # If there's any issue parsing the date/time, we'll just mark attendance
            pass

    if DB_TYPE in ['mysql', 'postgresql']:
        cursor.execute(
            "INSERT INTO attendance (student_id, date, time) VALUES (%s, %s, %s)",
            (student_id, date, time)
        )
    else:  # sqlite
        cursor.execute(
            "INSERT INTO attendance (student_id, date, time) VALUES (?, ?, ?)",
            (student_id, date, time)
        )
    
    conn.commit()
    conn.close()
    student_data = get_student_by_id(student_id)
    student_name = student_data['name'] if student_data else 'Unknown'
    return {'student_id': student_id, 'name': student_name, 'date': date, 'time': time}

def add_attendance_record(student_id, date, time):
    """Add a single attendance record to the database (for migration)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DB_TYPE in ['mysql', 'postgresql']:
        cursor.execute(
            "INSERT INTO attendance (student_id, date, time) VALUES (%s, %s, %s)",
            (student_id, date, time)
        )
    else:  # sqlite
        cursor.execute(
            "INSERT INTO attendance (student_id, date, time) VALUES (?, ?, ?)",
            (student_id, date, time)
        )
    
    conn.commit()
    conn.close()

def delete_attendance_by_id(attendance_id):
    """Delete an attendance record by its primary key."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DB_TYPE in ['mysql', 'postgresql']:
        cursor.execute("DELETE FROM attendance WHERE id = %s", (attendance_id,))
    else:  # sqlite
        cursor.execute("DELETE FROM attendance WHERE id = ?", (attendance_id,))
    
    conn.commit()
    conn.close()
    return True

def get_next_student_id():
    """Generate a new, unique student ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM students")
    rows = cursor.fetchall()
    # For all database types, safely extract IDs
    existing_ids = set()
    for row in rows:
        if row is not None:
            # Safely access the first element
            try:
                student_id = row[0]
                existing_ids.add(student_id)
            except (IndexError, TypeError):
                pass  # Skip invalid rows
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
    cursor = conn.cursor()
    
    if DB_TYPE in ['mysql', 'postgresql']:
        cursor.execute("SELECT * FROM admins WHERE id = %s AND password = %s", (admin_id, password))
    else:  # sqlite
        cursor.execute("SELECT * FROM admins WHERE id = ? AND password = ?", (admin_id, password))
    admin = cursor.fetchone()
    
    conn.close()
    return admin is not None

def update_student(student_id, name, faculty, dob, email, address):
    """Update an existing student's information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DB_TYPE in ['mysql', 'postgresql']:
        cursor.execute(
            "UPDATE students SET name = %s, faculty = %s, dob = %s, email = %s, address = %s WHERE id = %s",
            (name, faculty, dob, email, address, student_id)
        )
    else:  # sqlite
        cursor.execute(
            "UPDATE students SET name = ?, faculty = ?, dob = ?, email = ?, address = ? WHERE id = ?",
            (name, faculty, dob, email, address, student_id)
        )
    
    conn.commit()
    conn.close()

# Initialize the database and tables
create_tables()