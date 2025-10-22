# Database Migrations

This folder contains database migration scripts for the Anesthesiology Pre-Consultation Chatbot system.

## Migration Scripts

### 1. `add_feedback_fields.py`
**Purpose**: Adds feedback tracking columns to the ChatHistory table

**Columns Added**:
- `feedback` (VARCHAR(10)) - Stores feedback type: 'like', 'dislike', or 'ban'
- `feedback_at` (DATETIME) - Timestamp when feedback was given

**When to Run**:
- After initial database setup if upgrading from an older version
- Safe to run multiple times (has existence checks)

**Usage**:
```bash
python migrations/add_feedback_fields.py
```

---

### 2. `add_openai_response.py`
**Purpose**: Adds Azure OpenAI response tracking columns and updates message types

**Columns Added**:
- `openai_response` (TEXT) - Stores Azure OpenAI model response
- `preferred_response` (VARCHAR(10)) - Indicates which model response is preferred ('gemini' or 'openai')

**Data Updates**:
- Converts old 'bot' message types to 'chat' for Q&A interactions

**When to Run**:
- When implementing dual-model response system
- Safe to run multiple times (has existence checks)

**Usage**:
```bash
python migrations/add_openai_response.py
```

---

### 3. `add_evaluation_table.py`
**Purpose**: Creates the ChatbotEvaluation table for quality assessment

**Table Created**: `chatbot_evaluation`

**When to Run**:
- After initial database setup if the evaluation feature is needed
- Safe to run multiple times

**Usage**:
```bash
python migrations/add_evaluation_table.py
```

---

### 4. `add_evaluator_name.py`
**Purpose**: Adds evaluator name column to the evaluation table

**Column Added**:
- `evaluator_name` (VARCHAR(100)) - Name of the medical staff member who performed the evaluation

**When to Run**:
- After creating the evaluation table
- When upgrading the evaluation system

**Usage**:
```bash
python migrations/add_evaluator_name.py
```

---

## Migration Best Practices

### For Fresh Installation
If you're setting up a fresh database, you don't need to run these migrations. Simply use:

```bash
python init_db.py
```

This will create all tables with the latest schema using `db.create_all()`.

---

### For Existing Database Upgrade
If you have an existing database and want to upgrade to the latest schema:

1. **Backup your database first!**
   ```bash
   # For SQLite (local development)
   cp patients.db patients.db.backup

   # For MySQL/Cloud SQL
   # Use your cloud provider's backup tools or mysqldump
   ```

2. **Run migrations in order** (only run migrations for features you don't have):
   ```bash
   # Check which columns exist in your database first
   python check_database.py

   # Then run only the migrations you need:
   python migrations/add_feedback_fields.py
   python migrations/add_openai_response.py
   python migrations/add_evaluation_table.py
   python migrations/add_evaluator_name.py
   ```

---

### For Linux Deployment

When deploying to a Linux server:

1. **Fresh installation**:
   ```bash
   python3 init_db.py
   python3 create_admin.py
   ```

2. **Migrating existing data**:
   - Restore your database backup
   - Run necessary migrations based on your current schema
   - Verify with `python3 check_database.py`

---

## Safety Features

All migration scripts include:
- **Existence checks**: Scripts check if columns/tables already exist before creating them
- **Idempotent operations**: Safe to run multiple times without errors
- **Environment detection**: Automatically work with both SQLite (local) and MySQL (cloud)

---

## Database Schema Reference

For the complete current database schema, see `models.py` in the root directory.

### Core Tables:
1. **Patient** - Patient demographics and medical information
2. **ChatHistory** - Conversation records with AI responses
3. **SelfPayItem** - Medical service cost information
4. **ChatbotEvaluation** - Quality assessments by medical staff
5. **User** - Admin authentication

---

## Troubleshooting

### "Column already exists" Error
This is normal and means the migration has already been applied. You can safely ignore this message.

### "Table doesn't exist" Error
Run `python init_db.py` first to create the base tables.

### Database Connection Error
- Check your `.env` file has correct database credentials
- For local development, ensure `USE_LOCAL_MODEL` is set appropriately
- For cloud deployment, verify Cloud SQL instance is running

---

## Creating New Migrations

If you need to add new columns or tables:

1. **Update `models.py`** with the new schema
2. **Create a migration script** in this folder following the naming pattern: `add_<feature_name>.py`
3. **Use the template structure**:
   ```python
   from flask import Flask
   from sqlalchemy import text
   import sys, os
   from dotenv import load_dotenv

   sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   from models import db

   load_dotenv()

   def create_app():
       # App initialization code
       pass

   def add_your_feature():
       app = create_app()
       with app.app_context():
           # Check if column/table exists
           # Add column/table if needed
           db.session.commit()

   if __name__ == '__main__':
       add_your_feature()
   ```

4. **Test locally** before running on production
5. **Update this README** with documentation for your migration

---

## Questions?

For more information about the database schema and system architecture, see:
- `/CLAUDE.md` - Project reference and development guidelines
- `/README.md` - General project documentation
- `/DEPLOYMENT.md` - Deployment instructions
