from app_tocloud import app, db
from models import User, Patient, ChatHistory, SelfPayItem
import os

def update_schema():
    try:
        with app.app_context():
            # Create all tables with new schema
            db.create_all()
            
            # Execute raw SQL to update existing tables' collation
            db.session.execute("""
                ALTER DATABASE patients CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """)
            
            # Update ChatHistory table specifically
            db.session.execute("""
                ALTER TABLE chat_history 
                MODIFY message TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                MODIFY response TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                MODIFY message_type VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """)
            
            # Update Patient table
            db.session.execute("""
                ALTER TABLE patient
                MODIFY name VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                MODIFY sex VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                MODIFY operation VARCHAR(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                MODIFY medical_history TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                MODIFY worry TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """)
            
            db.session.commit()
            print("Schema updated successfully!")
            
    except Exception as e:
        print(f"Error updating schema: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    update_schema()
