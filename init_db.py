from flask import Flask
from models import db, User, init_db
from werkzeug.security import generate_password_hash
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_db():
    # Create Flask app
    app = Flask(__name__)
    
    # Initialize database
    init_db(app)
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            logger.info("Created all tables")
            
            # Check if admin user exists
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                # Create admin user
                admin = User(
                    username='admin',
                    password_hash=generate_password_hash('admin123')
                )
                db.session.add(admin)
                db.session.commit()
                logger.info("Admin user created successfully!")
            else:
                logger.info("Admin user already exists!")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise

if __name__ == '__main__':
    create_db()
