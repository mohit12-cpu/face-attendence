
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
import base64
import re
from database import (
    add_student, get_attendance, get_next_student_id, get_all_students, get_student_by_id, 
    delete_student_by_id, KNOWN_FACES_DIR
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    """Render the main page with attendance records."""
    attendance_records = get_attendance()
    return render_template('index.html', attendance=attendance_records)

@app.route('/students')
def list_students():
    """Render the page that lists all students."""
    students = get_all_students()
    return render_template('students.html', students=students)

@app.route('/student/<student_id>')
def student_details(student_id):
    """Render the details for a single student."""
    student = get_student_by_id(student_id)
    if not student:
        flash(f"Student with ID {student_id} not found.", "danger")
        return redirect(url_for('list_students'))
    return render_template('student_detail.html', student=student)

@app.route('/student/<student_id>/delete', methods=['POST'])
def delete_student_web(student_id):
    """Handle the deletion of a student from the web UI."""
    student = get_student_by_id(student_id)
    if student:
        delete_student_by_id(student_id)
        flash(f"Student {student.get('name', student_id)} has been deleted.", "success")
    else:
        flash(f"Student with ID {student_id} not found.", "danger")
    return redirect(url_for('list_students'))

@app.route('/known_faces/<filename>')
def known_face_image(filename):
    """Serve images from the known_faces directory."""
    return send_from_directory(KNOWN_FACES_DIR, filename)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle new student registration with live photo capture."""
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
                return redirect(url_for('register'))

            flash(f"Student {name} registered successfully with ID: {student_id}", "success")
            return redirect(url_for('list_students'))

        except Exception as e:
            # If anything goes wrong with image saving, delete the student record
            delete_student_by_id(student_id)
            flash(f"An error occurred while saving the image: {e}", "danger")
            return redirect(url_for('register'))

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
