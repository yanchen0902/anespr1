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

### Branch Structure
- **main/evaluation_mode**: Development branches for Windows environment
- **linux-deployment**: Production deployment branch for Linux servers
  - Contains Linux-specific configurations
  - MySQL database setup instead of SQLite
  - Production environment variables
  - Nginx/Gunicorn configuration files

### Google Cloud App Engine (Legacy)
- Project: anespr1-asia-east
- Cloud SQL Instance: anespr1-asia-east:asia-east1:anespr1
- Connection: mysql+pymysql://root:anespr123@/patients?unix_socket=/cloudsql/anespr1-asia-east:anespr1

### Linux Server Deployment
- **Database**: MySQL 8.0+ (production), SQLite (development only)
- **Web Server**: Nginx with SSL/TLS
- **WSGI Server**: Gunicorn with 4 workers
- **Process Manager**: Supervisor for service management
- **Host**: 0.0.0.0 (production), configurable
- **Port**: 8000 (Gunicorn), 80/443 (Nginx)
- **Environment**: Production mode with comprehensive logging

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

### 2025-09-06: Linux Deployment Branch Setup
- **Branch Management**: Created `linux-deployment` branch for production deployment
  - Separated from development branches (`evaluation_mode`, `main`)
  - Dedicated to Linux server deployment configurations
  - Safe environment for major deployment-related changes
- **Deployment Documentation**: Added comprehensive `DEPLOYMENT.md` guide
  - Complete Linux server setup instructions
  - MySQL database configuration
  - Nginx/Gunicorn/Supervisor setup
  - Security hardening and SSL configuration
  - Monitoring and maintenance procedures

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

## Contact & Support
- System designed for medical professionals
- Requires medical domain expertise for prompt updates
- Healthcare compliance considerations apply
- This is the future plan
- laeve as-is for now and fix when production