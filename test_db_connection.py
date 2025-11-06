#!/usr/bin/env python3
"""
Test database connection script
"""

import os
import sys

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test the database connection with the current configuration."""
    try:
        # Try to import the new SQL database module
        from database_sql import get_db_connection, create_tables
        print("Using database_sql module")
    except ImportError:
        # Fallback to the original SQLite database module
        try:
            from database import get_db_connection, create_tables
            print("Using database module (SQLite)")
        except ImportError:
            print("Error: Could not import database module")
            return False
    
    try:
        # Test connection
        conn = get_db_connection()
        print(f"Database connection successful: {conn}")
        
        # Test table creation
        create_tables()
        print("Tables created successfully")
        
        # Close connection
        if hasattr(conn, 'close'):
            conn.close()
        
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing database connection...")
    success = test_database_connection()
    if success:
        print("Database connection test PASSED")
        sys.exit(0)
    else:
        print("Database connection test FAILED")
        sys.exit(1)