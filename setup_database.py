#!/usr/bin/env python3
"""
Database setup script
"""

import os
import sys

def setup_database():
    """Setup database based on user input."""
    print("Database Setup")
    print("=" * 20)
    
    print("\nSelect database type:")
    print("1. SQLite (default, no additional setup required)")
    print("2. MySQL")
    print("3. PostgreSQL")
    
    choice = input("\nEnter your choice (1-3, default is 1): ").strip()
    
    if choice == "2":
        db_type = "mysql"
        print("\nMySQL Configuration:")
        db_host = input("Host (default: localhost): ").strip() or "localhost"
        db_port = input("Port (default: 3306): ").strip() or "3306"
        db_name = input("Database name (default: attendance_db): ").strip() or "attendance_db"
        db_user = input("Username (default: root): ").strip() or "root"
        db_password = input("Password: ").strip()
        
    elif choice == "3":
        db_type = "postgresql"
        print("\nPostgreSQL Configuration:")
        db_host = input("Host (default: localhost): ").strip() or "localhost"
        db_port = input("Port (default: 5432): ").strip() or "5432"
        db_name = input("Database name (default: attendance_db): ").strip() or "attendance_db"
        db_user = input("Username (default: postgres): ").strip() or "postgres"
        db_password = input("Password: ").strip()
        
    else:
        db_type = "sqlite"
        db_host = "localhost"
        db_port = "3306"
        db_name = "attendance_db"
        db_user = "root"
        db_password = ""
        print("\nUsing SQLite (no additional setup required)")
    
    # Create .env file
    env_content = f"""DB_TYPE={db_type}
DB_HOST={db_host}
DB_PORT={db_port}
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print(f"\nDatabase configuration saved to .env file")
    print("\nConfiguration summary:")
    print(f"  Database type: {db_type}")
    if db_type != "sqlite":
        print(f"  Host: {db_host}")
        print(f"  Port: {db_port}")
        print(f"  Database name: {db_name}")
        print(f"  Username: {db_user}")
        # Don't print password for security
    
    if db_type == "mysql":
        print("\nTo install MySQL dependencies, run:")
        print("  pip install mysql-connector-python")
    elif db_type == "postgresql":
        print("\nTo install PostgreSQL dependencies, run:")
        print("  pip install psycopg2-binary")
    
    print("\nSetup complete!")

if __name__ == "__main__":
    setup_database()