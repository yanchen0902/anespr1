import mysql.connector
from mysql.connector import Error
import os
from app_tocloud import app, db, User
from werkzeug.security import generate_password_hash

def setup_mysql():
    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='anespr123'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS patients")
            cursor.execute("USE patients")
            print("Database 'patients' created/selected successfully")
            
            # Set UTF8MB4 as default charset
            cursor.execute("ALTER DATABASE patients CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("Set database charset to UTF8MB4")
            
            # Close MySQL connection
            cursor.close()
            connection.close()
            
            # Initialize Flask app context and create tables
            with app.app_context():
                # Create all tables
                db.create_all()
                print("Created all tables")
                
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
                    print("Admin user created successfully!")
                else:
                    print("Admin user already exists!")
                    
    except Error as e:
        print(f"Error: {e}")
        raise

if __name__ == '__main__':
    setup_mysql()
