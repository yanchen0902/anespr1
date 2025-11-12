# anespr1_linux_deployment.zip - Package Contents

**Created**: 2025-10-22
**Purpose**: Linux deployment package (excludes migrations and Google Cloud files)

---

## What's Included ✅

### Python Application Files (13)
- ✅ `app_tocloud.py` - Main Flask application
- ✅ `models.py` - Database models
- ✅ `prompt_templates.py` - AI prompt templates
- ✅ `emr_integration.py` - EMR API integration module (NEW)
- ✅ `emr_schema.py` - EMR data schema (NEW)
- ✅ `init_db.py` - Database initialization (for fresh install)
- ✅ `create_admin.py` - Create admin user (for Linux)
- ✅ `create_admin_cloud.py` - Cloud admin creation script
- ✅ `check_database.py` - Database verification tool
- ✅ `update_schema.py` - Schema update utility
- ✅ `test_login.py` - Login testing script
- ✅ `test_ollama_gemma.py` - Model testing script
- ✅ `serve_flowchart.py` - Flowchart server

### Documentation (6)
- ✅ `README.md` - Comprehensive deployment guide (bilingual)
- ✅ `CLAUDE.md` - Project reference and history
- ✅ `DEPLOYMENT.md` - Deployment instructions
- ✅ `EMR_INTEGRATION_GUIDE.md` - EMR integration documentation (NEW)
- ✅ `EMR_DATABASE_CHANGES.md` - Database changes explanation (NEW)
- ✅ `flowchart.md` - System flowchart documentation

### Configuration Files (6)
- ✅ `.env.example` - Example environment variables
- ✅ `.env.linux` - Linux environment template
- ✅ `app.yaml.example` - Example App Engine config (for reference)
- ✅ `requirements.txt` - Python dependencies (full)
- ✅ `requirements.linux.txt` - Linux-specific dependencies
- ✅ `.gitignore` - Git ignore rules

### Templates (16 HTML files)
- ✅ `templates/index.html` - Main chatbot interface
- ✅ `templates/patient_id_input.html` - National ID lookup (NEW)
- ✅ `templates/patient_emr_info.html` - EMR data display (UPDATED)
- ✅ `templates/admin_dashboard.html` - Admin panel
- ✅ `templates/patient_detail.html` - Patient details view
- ✅ `templates/consultation_summary.html` - Consultation summary
- ✅ `templates/login.html` - Admin login
- ✅ `templates/feedback_stats.html` - Statistics page
- ✅ `templates/self_pay_form.html` - Cost selection
- ✅ `templates/greeting.html` - Welcome page
- ✅ `templates/hospital_admission.html` - Admission info
- ✅ `templates/anesthesia_safety.html` - Safety info
- ✅ `templates/pre_surgery_medication.html` - Medication info
- ✅ `templates/surgery_time.html` - Surgery timing info
- ✅ `templates/debug_database.html` - Debug tools

### Static Assets (4 files)
- ✅ `static/css/style.css` - Stylesheet
- ✅ `static/js/chat.js` - Chat interface JavaScript
- ✅ `static/images/greeting.jpg` - Greeting image
- ✅ `static/images/refresh-icon.svg` - Refresh icon

### Other Files
- ✅ `anespr1.code-workspace` - VS Code workspace
- ✅ `flowchart.html` - Interactive flowchart
- ✅ `database.db` - Empty SQLite database template

---

## What's Excluded ❌

### Migrations Folder
❌ `migrations/` - Database migration scripts (not needed for fresh install)
- Use `init_db.py` for fresh installations
- Migrations only needed for upgrading existing databases

### Google Cloud Files
❌ `app.yaml` - Google App Engine configuration
❌ `setup_mysql.py` - Cloud SQL setup script
❌ `.gcloudignore` - Google Cloud ignore rules

### Development Files
❌ `__pycache__/` - Python cache
❌ `venv/`, `venv39/` - Virtual environments
❌ `.git/` - Git repository
❌ `.vscode/` - VS Code settings
❌ `patients.db` - Development database with data
❌ `.env` - Local environment variables (secret)
❌ `*.pyc` - Compiled Python files

---

## Quick Start on Linux

### 1. Extract the zip file
```bash
unzip anespr1_linux_deployment.zip -d /opt/anespr1
cd /opt/anespr1
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.linux.txt
```

### 4. Configure environment
```bash
cp .env.linux .env
nano .env  # Edit with your API keys
```

### 5. Initialize database
```bash
python3 init_db.py
```

### 6. Create admin user
```bash
python3 create_admin.py
```

### 7. Run the application
```bash
# Development
python3 app_tocloud.py

# Production (recommended)
gunicorn -w 4 -b 0.0.0.0:8080 app_tocloud:app
```

---

## EMR Integration (New Feature)

### Test EMR Flow
1. Visit: `http://your-server:8080/patient_id`
2. Enter National ID: `A123456789` (test data)
3. Review EMR data displayed
4. Click confirmation button
5. Chatbot starts at CFS question (skips name/age/gender/surgery)

### Switch to Real EMR API
1. Configure environment variables:
   ```env
   EMR_API_URL=https://hospital-emr.example.com/api
   EMR_API_KEY=your_api_key
   ```
2. Edit `emr_integration.py`:
   - Implement `_fetch_real_patient_data()`
   - Implement `_transform_emr_data()`
   - Change `use_mock=True` to `use_mock=False`

### Documentation
- See `EMR_INTEGRATION_GUIDE.md` for complete implementation guide
- See `EMR_DATABASE_CHANGES.md` for database schema details

---

## File Size
- **Total files**: 49
- **Package size**: ~2-3 MB (compressed)

---

## Verification

### Check Package Contents
```bash
unzip -l anespr1_linux_deployment.zip | head -20
```

### Verify Exclusions
```bash
# Should return nothing:
unzip -l anespr1_linux_deployment.zip | grep migrations
unzip -l anespr1_linux_deployment.zip | grep app.yaml
unzip -l anespr1_linux_deployment.zip | grep setup_mysql.py
```

### Verify Inclusions
```bash
# Should list the files:
unzip -l anespr1_linux_deployment.zip | grep emr_integration.py
unzip -l anespr1_linux_deployment.zip | grep emr_schema.py
unzip -l anespr1_linux_deployment.zip | grep EMR_INTEGRATION_GUIDE.md
```

---

## Notes

1. **Fresh Installation**: Use `init_db.py` (NOT migrations)
2. **Admin Creation**: Use `create_admin.py` on Linux
3. **Environment**: Copy `.env.linux` to `.env` and configure
4. **Dependencies**: Use `requirements.linux.txt` for Linux
5. **EMR Feature**: Ready to use with mock data, switch to real API when ready

---

## Support

- **Documentation**: See `README.md` for full deployment guide
- **Project History**: See `CLAUDE.md` for all updates
- **EMR Integration**: See `EMR_INTEGRATION_GUIDE.md`

---

**Package Created**: 2025-10-22
**Location**: `C:\Users\memor\OneDrive\主治行政相關\anespr1\anespr1_linux_deployment.zip`
