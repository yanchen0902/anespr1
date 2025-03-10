from sqlalchemy import create_engine, text
import os
from models import db, Patient, ChatHistory, User
from datetime import datetime

# Database connection string for local testing
db_url = "mysql+pymysql://root:anespr123@localhost/patients"

# Create engine
engine = create_engine(db_url)

def check_tables():
    """Check all tables and their contents"""
    try:
        with engine.connect() as conn:
            # Check chat_history table
            print("\n=== Chat History Table ===")
            result = conn.execute(text("SELECT COUNT(*) FROM chat_history"))
            count = result.scalar()
            print(f"Total chat messages: {count}")
            
            if count > 0:
                result = conn.execute(text("""
                    SELECT ch.id, ch.patient_id, ch.message_type, ch.message, ch.response, 
                           ch.created_at, p.name as patient_name
                    FROM chat_history ch
                    JOIN patient p ON ch.patient_id = p.id
                    ORDER BY ch.created_at DESC
                    LIMIT 5
                """))
                print("\nMost recent chat messages:")
                for row in result:
                    print(f"\nID: {row.id}")
                    print(f"Patient: {row.patient_name} (ID: {row.patient_id})")
                    print(f"Type: {row.message_type}")
                    print(f"Message: {row.message}")
                    print(f"Response: {row.response}")
                    print(f"Created: {row.created_at}")
            
            # Check patient table
            print("\n=== Patient Table ===")
            result = conn.execute(text("SELECT COUNT(*) FROM patient"))
            count = result.scalar()
            print(f"Total patients: {count}")
            
            if count > 0:
                result = conn.execute(text("""
                    SELECT id, name, created_at 
                    FROM patient 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """))
                print("\nMost recent patients:")
                for row in result:
                    print(f"ID: {row.id}, Name: {row.name}, Created: {row.created_at}")
                    
                # Check if these patients have any chat history
                for row in result:
                    chat_count = conn.execute(text(
                        "SELECT COUNT(*) FROM chat_history WHERE patient_id = :pid"
                    ), {"pid": row.id}).scalar()
                    print(f"Patient {row.name} (ID: {row.id}) has {chat_count} chat messages")
    
    except Exception as e:
        print(f"Error checking database: {str(e)}")

if __name__ == "__main__":
    check_tables()
