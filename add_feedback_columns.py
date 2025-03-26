from app_tocloud import app, db
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_feedback_columns():
    """Add feedback and feedback_at columns to ChatHistory table"""
    with app.app_context():
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('chat_history')]
            
            if 'feedback' not in columns:
                logger.info("Adding 'feedback' column to ChatHistory table...")
                db.session.execute(text('ALTER TABLE chat_history ADD COLUMN feedback VARCHAR(10)'))
                logger.info("Added 'feedback' column successfully.")
            else:
                logger.info("'feedback' column already exists.")
                
            if 'feedback_at' not in columns:
                logger.info("Adding 'feedback_at' column to ChatHistory table...")
                db.session.execute(text('ALTER TABLE chat_history ADD COLUMN feedback_at DATETIME'))
                logger.info("Added 'feedback_at' column successfully.")
            else:
                logger.info("'feedback_at' column already exists.")
                
            db.session.commit()
            logger.info("Migration completed successfully.")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during migration: {str(e)}", exc_info=True)
            raise

if __name__ == '__main__':
    add_feedback_columns()
