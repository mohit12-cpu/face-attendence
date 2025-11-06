# CognAttendance - Face Recognition Attendance System

CognAttendance is a student attendance management system that uses facial recognition technology to track and record student attendance. Built with Python, Flask, and OpenCV, this system provides an efficient and automated way to manage student attendance using facial biometrics.

## Features

- **Facial Recognition**: Automatically identify students using face recognition technology
- **Multi-User System**: Separate interfaces for administrators and students
- **Real-time Attendance**: Capture and record attendance in real-time
- **Database Flexibility**: Supports SQLite (default), MySQL, and PostgreSQL
- **Web-based Interface**: Responsive web interface built with Flask and Bootstrap
- **Data Export**: Export attendance records to CSV format
- **Student Management**: Add, edit, and remove student records
- **Attendance Dashboard**: Visual dashboard with statistics and recent records
- **Security**: Admin authentication and CAPTCHA protection

## Technology Stack

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Database**: SQLite/MySQL/PostgreSQL with SQLAlchemy
- **Face Recognition**: OpenCV, face_recognition library
- **Image Processing**: Pillow
- **Production Server**: Waitress

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd face-attendance-system
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. For MySQL or PostgreSQL support (optional):
   ```bash
   # For MySQL
   pip install mysql-connector-python
   
   # For PostgreSQL
   pip install psycopg2-binary
   ```

## Database Configuration

The system supports three database types:
- SQLite (default, no additional setup required)
- MySQL
- PostgreSQL

### Configuration Options

Database configuration is controlled through environment variables:
- `DB_TYPE`: Database type ('sqlite', 'mysql', or 'postgresql')
- `DB_HOST`: Database server host
- `DB_PORT`: Database server port
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password

### Setup Script

Run the interactive setup script to configure your database:
```bash
python setup_database.py
```

## Usage

### Development Mode

To run the application in development mode:
```bash
python app.py
```

The application will be accessible at `http://127.0.0.1:5000`

### Production Mode

To run the application in production mode:
```bash
python run_production.py
```

By default, the application will be accessible at `http://127.0.0.1:8080`

### Environment Variables for Production

- `APP_HOST`: Host address (default: 0.0.0.0)
- `APP_PORT`: Port number (default: 8080)
- `APP_THREADS`: Number of worker threads (default: 8)

## User Roles

### Administrator

Administrators have full access to the system:
- Manage student records (add, edit, delete)
- View all attendance records
- Export attendance data
- Access dashboard with statistics

Login at: `/admin/login`

Default admin credentials:
- Username: admin
- Password: admin

### Students

Students can view their own attendance records:
- Login with their student ID
- View personal attendance history

Login at: `/student/login`

## Project Structure

```
face-attendance-system/
├── app.py                 # Main Flask application
├── database.py            # SQLite database implementation
├── database_sql.py        # Multi-database implementation
├── db_config.py           # Database configuration
├── run_production.py      # Production server setup
├── setup_database.py      # Database setup script
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
├── static/                # CSS and static assets
├── known_faces/           # Student face images
└── attendance.db          # Default SQLite database
```

## Face Recognition Workflow

1. **Student Registration**: Capture student face image during registration
2. **Face Encoding**: System creates facial encodings and stores them
3. **Attendance Capture**: Student faces are captured via webcam
4. **Face Matching**: System matches captured face with known faces
5. **Attendance Recording**: Successful matches record attendance with timestamp

## API Endpoints

### Admin Routes
- `/admin/login` - Admin login page
- `/admin` - Admin dashboard
- `/admin/register` - Register new student
- `/admin/student/<id>/edit` - Edit student information
- `/admin/student/<id>/delete` - Delete student

### Student Routes
- `/student/login` - Student login page
- `/student/attendance` - Student attendance records
- `/student/logout` - Student logout

### General Routes
- `/login` - Main admin login
- `/` - Main dashboard
- `/students` - List all students
- `/attendance` - View all attendance records
- `/attendance/export` - Export attendance to CSV
- `/student/<id>` - View student details

## Data Management

### Database Schema

1. **students**
   - id (Primary Key)
   - name
   - faculty
   - dob (date of birth)
   - email
   - address

2. **attendance**
   - id (Primary Key, Auto-increment)
   - student_id (Foreign Key to students.id)
   - date
   - time

3. **admins**
   - id (Primary Key)
   - password
   - created_at

### Data Migration

Use the migration script to transfer data between database types:
```bash
python migrate_to_db.py
```

## Testing Database Connection

Test your database configuration:
```bash
python test_db_connection.py
```

## Security Features

- CAPTCHA protection on login forms
- Session-based authentication
- Password hashing for admin accounts
- Input validation and sanitization
- Secure file handling for face images

## Troubleshooting

1. **Face Recognition Issues**: Ensure proper lighting and clear face images
2. **Database Connection Errors**: Verify database configuration and credentials
3. **Missing Dependencies**: Install required packages from requirements.txt
4. **Port Conflicts**: Change the port using APP_PORT environment variable

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Face recognition powered by the `face_recognition` library
- Web framework provided by Flask
- Database abstraction with SQLAlchemy
- Production server using Waitress