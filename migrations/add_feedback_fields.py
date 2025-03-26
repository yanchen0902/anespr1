from flask import Flask
from flask_sqlalchemy import SQLAlchemy
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
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def add_feedback_columns():
    """Add feedback and feedback_at columns to ChatHistory table"""
    app = create_app()
    with app.app_context():
        # Check if columns already exist
        inspector = db.inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('chat_history')]
        
        if 'feedback' not in columns:
            print("Adding 'feedback' column to ChatHistory table...")
            db.engine.execute('ALTER TABLE chat_history ADD COLUMN feedback VARCHAR(10)')
            print("Added 'feedback' column successfully.")
        else:
            print("'feedback' column already exists.")
            
        if 'feedback_at' not in columns:
            print("Adding 'feedback_at' column to ChatHistory table...")
            db.engine.execute('ALTER TABLE chat_history ADD COLUMN feedback_at DATETIME')
            print("Added 'feedback_at' column successfully.")
        else:
            print("'feedback_at' column already exists.")

if __name__ == '__main__':
    add_feedback_columns()
    print("Migration completed successfully.")
