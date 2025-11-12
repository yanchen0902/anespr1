"""
Migration: Expand message_type column for EMR snapshot support
==============================================================

This migration expands ChatHistory.message_type from VARCHAR(10) to VARCHAR(20)
to support the new 'emr_snapshot' message type (14 characters).

Run this ONLY if you have an existing database.
For fresh installations, init_db.py already creates the correct schema.

Usage:
    python migrations/expand_message_type_for_emr.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, init_db
from flask import Flask

def expand_message_type_column():
    """Expand message_type column from VARCHAR(10) to VARCHAR(20)"""

    app = Flask(__name__)
    init_db(app)

    with app.app_context():
        # Check if we're using SQLite or MySQL
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']

        if 'sqlite' in db_uri:
            print("SQLite database detected")
            print("\nWARNING: SQLite doesn't support ALTER COLUMN directly.")
            print("The column will be updated when you recreate the database.")
            print("\nFor existing SQLite databases:")
            print("  1. Backup your database: cp patients.db patients.db.backup")
            print("  2. The column change is already in models.py")
            print("  3. SQLite will handle VARCHAR(20) automatically on next write")
            print("\nNo action needed - SQLite is flexible with VARCHAR lengths.")

        elif 'mysql' in db_uri or 'pymysql' in db_uri:
            print("MySQL database detected")
            print("\nExecuting ALTER TABLE to expand message_type column...")

            try:
                # MySQL syntax
                sql = "ALTER TABLE chat_history MODIFY COLUMN message_type VARCHAR(20)"
                db.session.execute(sql)
                db.session.commit()
                print("✅ Successfully expanded message_type column to VARCHAR(20)")
                print("\nYou can now use 'emr_snapshot' as a message_type value.")

            except Exception as e:
                db.session.rollback()
                print(f"❌ Error executing migration: {str(e)}")
                print("\nYou may need to run this SQL manually:")
                print("  ALTER TABLE chat_history MODIFY COLUMN message_type VARCHAR(20);")
                sys.exit(1)

        else:
            print(f"Unknown database type: {db_uri}")
            print("Please modify message_type column manually to VARCHAR(20)")
            sys.exit(1)

if __name__ == '__main__':
    print("=" * 70)
    print("EMR Integration Migration: Expand message_type Column")
    print("=" * 70)
    print()

    response = input("Have you backed up your database? (yes/no): ")
    if response.lower() != 'yes':
        print("Please backup your database first, then run this script again.")
        sys.exit(0)

    expand_message_type_column()

    print()
    print("=" * 70)
    print("Migration complete!")
    print("=" * 70)
