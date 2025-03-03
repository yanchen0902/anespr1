from app import app, db
from models import User
from werkzeug.security import generate_password_hash
import os

# Use the cloud database URL
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:anespr123@/patients?unix_socket=/cloudsql/gen-lang-client-0605675586:asia-east1:anespr1"

with app.app_context():
    # Create tables if they don't exist
    db.create_all()
    
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
