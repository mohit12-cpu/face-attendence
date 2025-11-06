import sqlite3

# Connect to the database
conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in the database:")
for table in tables:
    print(f"  - {table[0]}")

# Check students table
try:
    cursor.execute("SELECT * FROM students;")
    students = cursor.fetchall()
    print(f"\nStudents in the database ({len(students)} found):")
    for student in students:
        print(f"  {student}")
except Exception as e:
    print(f"Error accessing students table: {e}")

# Check attendance table
try:
    cursor.execute("SELECT * FROM attendance;")
    attendance = cursor.fetchall()
    print(f"\nAttendance records ({len(attendance)} found):")
    for record in attendance:
        print(f"  {record}")
except Exception as e:
    print(f"Error accessing attendance table: {e}")

conn.close()