from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager
from datetime import datetime
import re

# Initialize SQLAlchemy
db = SQLAlchemy()

# Initialize Flask-Login
login_manager = LoginManager()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password_hash = db.Column(db.String(120))

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sex = db.Column(db.String(10))
    age = db.Column(db.Integer)
    name = db.Column(db.String(100))
    operation = db.Column(db.String(200))
    cfs = db.Column(db.String(50))
    medical_history = db.Column(db.Text)
    worry = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    self_pay_items = db.relationship('SelfPayItem', backref='patient', lazy=True)
    chat_history = db.relationship('ChatHistory', backref='patient', lazy=True)

class SelfPayItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    item_name = db.Column(db.String(100))
    price = db.Column(db.Float)
    selected_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    message = db.Column(db.Text)  # User's message
    response = db.Column(db.Text)  # API response
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    message_type = db.Column(db.String(10))  # 'user' or 'bot'

    def sanitize_text(self, text):
        if not text:
            return None
        # Remove any non-printable characters
        text = ''.join(char for char in text if char.isprintable())
        # Replace special quotes and dashes
        text = re.sub(r'[""'']', '"', text)
        text = re.sub(r'[–—]', '-', text)
        return text

    def __init__(self, **kwargs):
        # Sanitize message and response before saving
        if 'message' in kwargs:
            kwargs['message'] = self.sanitize_text(kwargs['message'])
        if 'response' in kwargs:
            kwargs['response'] = self.sanitize_text(kwargs['response'])
        super(ChatHistory, self).__init__(**kwargs)

def init_login_manager(app):
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))