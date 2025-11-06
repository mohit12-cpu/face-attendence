
import csv
import os
from database import add_student, add_attendance_record, get_all_students, SCRIPT_DIR, create_tables, DB_FILE

# Use absolute paths for CSV files
STUDENTS_CSV = os.path.join(SCRIPT_DIR, "students.csv")
ATTENDANCE_CSV = os.path.join(SCRIPT_DIR, "attendance.csv")

def migrate_students():
    """Migrate students from the CSV file to the database."""
    if not os.path.exists(STUDENTS_CSV):
        print(f"Source file not found, skipping student migration: {STUDENTS_CSV}")
        return

    with open(STUDENTS_CSV, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        student_count = 0
        for row in reader:
            add_student(
                student_id=row['ID'],
                name=row['Name'],
                faculty=row.get('Faculty', ''),
                dob=row.get('DOB', ''),
                email=row.get('Email', ''),
                address=row.get('Address', '')
            )
            student_count += 1
    print(f"Successfully migrated {student_count} students from {STUDENTS_CSV}")

def migrate_attendance():
    """Migrate attendance records from the CSV file to the database."""
    if not os.path.exists(ATTENDANCE_CSV):
        print(f"Source file not found, skipping attendance migration: {ATTENDANCE_CSV}")
        return

    with open(ATTENDANCE_CSV, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        attendance_count = 0
        for row in reader:
            # Ensure the record has the required fields
            if all(k in row for k in ['ID', 'Date', 'Time']):
                add_attendance_record(
                    student_id=row['ID'],
                    date=row['Date'],
                    time=row['Time']
                )
                attendance_count += 1
    print(f"Successfully migrated {attendance_count} attendance records from {ATTENDANCE_CSV}")

if __name__ == "__main__":
    print("Starting data migration...")
    # Recreate the database for a clean migration
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Removed existing database: {DB_FILE}")
    
    print("Creating new database and tables...")
    create_tables()

    # Run the migrations
    migrate_students()
    migrate_attendance()

    print("\nMigration complete.")
    # Verify by printing the number of students
    students_in_db = get_all_students()
    print(f"Verification: Found {len(students_in_db)} students in the database.")
    print("You can now run the main application.")
