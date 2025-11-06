
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, jsonify, Response
import os
import base64
import io
import csv
import random
from datetime import datetime
import re
from functools import wraps
try:
    # Try to use the new SQL database module first
    from database_sql import (
        add_student, get_attendance, get_next_student_id, get_all_students, get_student_by_id, 
        delete_student_by_id, verify_admin, update_student, KNOWN_FACES_DIR, get_student_attendance
    )
    print("Using database_sql module")
except ImportError:
    # Fallback to the original SQLite database module
    from database import (
        add_student, get_attendance, get_next_student_id, get_all_students, get_student_by_id, 
        delete_student_by_id, verify_admin, update_student, KNOWN_FACES_DIR, get_student_attendance
    )
    print("Using database module")

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Authentication --- #
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # CAPTCHA validation
        user_captcha = request.form.get('captcha', '')
        if 'captcha' not in session or user_captcha.lower() != session['captcha'].lower():
            flash('Invalid CAPTCHA. Please try again.', 'danger')
            return redirect(url_for('login'))

        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['logged_in'] = True
            flash('You were successfully logged in', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    captcha_text = ''.join(random.choices('0123456789', k=5))
    session['captcha'] = captcha_text
    return render_template('login.html', captcha=captcha_text)

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    flash('You were logged out.', 'info')
    return redirect(url_for('login'))

# --- Web Pages --- #
@app.route('/')
@login_required
def index():
    """Render the main page with attendance records."""
    all_students = get_all_students()
    all_records = get_attendance()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Prepare dashboard stats
    stats = {
        'total_students': len(all_students),
        'total_records': len(all_records),
        'today_records': sum(1 for r in all_records if r['date'] == today_str)
    }
    return render_template('index.html', attendance=all_records[:10], **stats)

@app.route('/students')
@login_required
def list_students():
    """Render the page that lists all students."""
    students = get_all_students()
    return render_template('students.html', students=students)

@app.route('/attendance')
@login_required
def list_attendance():
    """Render a page with all attendance records, fully searchable."""
    attendance_records = get_attendance()
    return render_template('attendance.html', attendance=attendance_records)

@app.route('/attendance/export')
@login_required
def export_attendance():
    """Export the full attendance log to a CSV file."""
    attendance_records = get_attendance()

    # Use an in-memory string buffer to build the CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Write the header row
    writer.writerow(['Student ID', 'Name', 'Date', 'Time'])

    # Write the data rows
    for record in attendance_records:
        writer.writerow([record['student_id'], record['name'], record['date'], record['time']])

    output.seek(0)
    return Response(output, mimetype="text/csv", headers={"Content-Disposition":"attachment;filename=attendance_log.csv"})

@app.route('/student/<student_id>')
@login_required
def student_details(student_id):
    """Render the details for a single student."""
    student = get_student_by_id(student_id)
    if not student:
        flash(f"Student with ID {student_id} not found.", "danger")
        return redirect(url_for('list_students'))
    return render_template('student_detail.html', student=student)

@app.route('/known_faces/<filename>')
def known_face_image(filename):
    """Serve images from the known_faces directory."""
    return send_from_directory(KNOWN_FACES_DIR, filename)

# --- Admin Panel Routes --- #
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        # CAPTCHA validation
        user_captcha = request.form.get('captcha', '')
        if 'captcha' not in session or user_captcha.lower() != session['captcha'].lower():
            flash('Invalid CAPTCHA. Please try again.', 'danger')
            return redirect(url_for('admin_login'))

        admin_id = request.form['username']
        password = request.form['password']
        
        if verify_admin(admin_id, password):
            session['admin_logged_in'] = True
            session['admin_id'] = admin_id
            flash('Admin login successful', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials. Please try again.', 'danger')
    
    captcha_text = ''.join(random.choices('0123456789', k=5))
    session['captcha'] = captcha_text
    return render_template('admin_login.html', captcha=captcha_text)

@app.route('/admin/logout')
@admin_required
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    flash('Admin logged out.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard with student management overview."""
    all_students = get_all_students()
    all_records = get_attendance()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    stats = {
        'total_students': len(all_students),
        'total_records': len(all_records),
        'today_records': sum(1 for r in all_records if r['date'] == today_str)
    }
    return render_template('admin_dashboard.html', students=all_students, **stats)

@app.route('/admin/register', methods=['GET', 'POST'])
@admin_required
def admin_register():
    """Handle new student registration with live photo capture - Admin only."""
    if request.method == 'POST':
        student_id = get_next_student_id()
        name = request.form['name']
        faculty = request.form.get('faculty', '')
        dob = request.form.get('dob', '')
        email = request.form.get('email', '')
        address = request.form.get('address', '')

        # Add student record to the database first
        add_student(student_id, name, faculty, dob, email, address)

        face_image_data = request.form.get('face_image_data')
        face_image_file = request.files.get('face_image_file')
        face_path = os.path.join(KNOWN_FACES_DIR, f"{student_id}.jpg")

        try:
            if face_image_data and face_image_data != 'data:,':
                # Decode the base64 image from the live capture
                img_data = re.sub('^data:image/.+;base64,', '', face_image_data)
                img_binary = base64.b64decode(img_data)
                with open(face_path, 'wb') as f:
                    f.write(img_binary)
            elif face_image_file:
                # Save the uploaded file
                face_image_file.save(face_path)
            else:
                # No image was provided, which should be caught by the frontend.
                # As a fallback, delete the created student record and show an error.
                flash("No face image was provided. Please capture or upload a photo.", "danger")
                delete_student_by_id(student_id)
                return redirect(url_for('admin_register'))

            flash(f"Student {name} registered successfully with ID: {student_id}", "success")
            return redirect(url_for('admin_dashboard'))

        except Exception as e:
            # If anything goes wrong with image saving, delete the student record
            delete_student_by_id(student_id)
            flash(f"An error occurred while saving the image: {e}", "danger")
            return redirect(url_for('admin_register'))

    return render_template('admin_register.html')

@app.route('/admin/student/<student_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_student(student_id):
    """Edit student information - Admin only."""
    student = get_student_by_id(student_id)
    if not student:
        flash(f"Student with ID {student_id} not found.", "danger")
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        faculty = request.form.get('faculty', '')
        dob = request.form.get('dob', '')
        email = request.form.get('email', '')
        address = request.form.get('address', '')
        
        update_student(student_id, name, faculty, dob, email, address)
        
        # Handle face image update if provided
        face_image_data = request.form.get('face_image_data')
        face_image_file = request.files.get('face_image_file')
        face_path = os.path.join(KNOWN_FACES_DIR, f"{student_id}.jpg")
        
        try:
            if face_image_data and face_image_data != 'data:,':
                # Decode the base64 image from the live capture
                img_data = re.sub('^data:image/.+;base64,', '', face_image_data)
                img_binary = base64.b64decode(img_data)
                with open(face_path, 'wb') as f:
                    f.write(img_binary)
            elif face_image_file:
                # Save the uploaded file
                face_image_file.save(face_path)
        except Exception as e:
            flash(f"An error occurred while updating the image: {e}", "warning")
        
        flash(f"Student {name} updated successfully", "success")
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_edit_student.html', student=student)

@app.route('/admin/student/<student_id>/delete', methods=['POST'])
@admin_required
def admin_delete_student(student_id):
    """Handle the deletion of a student from the admin panel."""
    student = get_student_by_id(student_id)
    if student:
        delete_student_by_id(student_id)
        return jsonify({'success': True, 'message': f"Student {student.get('name', student_id)} has been deleted."})
    else:
        return jsonify({'success': False, 'message': f"Student with ID {student_id} not found."}), 404

# --- Student Panel Routes --- #
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    """Student login to view their attendance records."""
    if request.method == 'POST':
        student_id = request.form['student_id']
        
        # Verify student exists
        student = get_student_by_id(student_id)
        
        if not student:
            flash('Invalid Student ID. Please try again.', 'danger')
            return redirect(url_for('student_login'))
        
        # Store student ID in session
        session['student_id'] = student_id
        flash(f'Welcome, {student["name"]}!', 'success')
        return redirect(url_for('student_attendance'))
    
    return render_template('student_login.html')

@app.route('/student/attendance')
def student_attendance():
    """Display attendance records for the logged-in student."""
    if 'student_id' not in session:
        flash('Please log in to view your attendance records.', 'warning')
        return redirect(url_for('student_login'))
    
    student_id = session['student_id']
    student = get_student_by_id(student_id)
    
    if not student:
        flash('Student record not found.', 'danger')
        session.pop('student_id', None)
        return redirect(url_for('student_login'))
    
    try:
        attendance_records = get_student_attendance(student_id)
    except Exception as e:
        flash(f'Error retrieving attendance records: {e}', 'danger')
        return redirect(url_for('student_login'))
    
    return render_template('student_attendance.html', student=student, attendance=attendance_records)

@app.route('/student/logout')
def student_logout():
    """Logout the student."""
    session.pop('student_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('student_login'))

if __name__ == '__main__':
    app.run(debug=True)
