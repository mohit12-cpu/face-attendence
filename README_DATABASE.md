# Database Configuration

This application supports multiple database backends:
- SQLite (default, no additional setup required)
- MySQL
- PostgreSQL

## Database Configuration

To configure which database to use, set the following environment variables:

### For MySQL:
```bash
export DB_TYPE=mysql
export DB_HOST=localhost
export DB_PORT=3306
export DB_NAME=attendance_db
export DB_USER=your_username
export DB_PASSWORD=your_password
```

### For PostgreSQL:
```bash
export DB_TYPE=postgresql
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=attendance_db
export DB_USER=your_username
export DB_PASSWORD=your_password
```

### For SQLite (default):
SQLite is used by default and requires no additional configuration. The database file will be created automatically as `attendance.db` in the application directory.

## Database Schema

The application uses three tables:

1. **students** - Stores student information
   - id (Primary Key)
   - name
   - faculty
   - dob (date of birth)
   - email
   - address

2. **attendance** - Stores attendance records
   - id (Primary Key, Auto-increment)
   - student_id (Foreign Key to students.id)
   - date
   - time

3. **admins** - Stores admin credentials
   - id (Primary Key)
   - password
   - created_at

## Required Dependencies

### For MySQL:
```bash
pip install mysql-connector-python
```

### For PostgreSQL:
```bash
pip install psycopg2-binary
```

### For SQLite:
SQLite is included with Python by default, so no additional installation is required.

## Environment Variables

You can set these environment variables in your system or create a `.env` file in the project root:

```
DB_TYPE=sqlite
DB_HOST=localhost
DB_PORT=3306
DB_NAME=attendance_db
DB_USER=root
DB_PASSWORD=
```

## First Time Setup

1. Install the required dependencies for your chosen database
2. Set the appropriate environment variables
3. Run the application - the database tables will be created automatically
4. For MySQL/PostgreSQL, make sure your database server is running and accessible

## Migration from SQLite to MySQL/PostgreSQL

If you're migrating from SQLite to MySQL or PostgreSQL:

1. Set your environment variables for the new database
2. Run the migration script:
   ```bash
   python migrate_to_db.py
   ```

This will create the necessary tables and migrate any existing data from the SQLite database.