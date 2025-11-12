# CLAUDE.md - Project Reference

## Project Overview
**Anesthesiology Pre-Consultation Chatbot System**
- Healthcare application for pre-surgical anesthesia consultation
- Collects patient information through structured dialogue
- Provides AI-powered medical guidance using Gemini and Ollama models
- Includes admin dashboard for healthcare professionals

## Key Files & Structure

### Main Application
- `app_tocloud.py` - Main Flask application with all routes and logic
- `models.py` - Database models (Patient, ChatHistory, SelfPayItem, ChatbotEvaluation, User)
- `prompt_templates.py` - AI prompt templates for different medical scenarios
- `requirements.txt` - Python dependencies
- `patients.db` - Local SQLite database (development)

### Templates Directory
- `templates/index.html` - Main patient interface
- `templates/admin_dashboard.html` - Admin management interface
- `templates/patient_detail.html` - Individual patient consultation view
- `templates/consultation_summary.html` - Patient consultation summary
- `templates/self_pay_form.html` - Medical service cost selection
- `templates/feedback_stats.html` - Response quality statistics
- `templates/login.html` - Admin login page
- Additional info pages: `greeting.html`, `hospital_admission.html`, etc.

## Environment Configuration

### Required Environment Variables (.env file)
```env
GOOGLE_API_KEY=your_gemini_api_key
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
USE_LOCAL_MODEL=false
OLLAMA_URL=http://192.168.226.162:11434
OLLAMA_MODEL=gemma3:latest
```

### Local Development Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python app_tocloud.py

# Database initialization (if needed)
python init_db.py

# Create admin user (if needed)
python create_admin.py
```

### Testing Commands
```bash
# Check if tests exist
find . -name "*test*" -type f

# Check package.json for test scripts
cat package.json 2>/dev/null || echo "No package.json found"

# Check for common Python test runners
python -m pytest --version 2>/dev/null || echo "pytest not available"
python -m unittest --version 2>/dev/null || echo "unittest available (built-in)"
```

## Database Schema

### Core Tables
1. **Patient** - Demographics, surgery type, medical history
2. **ChatHistory** - Conversation records with message types:
   - `chat` - Q&A interactions
   - `user`/`bot` - Form flow messages  
   - `summary` - Patient information summary
3. **SelfPayItem** - Medical service costs and selections
4. **ChatbotEvaluation** - Quality assessments by medical staff
5. **User** - Admin authentication

### Database Configuration
- **Production**: Cloud SQL (MySQL) on Google App Engine
- **Development**: SQLite (patients.db)
- **Connection**: Handles both local SQLite and Cloud SQL automatically

## Key Features & Functionality

### Patient Flow
1. **Information Collection**: Name, age, gender, surgery type, medical history, concerns
2. **AI Consultation**: Natural language Q&A using Gemini/Ollama
3. **Self-Pay Selection**: Optional medical service cost calculator
4. **Summary Generation**: Complete consultation report

### Admin Features
1. **Dashboard**: Patient list with statistics
2. **Patient Details**: Full conversation history and evaluation
3. **Response Evaluation**: Rate AI responses (accuracy, trustworthiness, empathy)
4. **Feedback System**: Like/dislike/ban responses
5. **Statistics**: Feedback analytics and evaluation summaries

### AI Integration
- **Primary**: Google Gemini 2.0 Flash
- **Fallback**: Local Ollama (Gemma3) model
- **Prompts**: Medical context-aware templates
- **Safety**: Content filtering and medical appropriateness

## Development Notes

### Session Management
- User-specific session storage with UUID
- Patient ID linking across sessions
- Session repair mechanisms for robustness

### Error Handling
- Comprehensive logging with context
- Database rollback on failures
- User-friendly error messages
- Debug mode for development

### Security Considerations
- Admin authentication required for management
- Password hashing for admin accounts
- Input sanitization and validation
- Medical data privacy compliance

## Deployment Information

### Google Cloud App Engine
- Project: anespr1-asia-east
- Cloud SQL Instance: anespr1-asia-east:asia-east1:anespr1
- Connection: mysql+pymysql://root:anespr123@/patients?unix_socket=/cloudsql/anespr1-asia-east:asia-east1:anespr1

### Local Development
- Host: 0.0.0.0
- Port: 8080 (configurable via PORT env var)
- Debug mode enabled in development

## Common Tasks

### Adding New Surgery Types
1. Update surgery selection options in templates
2. Modify prompt templates for new surgery context
3. Test AI responses for accuracy

### Database Migrations
1. Update models.py
2. Use Flask-Migrate or manual SQL updates
3. Test locally before deploying

### AI Model Updates
1. Update generation_config in app_tocloud.py
2. Test response quality
3. Update prompt templates if needed

### Admin Management
1. Default admin: username=admin, password=admin123
2. Create additional admins via database or script
3. Manage user permissions as needed

## Monitoring & Maintenance

### Key Metrics
- Patient consultation count
- AI response quality ratings
- Error rates and types
- Database performance

### Regular Tasks
- Review AI response feedback
- Update medical knowledge in prompts
- Monitor API usage and costs
- Database backup and maintenance

## Recent Updates

### 2025-10-22: Linux Deployment Preparation (Git: c2af0af)
- **Documentation Overhaul**: Complete rewrite of project documentation for Linux deployment handoff
  - **README.md**: Comprehensive bilingual (Chinese/English) documentation
    - Clear file categorization: Linux Essential vs Optional vs Google Cloud only
    - Step-by-step Linux deployment guide with systemd service example
    - Environment configuration with `.env.linux` template
    - FAQ section covering common deployment issues
    - Security considerations and best practices
  - **migrations/README.md**: Database migration documentation
    - Detailed guide for each migration script
    - Clear distinction: fresh install vs upgrading existing database
    - Safety features and troubleshooting

- **File Cleanup**: Removed redundant files for cleaner codebase
  - Deleted `templates/admin.html` (duplicate of `admin_dashboard.html`)
  - Deleted `add_feedback_columns.py` (duplicate of `migrations/add_feedback_fields.py`)

- **Deployment Clarity**: Key distinctions for Linux engineers
  - ✅ Use `init_db.py` for fresh installation (NOT migrations folder)
  - ✅ Use `create_admin.py` for Linux (NOT `create_admin_cloud.py`)
  - ❌ Ignore Google Cloud files: `app.yaml`, `setup_mysql.py`, `.gcloudignore`
  - ⚠️ `migrations/` folder only needed for upgrading existing databases

- **Quick Start Guide**: 5-step deployment process
  ```bash
  python3 -m venv venv && source venv/bin/activate
  pip install -r requirements.linux.txt
  cp .env.linux .env  # Fill in API keys
  python3 init_db.py
  python3 create_admin.py
  gunicorn -w 4 -b 0.0.0.0:8080 app_tocloud:app
  ```

**Benefits**:
- Clear separation of Linux vs Google Cloud deployment paths
- Reduced confusion with redundant files removed
- Engineer-friendly documentation with step-by-step instructions
- Production-ready with systemd service configuration
- No ambiguity about which scripts to run for fresh installation

---

### 2025-09-21: Model Toggle System Enhancement (Git: cca2ec2)
- **Dual Model Response System**: System now always calls both primary model (Ollama/Gemini) and Azure OpenAI
  - **Primary Model**: Controlled by `USE_LOCAL_MODEL` environment variable
  - **Azure OpenAI**: Always called and responses saved to database
  - **Database Storage**: Both responses stored in `ChatHistory` table (`response` and `openai_response` fields)

- **Model Switching Configuration**:
  ```env
  # For Gemini + Azure OpenAI
  USE_LOCAL_MODEL=False

  # For Ollama + Azure OpenAI
  USE_LOCAL_MODEL=True
  ```

- **Important**: No spaces around the `=` sign in `.env` file to avoid parsing issues

- **Code Changes**:
  - Fixed `USE_LOCAL_MODEL` logic in `app_tocloud.py:29`
  - Updated chat endpoint to always call Azure OpenAI (`app_tocloud.py:703-707`)
  - Renamed variables for clarity: `gemini_response` → `primary_response`

**Benefits**:
- Flexibility to switch between local Ollama and cloud Gemini models
- Always maintain Azure OpenAI responses for comparison and backup
- Consistent data collection for model evaluation and improvement
- Easy environment-based model switching without code changes

### 2025-01-29: Azure OpenAI Prompt Structure Optimization
- **Enhanced Prompt Architecture**: Implemented separated system and user prompts for Azure OpenAI integration
  - **System Prompt**: Contains age-appropriate medical guidelines + surgery-specific protocols (Part 1 + Part 3)
  - **User Prompt**: Contains patient information + question-specific guidance + actual question (Part 2 + Part 4)
- **New Function**: Added `get_separated_prompts()` in `prompt_templates.py:410-448`
  - Returns tuple: `(system_prompt, user_prompt)`
  - Maintains backward compatibility with existing `get_prompt()` function
- **Updated Azure OpenAI Integration**: Modified `get_openai_response()` in `app_tocloud.py:557-565`
  - Now uses proper role separation for better context understanding
  - Improved prompt structure for more accurate medical responses
- **Configuration Update**: Azure OpenAI API version updated to `2024-12-01-preview`

**Benefits**:
- Better context separation for Azure OpenAI models
- Improved response quality through proper role-based prompting
- Maintains compatibility with existing Gemini/Ollama implementations
- Centralized prompt logic in `prompt_templates.py` module

---

### 2025-10-22: EMR Integration Placeholder Structure (Future Feature)
- **EMR Integration Framework**: Complete placeholder structure for future hospital EMR system integration
  - **Patient Access**: National ID (身份證字號) lookup instead of QR code
  - **Data Flow**: ID entry → EMR data fetch → Patient confirmation → Chatbot consultation (starts at CFS)
  - **Hybrid Storage**: EMR data saved as JSON snapshot in `ChatHistory` (no schema changes needed)

- **New Files Created**:
  - **`emr_schema.py`**: Standardized JSON schema for EMR snapshots
    - Complete data structure: patient demographics, surgery info, vital signs, medical history
    - Validation functions and example data
    - Version: 1.0.0

  - **`emr_integration.py`**: EMR API integration module
    - `fetch_patient_from_emr(id_number, use_mock=True)`: Main entry point
    - Mock data implementation (currently active)
    - Placeholder for real EMR API integration
    - Error handling: `PatientNotFoundError`, `EMRAPIError`
    - Data transformation layer ready for hospital API mapping

  - **`EMR_INTEGRATION_GUIDE.md`**: Comprehensive implementation documentation
    - Patient flow diagrams
    - Step-by-step integration guide
    - Security considerations
    - Questions for hospital IT department

- **Modified Files**:
  - **`models.py`**: ChatHistory model updated
    - `message_type` expanded from `String(10)` to `String(20)`
    - Added 'emr_snapshot' as valid message type
    - **Fresh installations**: `init_db.py` creates correct schema automatically
    - **Existing databases**: Run `migrations/expand_message_type_for_emr.py` if upgrading

  - **`templates/patient_emr_info.html`**: Dynamic EMR data display
    - Removed EVAN branding
    - Full Jinja2 template integration for all fields
    - Editable vital signs fields with pencil icons
    - Confirmation button added: "確認資料並開始諮詢"

  - **`app_tocloud.py`**: New routes and session flow
    - `/patient_id` (existing): National ID lookup form
    - `/patient_info` (modified): Display EMR data with transformation layer
    - `/confirm_emr_data` (new): Save EMR snapshot and create Patient record
    - Session flow: Skips basic questions, starts at CFS step
    - Home route modified: Preserves session when coming from EMR confirmation

- **EMR Snapshot Structure** (stored in ChatHistory.message as JSON):
```json
{
  "schema_version": "1.0.0",
  "source": "hospital_emr",
  "fetched_at": "ISO datetime",
  "confirmed_at": "ISO datetime",
  "confirmed_by_patient": true,
  "patient_demographics": {
    "medical_record_number": "M1234567",
    "id_number": "A123456789",
    "patient_name": "王大明",
    "date_of_birth": "1978/05/20",
    "age": 45,
    "gender": "男",
    "blood_type": "O+"
  },
  "surgery_info": {
    "surgery_date": "2023/11/15",
    "surgery_time": "08:00",
    "surgery_name": "闌尾切除術",
    "attending_surgeon": "陳醫師",
    "department": "一般外科",
    "preop_diagnosis": "急性闌尾炎",
    "anesthesia_type": "全身麻醉"
  },
  "vital_signs": {
    "height": "175 cm",
    "weight": "70 kg",
    "bmi": "22.86",
    "temperature": "36.5 °C",
    "heart_rate": "72 bpm",
    "blood_pressure": "120/80 mmHg",
    "respiratory_rate": "16 bpm",
    "spo2": "98%"
  },
  "medical_history": {
    "allergies": ["青黴素"],
    "medications": ["降血壓藥"],
    "past_surgeries": [],
    "chronic_conditions": ["高血壓"],
    "notes": ""
  }
}
```

- **Patient Flow** (Complete):
```
1. Patient visits /patient_id
   ↓
2. Enters National ID: A123456789
   ↓
3. System fetches EMR data (currently mock, will be real API)
   ↓
4. Display patient_emr_info.html with all data
   ↓
5. Patient reviews and clicks confirmation button
   ↓
6. Creates Patient record in database
   ↓
7. Saves EMR snapshot to ChatHistory (message_type='emr_snapshot')
   ↓
8. Sets session: current_step='cfs' (skips name/age/sex/operation)
   ↓
9. Redirects to chatbot starting at CFS question
```

- **Testing** (Mock Data Available):
  - Visit: `http://localhost:8080/patient_id`
  - Enter National ID: `A123456789`
  - Mock patient "王小明" data will be displayed
  - Click confirmation to test full flow

- **Environment Variables** (for future real EMR integration):
```env
EMR_API_URL=https://hospital-emr.example.com/api
EMR_API_KEY=your_api_key_here
EMR_API_TIMEOUT=30
```

- **Switching to Real EMR API**:
  1. Configure environment variables
  2. Implement `_fetch_real_patient_data()` in `emr_integration.py`
  3. Implement `_transform_emr_data()` to map hospital EMR fields
  4. Change `use_mock=True` to `use_mock=False`

**Benefits**:
- ✅ No database schema changes needed (uses existing ChatHistory table)
- ✅ Complete audit trail via EMR snapshot JSON
- ✅ Easy to switch between mock and real EMR API
- ✅ Skips redundant questions (name, age, gender, surgery)
- ✅ Full EMR data available for AI prompts (future enhancement)
- ✅ Professional patient experience with pre-filled data
- ✅ Maintains separation between core patient data and EMR snapshots

**Status**: Placeholder structure complete and functional with mock data
**Next Steps**: Pending real hospital EMR API integration

---

## Contact & Support
- System designed for medical professionals
- Requires medical domain expertise for prompt updates
- Healthcare compliance considerations apply