from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager
from datetime import datetime
import re
import os

# Initialize SQLAlchemy
db = SQLAlchemy()

# Initialize Flask-Login
login_manager = LoginManager()

def init_db(app):
    """Initialize the database with the given Flask app"""
    # Configure SQLAlchemy based on environment
    if os.getenv('GAE_ENV', '').startswith('standard'):
        # Running on App Engine, use Cloud SQL with unix socket
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:anespr123@/patients?unix_socket=/cloudsql/anespr1-asia-east:asia-east1:anespr1&charset=utf8mb4'
    else:
        # Local development - use SQLite
        sqlite_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'patients.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_path}'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'admin_login'

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Always store in UTC
    self_pay_items = db.relationship('SelfPayItem', backref='patient', lazy=True)
    chat_history = db.relationship('ChatHistory', backref='patient', lazy=True)

class SelfPayItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    item_name = db.Column(db.String(100))
    price = db.Column(db.Float)
    selected_at = db.Column(db.DateTime, default=datetime.utcnow)  # Always store in UTC

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    message = db.Column(db.Text)  # User's message
    response = db.Column(db.Text)  # Azure OpenAI response (primary for Linux deployment)
    openai_response = db.Column(db.Text)  # Legacy/alternative response field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Always store in UTC
    message_type = db.Column(db.String(20))  # 'user', 'bot', 'chat', 'summary', or 'emr_snapshot'
    feedback = db.Column(db.String(10), default=None)  # 'like', 'dislike', or 'ban'
    feedback_at = db.Column(db.DateTime, default=None)  # When feedback was given, in UTC
    preferred_response = db.Column(db.String(10), default=None)  # 'gemini' or 'openai'

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
        # Sanitize message and responses before saving
        if 'message' in kwargs:
            kwargs['message'] = self.sanitize_text(kwargs['message'])
        if 'response' in kwargs:
            kwargs['response'] = self.sanitize_text(kwargs['response'])
        if 'openai_response' in kwargs:
            kwargs['openai_response'] = self.sanitize_text(kwargs['openai_response'])
        super(ChatHistory, self).__init__(**kwargs)

class ChatbotEvaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    evaluated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    evaluator_name = db.Column(db.String(100))
    accuracy_score = db.Column(db.Integer, nullable=False)
    trustworthiness_score = db.Column(db.Integer, nullable=False)
    empathy_score = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text)
    evaluated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    patient = db.relationship('Patient', backref=db.backref('evaluations', lazy=True))
    evaluator = db.relationship('User', backref=db.backref('evaluations_given', lazy=True))

def init_login_manager(app):
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))