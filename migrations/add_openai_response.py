from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import sys
import os
from dotenv import load_dotenv

# Add parent directory to path so we can import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import db, ChatHistory

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configure SQLAlchemy based on environment
    if os.getenv('GAE_ENV', '').startswith('standard'):
        # Running on App Engine, use Cloud SQL with unix socket
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:anespr123@/patients?unix_socket=/cloudsql/anespr1-asia-east:asia-east1:anespr1&charset=utf8mb4'
    else:
        # Local development - use SQLite
        sqlite_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'patients.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_path}'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def add_openai_columns():
    """Add openai_response and preferred_response columns to ChatHistory table"""
    app = create_app()
    with app.app_context():
        # Check if columns already exist
        inspector = db.inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('chat_history')]
        
        if 'openai_response' not in columns:
            print("Adding 'openai_response' column to ChatHistory table...")
            db.session.execute(text('ALTER TABLE chat_history ADD COLUMN openai_response TEXT'))
            print("Added 'openai_response' column successfully.")
        else:
            print("'openai_response' column already exists.")
            
        if 'preferred_response' not in columns:
            print("Adding 'preferred_response' column to ChatHistory table...")
            db.session.execute(text('ALTER TABLE chat_history ADD COLUMN preferred_response VARCHAR(10)'))
            print("Added 'preferred_response' column successfully.")
        else:
            print("'preferred_response' column already exists.")
            
        # Update existing message types
        print("Updating existing message types...")
        db.session.execute(text("""
            UPDATE chat_history 
            SET message_type = 'chat' 
            WHERE message_type = 'bot' 
            AND message IS NOT NULL 
            AND response IS NOT NULL
        """))
        print("Updated message types successfully.")
        
        # Commit all changes
        db.session.commit()

if __name__ == '__main__':
    add_openai_columns()
    print("Migration completed successfully.")
