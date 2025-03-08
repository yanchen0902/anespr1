from flask import Flask
from flask_login import LoginManager, UserMixin

app = Flask(__name__)
app.secret_key = 'test-secret-key'

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    return None

@app.route('/')
def home():
    return 'Test app running!'

if __name__ == '__main__':
    app.run(debug=True)

import unittest
from flask import Flask, session
from flask_login import LoginManager, UserMixin, current_user, login_user
from werkzeug.security import generate_password_hash
from models import db, User, Patient

class TestLogin(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize Flask-Login
        self.login_manager = LoginManager()
        self.login_manager.init_app(self.app)
        
        # Initialize database
        db.init_app(self.app)
        
        # Create application context
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        
        # Create test admin user
        self.admin_user = User(
            username='test_admin',
            password_hash=generate_password_hash('test123')
        )
        db.session.add(self.admin_user)
        db.session.commit()
        
        # Create test patient
        self.test_patient = Patient(
            name='Test Patient',
            age=30,
            sex='M'
        )
        db.session.add(self.test_patient)
        db.session.commit()
        
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_admin_login_success(self):
        """Test successful admin login"""
        with self.client as c:
            response = c.post('/login', data={
                'username': 'test_admin',
                'password': 'test123'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(current_user.is_authenticated)

    def test_admin_login_fail(self):
        """Test failed admin login with wrong password"""
        with self.client as c:
            response = c.post('/login', data={
                'username': 'test_admin',
                'password': 'wrong_password'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 401)
            self.assertFalse(current_user.is_authenticated)

    def test_patient_identification(self):
        """Test patient identification system"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 'test_session'
                sess['patient_info'] = {'name': 'Test Patient'}
            
            # Test patient lookup
            response = c.post('/chat', json={
                'message': 'Test Patient',
                'user_id': 'test_session'
            })
            self.assertEqual(response.status_code, 200)
            self.assertIn('patient_id', session)

    def test_patient_creation(self):
        """Test new patient creation when no match found"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 'test_session'
                sess['patient_info'] = {'name': 'New Patient'}
            
            # Test new patient creation
            response = c.post('/chat', json={
                'message': 'New Patient',
                'user_id': 'test_session'
            })
            self.assertEqual(response.status_code, 200)
            
            # Verify patient was created
            new_patient = Patient.query.filter_by(name='New Patient').first()
            self.assertIsNotNone(new_patient)

    def test_similar_patient_matching(self):
        """Test matching of similar patient names"""
        similar_patient = Patient(
            name='Test Patient Jr',
            age=25,
            sex='M'
        )
        db.session.add(similar_patient)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 'test_session'
                sess['patient_info'] = {'name': 'Test Patient Junior'}
            
            # Test similar name matching
            response = c.post('/chat', json={
                'message': 'Test Patient Junior',
                'user_id': 'test_session'
            })
            self.assertEqual(response.status_code, 200)
            self.assertIn('patient_id', session)
            self.assertEqual(session['patient_id'], similar_patient.id)

if __name__ == '__main__':
    unittest.main()
