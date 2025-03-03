from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():
        # Check if admin user already exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123')  # You can change this password
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists!")
