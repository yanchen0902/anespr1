import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db, init_db
from sqlalchemy import text

# Initialize app
app = Flask(__name__)
init_db(app)

with app.app_context():
    try:
        # Check if column exists first
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('chatbot_evaluation')]
        
        if 'evaluator_name' not in columns:
            print("Adding evaluator_name column to chatbot_evaluation table...")
            db.session.execute(text("ALTER TABLE chatbot_evaluation ADD COLUMN evaluator_name VARCHAR(100)"))
            db.session.commit()
            print("Column added successfully.")
        else:
            print("evaluator_name column already exists.")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        db.session.rollback()
