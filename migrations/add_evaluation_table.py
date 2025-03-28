from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import db, ChatbotEvaluation

if __name__ == '__main__':
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        print("Creating evaluation table...")
        # This will create only tables that don't exist yet
        db.create_all()
        print("Evaluation table created successfully!")
