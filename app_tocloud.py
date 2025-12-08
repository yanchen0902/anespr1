from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime, timedelta
import json
import openai
import os
import requests
from dotenv import load_dotenv
from markdown import markdown
import bleach
import logging
import secrets
import uuid
import re
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Patient, SelfPayItem, ChatHistory, login_manager, init_db, ChatbotEvaluation
from sqlalchemy import text, func
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Ensure proper UTF-8 handling
app.config['DEBUG'] = True  # Enable debug mode
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Force templates to reload
app.secret_key = 'anespr1-secret-key'

# Initialize database
init_db(app)

# Create database tables if they don't exist
with app.app_context():
    try:
        # Create tables without dropping existing ones
        db.create_all()
        logger.info("Database tables checked/created")
        
        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("Created default admin user")
        else:
            logger.info("Admin user already exists")
    except Exception as e:
        logger.error(f"Error checking database: {str(e)}")
        raise
    
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def _initialize_session_vars():
    """Helper function to initialize or repair session variables"""
    logger.info(f"[_initialize_session_vars] Entry. Session before init: {dict(session)}")
    user_id_created = False
    if 'user_id' not in session:
        session['user_id'] = uuid.uuid4().hex
        user_id_created = True
        logger.info(f"New user session initialized with user_id: {session['user_id']}")

    # Ensure the user-specific dictionary exists in the session
    user_specific_session_key = session['user_id'] 
    if user_specific_session_key not in session or not isinstance(session[user_specific_session_key], dict):
        session[user_specific_session_key] = {}
        session.modified = True

    # Initialize or repair current_step and patient_info
    if user_id_created or 'current_step' not in session[user_specific_session_key]:
        session[user_specific_session_key]['current_step'] = 'initial'
        session.modified = True
        logger.info(f"Set current_step to 'initial' for user_id: {session['user_id']}")

    if 'patient_info' not in session[user_specific_session_key]:
        session[user_specific_session_key]['patient_info'] = {}
        session.modified = True

    session.modified = True  # Ensure all changes are marked
    logger.info(f"[_initialize_session_vars] Exit. Session after init: {dict(session)}")

@app.before_request
def make_session_permanent():
    logger.info(f"[make_session_permanent] Entry. Session before mods: {dict(session)}")
    session.permanent = True
    _initialize_session_vars()  # Call the helper function
    logger.info(f"[make_session_permanent] Exit. Session after mods: {dict(session)}")
    # Log request information for debugging (optional, can be verbose)
    # logger.info(f"Request from IP: {request.remote_addr}, Session ID: {session.get('_id', 'No ID')}, User ID: {session['user_id']}")
    # logger.info(f"Current session data for user {session['user_id']}: {session[user_specific_session_key]}")

# 問題流程 - Preserved from original app_tocloud2.py
# questions = {
#     "name": "您好！我是您的麻醉諮詢助手。為了提供您最適合的建議，請讓我先了解一些基本資訊。請問您的大名是？",
#     "age": "請問您的年齡是？",
#     "sex": "請問您的性別是？",
#     "cfs": "您是否能夠自行外出，不需要他人協助？（是/否）",
#     "medical_history": "請問您有什麼重要的病史嗎？例如：高血壓、糖尿病、心臟病等。如果沒有，請回答「無」",
#     "operation": "請問您預計要進行什麼手術？",
#     "worry": "您最擔心什麼？您可以點選或輸入您的擔憂。如果沒有特別擔心的，請點選「沒有特別擔心」。"
# }



def utc_now():
    """Get current UTC time"""
    return datetime.utcnow()

def to_local_time(utc_dt):
    """Convert UTC datetime to local time (Taipei)"""
    if utc_dt is None:
        return None
    if utc_dt.tzinfo is None:  # Make sure it's UTC
        utc_dt = pytz.UTC.localize(utc_dt)
    taipei_tz = pytz.timezone('Asia/Taipei')
    return utc_dt.astimezone(taipei_tz)

def format_local_time(utc_dt, format='%Y-%m-%d %H:%M'):
    """Convert UTC datetime to local time and format it"""
    local_dt = to_local_time(utc_dt)
    if local_dt is None:
        return ''
    return local_dt.strftime(format)

def save_chat_history(patient_id, message, response, message_type='chat'):
    """Save chat history to database"""
    try:
        # Validate message type
        if message_type not in ['chat', 'user', 'bot', 'summary']:
            raise ValueError(f"Invalid message type: {message_type}")
            
        # Log the save attempt for debugging
        logger.info(f"Saving chat history: patient_id={patient_id}, type={message_type}")
        if message:
            logger.info(f"Message size: {len(message)} characters")
            logger.info(f"Message preview: {message[:100]}...")
        if response:
            logger.info(f"Response size: {len(response)} characters")
            logger.info(f"Response preview: {response[:100]}...")
            
        # Create chat history entry
        chat_entry = ChatHistory(
            patient_id=patient_id,
            message=message,
            response=response,
            message_type=message_type,
            created_at=datetime.utcnow()
        )
        
        # Add and commit to database
        try:
            db.session.add(chat_entry)
            db.session.commit()
            logger.info(f"Chat history saved successfully")
        except Exception as e:
            logger.error(f"Database error saving chat history: {str(e)}", exc_info=True)
            db.session.rollback()
            raise
            
    except Exception as e:
        logger.error(f"Error in save_chat_history: {str(e)}", exc_info=True)
        raise

def create_or_find_patient(name):
    """Create a new patient"""
    try:
        # Create new patient
        patient = Patient(name=name)
        db.session.add(patient)
        db.session.commit()
        logger.info(f"Created new patient: {patient.id}")
        return patient
        
    except Exception as e:
        logger.error(f"Error in create_or_find_patient: {str(e)}", exc_info=True)
        db.session.rollback()
        return None

def handle_patient_info(user_id, step, message):
    """Handle patient information collection steps"""
    try:
        # Initialize info dict if not exists
        if 'patient_info' not in session[user_id]:
            session[user_id]['patient_info'] = {}
        info = session[user_id]['patient_info']
        
        # Handle each step
        if step == 'initial':
            if not message:
                return "請問您的姓名是？"
            
            info['name'] = message
            session[user_id]['current_step'] = 'age'
            session.modified = True
            return "好的，接下來請問您的年齡是？"
            
        elif step == 'age':
            try:
                age = int(message)
                if age < 0 or age > 150:
                    return "請輸入有效的年齡（0-150歲之間）"
                info['age'] = age
                session[user_id]['current_step'] = 'sex'
                session.modified = True
                return "您的性別是？（男/女）"
            except ValueError:
                return "請輸入有效的年齡數字"
            
        elif step == 'sex':
            if message not in ['男', '女']:
                return "請選擇性別（男/女）"
            info['sex'] = message
            session[user_id]['current_step'] = 'cfs'
            session.modified = True
            return "您可以自行外出嗎？（是/否）"
            
        elif step == 'cfs':
            if message not in ['是', '否']:
                return "請選擇是否可以自行外出（是/否）"
            info['cfs'] = message
            session[user_id]['current_step'] = 'operation'
            session.modified = True
            return "請問您預計進行什麼手術？（若手術部位為選項之外請輸入手術名稱）"
            
        elif step == 'operation':
            info['operation'] = message
            session[user_id]['current_step'] = 'medical_history'
            session.modified = True
            return "請問您有什麼慢性病史嗎？(可複選，若不在選項之中，請輸入文字)"
            
        elif step == 'medical_history':
            info['medical_history'] = message
            session[user_id]['current_step'] = 'worry'
            session.modified = True
            return "關於麻醉，您最擔心什麼？"
            
        elif step == 'worry':
            info['worry'] = message
            
            # Create or find patient in database
            try:
                patient = create_or_find_patient(info['name'])
                if not patient:
                    raise Exception("無法建立或找到病患資料")
                
                # Update patient info
                patient.age = info['age']
                patient.sex = info['sex']
                patient.operation = info['operation']
                patient.cfs = info['cfs']
                patient.medical_history = info['medical_history']
                patient.worry = info['worry']
                
                try:
                    db.session.commit()
                    logger.info(f"Patient info updated for {patient.id}")
                except Exception as e:
                    logger.error(f"Error updating patient info: {str(e)}", exc_info=True)
                    db.session.rollback()
                    raise
                
                # Store patient_id in session
                session[f'patient_id_{user_id}'] = patient.id
                
                # Update session state
                session[user_id]['current_step'] = 'chat'
                session.modified = True
                
                # Generate and save summary
                summary = generate_summary(info)
                save_chat_history(patient.id, None, summary, 'summary')
                
                return f"{summary}\n\n您有任何關於麻醉的問題嗎？"
                
            except Exception as e:
                logger.error(f"Error saving patient data: {str(e)}", exc_info=True)
                db.session.rollback()
                raise
            
        else:
            raise ValueError(f"Invalid step: {step}")
            
    except Exception as e:
        logger.error(f"Error in handle_patient_info: {str(e)}", exc_info=True)
        raise

def generate_summary(info):
    """Generate a summary of patient information"""
    summary = "<h2>您提供的資訊摘要</h2>"
    summary += "<ul>"
    summary += f"<li><strong>姓名</strong>：{info.get('name', '未知')}</li>"
    summary += f"<li><strong>年齡</strong>：{info.get('age', '未知')}歲</li>"
    summary += f"<li><strong>性別</strong>：{info.get('sex', '未知')}</li>"
    summary += f"<li><strong>預定手術</strong>：{info.get('operation', '未知')}</li>"
    
    cfs = "可以自行外出" if info.get('cfs') == "是" else "需要他人協助"
    summary += f"<li><strong>行動能力</strong>：{cfs}</li>"
    
    medical_history = info.get('medical_history', '無')
    if medical_history in ["沒有", "無"]:
        medical_history = "無特殊病史"
    summary += f"<li><strong>病史</strong>：{medical_history}</li>"
    
    worry = info.get('worry', '無特殊擔憂')
    if worry in ["沒有", "無"]:
        worry = "無特殊擔憂"
    summary += f"<li><strong>擔憂</strong>：{worry}</li>"
    summary += "</ul>"

    
    # Add trigger text for showing question buttons
    summary += "<p>您好！我已經了解您的基本資料了。請問您有什麼關於麻醉的問題嗎？</p>"
    
    return summary




def get_bot_response(message, patient_info):
    """Get response from Azure OpenAI model"""
    try:
        # Get patient_id from session
        user_id = patient_info.get('user_id')
        if not user_id:
            logger.error("No user ID provided in patient_info")
            return "抱歉，系統發生錯誤。請重新開始對話。"

        patient_id = session.get(f'patient_id_{user_id}')
        if not patient_id:
            logger.error(f"No patient_id found in session for user_id: {user_id}")
            return "抱歉，系統發生錯誤。請重新開始對話。"

        # Get response from Azure OpenAI
        logger.info("Using Azure OpenAI model")
        response_text = get_openai_response(message, patient_info)

        if response_text and not response_text.startswith("抱歉"):
            # Return the response with follow-up prompt
            return f"{response_text}\n\n您還有其他關於麻醉的問題嗎？"
        else:
            logger.error("Failed to get response from Azure OpenAI model")
            return "抱歉，我現在無法回答您的問題。請稍後再試。"

    except Exception as e:
        logger.error(f"Error in get_bot_response: {str(e)}", exc_info=True)
        return "抱歉，系統發生錯誤。請稍後再試。"

def format_response(response):
    """Convert response to HTML with markdown formatting"""
    try:
        # Normalize line endings and ensure proper spacing
        response = response.replace('\r\n', '\n').replace('\r', '\n')

        # Clean up excessive newlines
        response = re.sub(r'\n\s*\n\s*\n', '\n\n', response)  # Replace 3+ newlines with 2

        # Fix spacing after colons before actual lists
        response = re.sub(r'([：:])\s*\n\s*([*-]\s+\S)', r'\1\n\2', response)

        # Remove blank lines between list items (prevents extra spacing in bullet points)
        response = re.sub(r'([-*]\s+[^\n]+)\n\s*\n([-*]\s+)', r'\1\n\2', response)

        # Convert markdown to HTML
        html = markdown(response)

        # Clean HTML output
        allowed_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'em',
                       'ul', 'ol', 'li', 'code', 'pre', 'blockquote', 'a', 'br']
        allowed_attributes = {'a': ['href', 'title']}
        html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attributes)

        # Clean up HTML spacing
        html = re.sub(r'>\s+<', '><', html)  # Remove whitespace between tags
        html = re.sub(r'<p>\s+', '<p>', html)  # Remove leading whitespace in paragraphs
        html = re.sub(r'\s+</p>', '</p>', html)  # Remove trailing whitespace in paragraphs
        html = re.sub(r'<li>\s+', '<li>', html)  # Remove leading whitespace in list items
        html = re.sub(r'\s+</li>', '</li>', html)  # Remove trailing whitespace in list items

        # Remove newlines between list tags to prevent <br> insertion by frontend
        html = re.sub(r'</li>\s*\n\s*<li>', '</li><li>', html)  # Remove newlines between list items
        html = re.sub(r'<ul>\s*\n\s*<li>', '<ul><li>', html)  # Remove newline after <ul>
        html = re.sub(r'</li>\s*\n\s*</ul>', '</li></ul>', html)  # Remove newline before </ul>
        html = re.sub(r'<ol>\s*\n\s*<li>', '<ol><li>', html)  # Remove newline after <ol>
        html = re.sub(r'</li>\s*\n\s*</ol>', '</li></ol>', html)  # Remove newline before </ol>

        # Remove <p> tags inside <li> elements (prevents extra spacing in list items)
        # This is the main cause of extra spacing - markdown package wraps list content in <p> tags
        html = re.sub(r'<li>\s*<p>(.*?)</p>\s*</li>', r'<li>\1</li>', html, flags=re.DOTALL)

        # Also handle cases where <p> is nested in <li> with other content
        html = re.sub(r'<li><p>', '<li>', html)
        html = re.sub(r'</p></li>', '</li>', html)

        # DEBUG: Log the final HTML output
        logger.info(f"=== FINAL HTML OUTPUT ===")
        logger.info(f"HTML length: {len(html)}")
        logger.info(f"HTML content:\n{html}")
        logger.info(f"HTML repr:\n{repr(html)}")
        logger.info("=" * 50)

        return html
    except Exception as e:
        logger.error(f"Error formatting response: {str(e)}", exc_info=True)
        return response  # Return original text if formatting fails

# Import from our prompt templates module
from prompt_templates import get_question_type

# Import from our prompt templates module
from prompt_templates import get_surgery_type

def create_context(message, patient_info):
    """Create context for Gemini model with patient info and message"""
    # Import our get_prompt function which handles all template logic
    from prompt_templates import get_prompt
    
    # Get the appropriate prompt using the prompt templates module
    return get_prompt(message, patient_info)


# Initialize Azure OpenAI API
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')

if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME]):
    logger.error("Azure OpenAI configuration incomplete. Required: API_KEY, ENDPOINT, DEPLOYMENT_NAME")
    azure_openai_client = None
else:
    logger.info(f"Azure OpenAI configuration loaded: {AZURE_OPENAI_API_KEY[:5]}...{AZURE_OPENAI_API_KEY[-4:]}")
    logger.info(f"Azure OpenAI endpoint: {AZURE_OPENAI_ENDPOINT}")
    logger.info(f"Azure OpenAI deployment: {AZURE_OPENAI_DEPLOYMENT_NAME}")
    
    try:
        from openai import AzureOpenAI
        azure_openai_client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        logger.info("Azure OpenAI client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
        azure_openai_client = None

def get_openai_response(message, patient_info):
    """Get response from Azure OpenAI model"""
    try:
        if not azure_openai_client:
            logger.error("Azure OpenAI client not initialized")
            return "抱歉，Azure OpenAI 服務未設定。"
            
        # Use separated prompts for Azure OpenAI
        from prompt_templates import get_separated_prompts
        system_prompt, user_prompt = get_separated_prompts(message, patient_info)

        # Log the exact prompts being sent
        logger.info("=== AZURE OPENAI SYSTEM PROMPT ===")
        logger.info(system_prompt)
        logger.info("=== AZURE OPENAI USER PROMPT ===")
        logger.info(user_prompt)
        logger.info("=== SENDING REQUEST TO AZURE OPENAI ===")

        # Also print to console for immediate visibility
        print("\n" + "="*50)
        print("SYSTEM PROMPT:")
        print(system_prompt)
        print("\n" + "="*50)
        print("USER PROMPT:")
        print(user_prompt)
        print("="*50 + "\n")

        logger.info("Sending request to Azure OpenAI...")
        
        response = azure_openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,  # This is the deployment name, not model name
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_completion_tokens=2000
        )
        logger.info("Received response from Azure OpenAI")

        # Debug: Log the full response structure
        logger.info(f"Response object: {response}")
        logger.info(f"Response type: {type(response)}")

        if not response:
            logger.error("Response is None")
            return "抱歉，Azure OpenAI 回應為空。"

        if not hasattr(response, 'choices'):
            logger.error(f"Response has no 'choices' attribute. Available attributes: {dir(response)}")
            return "抱歉，Azure OpenAI 回應格式錯誤。"

        if not response.choices:
            logger.error("Response choices is empty")
            return "抱歉，Azure OpenAI 回應選項為空。"

        logger.info(f"Response choices count: {len(response.choices)}")
        logger.info(f"First choice: {response.choices[0]}")

        if not hasattr(response.choices[0], 'message'):
            logger.error("First choice has no message attribute")
            return "抱歉，Azure OpenAI 回應訊息格式錯誤。"

        content = response.choices[0].message.content
        logger.info(f"Response content: {content}")

        return format_response(content)
    except Exception as e:
        logger.error(f"Error getting Azure OpenAI response: {str(e)}", exc_info=True)
        return f"抱歉，Azure OpenAI 回應出現錯誤：{str(e)}"

@app.route('/')
def home():
    """Reset session and start fresh (unless coming from EMR confirmation)"""
    logger.info(f"[home] Entry. Session before clear: {dict(session)}")

    # Check if we should skip clearing session (coming from EMR confirmation)
    skip_clear = session.get('skip_clear', False)

    if skip_clear:
        logger.info(f"[home] Skipping session clear (EMR confirmation flow)")
        session.pop('skip_clear', None)  # Remove the flag
        session.modified = True
    else:
        session.clear()
        logger.info(f"[home] Session after clear: {dict(session)}")
    
    # IMPORTANT: Explicitly initialize session variables after clearing
    _initialize_session_vars()
    logger.info(f"[home] Session after _initialize_session_vars: {dict(session)}")
    
    # Now we can safely retrieve user_id and current_step
    user_id_to_pass = session.get('user_id')

    current_step_to_pass = 'initial' # Default, should be overridden
    
    if user_id_to_pass and user_id_to_pass in session and isinstance(session.get(user_id_to_pass), dict):
        current_step_to_pass = session[user_id_to_pass].get('current_step', 'initial')
    else:
        logger.warning(f"Home route: user_id '{user_id_to_pass}' not found in session or its entry is not a dict after explicit initialization. Session state: {dict(session)}")

    logger.info(f"[home] Passing to template: user_id='{user_id_to_pass}', server_current_step='{current_step_to_pass}'")
    return render_template('index.html', 
                           user_id=user_id_to_pass, 
                           server_current_step=current_step_to_pass)

# Mock EMR data - replace with actual API integration later
def get_patient_by_national_id(national_id):
    """
    Mock function to simulate EMR data retrieval by National ID (身分證字號)
    In production, this will connect to the hospital's EMR system
    """
    # Mock patient data - only one patient for testing
    if national_id.upper() == 'A123456789':
        return {
            'national_id': 'A123456789',
            'patient_id': 'P2025001234',  # Hospital internal patient ID
            'name': '王小明',
            'gender': '男',
            'age': 45,
            'birth_date': '1979-03-15',
            'phone': '0912-345-678',
            'blood_type': 'A型RH+',
            'surgery_type': '腹腔鏡膽囊切除術',
            'surgery_date': '2025-10-05',
            'surgeon': '陳醫師',
            'ward': '5A病房',
            'medical_history': '高血壓、糖尿病',
            'allergies': '無已知藥物過敏',
            'current_medications': '降血壓藥物、血糖控制藥物'
        }

    return None

@app.route('/patient_id', methods=['GET', 'POST'])
def patient_id_input():
    """
    National ID (身分證字號) input page for EMR integration
    """
    logger.info(f"[patient_id_input] Entry. Method: {request.method}")

    if request.method == 'POST':
        national_id = request.form.get('patient_id', '').strip().upper()
        logger.info(f"[patient_id_input] Received national_id: {national_id}")

        # Validate National ID format (Taiwan ID format)
        if not re.match(r'^[A-Z][1-2][0-9]{8}$', national_id):
            logger.warning(f"[patient_id_input] Invalid format: {national_id}")
            return render_template('patient_id_input.html',
                                 error='身分證字號格式不正確，請重新輸入')

        # Try to get patient data by National ID
        patient_data = get_patient_by_national_id(national_id)
        logger.info(f"[patient_id_input] Patient data found: {patient_data is not None}")

        if not patient_data:
            logger.warning(f"[patient_id_input] No patient found for ID: {national_id}")
            return render_template('patient_id_input.html',
                                 error='查無此患者資料，請確認身分證字號是否正確')

        # Store patient data in session
        session['emr_patient_data'] = patient_data
        session.modified = True
        logger.info(f"[patient_id_input] Patient data stored in session")

        # Redirect to patient info display page
        return redirect(url_for('patient_emr_info'))

    logger.info(f"[patient_id_input] Rendering GET page")
    return render_template('patient_id_input.html')

@app.route('/patient_info')
def patient_emr_info():
    """
    Display patient information from EMR
    """
    patient_data = session.get('emr_patient_data')

    if not patient_data:
        flash('請先輸入身分證字號查詢患者資料', 'error')
        return redirect(url_for('patient_id_input'))

    # Transform old mock data format to new EMR snapshot schema
    # TODO: Remove this transformation when get_patient_by_national_id() uses emr_integration.py
    from datetime import datetime

    emr_data = {
        'schema_version': '1.0.0',
        'source': 'mock_emr',
        'fetched_at': datetime.now().isoformat(),
        'confirmed_at': None,
        'confirmed_by_patient': False,

        'patient_demographics': {
            'medical_record_number': patient_data.get('patient_id', ''),
            'id_number': patient_data.get('national_id', ''),
            'patient_name': patient_data.get('name', ''),
            'date_of_birth': patient_data.get('birth_date', ''),
            'age': patient_data.get('age', 0),
            'gender': patient_data.get('gender', ''),
            'blood_type': patient_data.get('blood_type', '')
        },

        'surgery_info': {
            'surgery_date': patient_data.get('surgery_date', ''),
            'surgery_time': '',
            'surgery_name': patient_data.get('surgery_type', ''),
            'surgery_name_en': '',
            'attending_surgeon': patient_data.get('surgeon', ''),
            'department': '',
            'preop_diagnosis': '',
            'anesthesia_type': ''
        },

        'vital_signs': {
            'height': '175 cm',
            'weight': '70 kg',
            'bmi': '22.86',
            'temperature': '36.5 °C',
            'heart_rate': '72 bpm',
            'blood_pressure': '120/80 mmHg',
            'respiratory_rate': '16 bpm',
            'spo2': '98%'
        },

        'medical_history': {
            'allergies': [patient_data.get('allergies', '')],
            'medications': [patient_data.get('current_medications', '')],
            'past_surgeries': [],
            'chronic_conditions': [patient_data.get('medical_history', '')],
            'notes': ''
        }
    }

    return render_template('patient_emr_info.html', emr_data=emr_data)

@app.route('/confirm_emr_data', methods=['POST'])
def confirm_emr_data():
    """
    Patient confirms EMR data and saves snapshot to ChatHistory
    Then redirects to chatbot consultation
    """
    import json
    from datetime import datetime

    logger.info("[confirm_emr_data] Entry")

    # Get EMR data from session
    patient_data = session.get('emr_patient_data')

    if not patient_data:
        flash('請先輸入身分證字號查詢患者資料', 'error')
        return redirect(url_for('patient_id_input'))

    # Transform to EMR snapshot format
    emr_snapshot = {
        'schema_version': '1.0.0',
        'source': 'mock_emr',
        'fetched_at': datetime.now().isoformat(),
        'confirmed_at': datetime.now().isoformat(),
        'confirmed_by_patient': True,

        'patient_demographics': {
            'medical_record_number': patient_data.get('patient_id', ''),
            'id_number': patient_data.get('national_id', ''),
            'patient_name': patient_data.get('name', ''),
            'date_of_birth': patient_data.get('birth_date', ''),
            'age': patient_data.get('age', 0),
            'gender': patient_data.get('gender', ''),
            'blood_type': patient_data.get('blood_type', '')
        },

        'surgery_info': {
            'surgery_date': patient_data.get('surgery_date', ''),
            'surgery_time': '',
            'surgery_name': patient_data.get('surgery_type', ''),
            'surgery_name_en': '',
            'attending_surgeon': patient_data.get('surgeon', ''),
            'department': '',
            'preop_diagnosis': '',
            'anesthesia_type': ''
        },

        'vital_signs': {
            'height': '175 cm',
            'weight': '70 kg',
            'bmi': '22.86',
            'temperature': '36.5 °C',
            'heart_rate': '72 bpm',
            'blood_pressure': '120/80 mmHg',
            'respiratory_rate': '16 bpm',
            'spo2': '98%'
        },

        'medical_history': {
            'allergies': [patient_data.get('allergies', '')],
            'medications': [patient_data.get('current_medications', '')],
            'past_surgeries': [],
            'chronic_conditions': [patient_data.get('medical_history', '')],
            'notes': ''
        }
    }

    # Create or get patient record
    # For now, create a new patient record based on EMR data
    try:
        patient = Patient(
            name=emr_snapshot['patient_demographics']['patient_name'],
            age=emr_snapshot['patient_demographics']['age'],
            sex=emr_snapshot['patient_demographics']['gender'],
            operation=emr_snapshot['surgery_info']['surgery_name'],
            medical_history=', '.join(emr_snapshot['medical_history']['chronic_conditions']),
            worry='',  # Will be filled during consultation
            cfs=''  # Will be filled during consultation
        )
        db.session.add(patient)
        db.session.flush()  # Get patient.id without committing

        # Save EMR snapshot to ChatHistory
        emr_chat = ChatHistory(
            patient_id=patient.id,
            message_type='emr_snapshot',
            message=json.dumps(emr_snapshot, ensure_ascii=False),
            response=None
        )
        db.session.add(emr_chat)
        db.session.commit()

        logger.info(f"[confirm_emr_data] Created patient {patient.id} and saved EMR snapshot")

        # Initialize session for chatbot with patient_id
        _initialize_session_vars()

        user_id = session.get('user_id')
        session['patient_id'] = patient.id
        session['emr_confirmed'] = True

        # Set up chatbot session state
        # Skip name, age, sex, operation questions since we have them from EMR
        # Start directly at CFS (Clinical Frailty Scale) question
        if user_id and user_id in session:
            session[user_id]['current_step'] = 'cfs'  # Start at CFS instead of 'initial'
            session[user_id]['patient_info'] = {
                'name': emr_snapshot['patient_demographics']['patient_name'],
                'age': emr_snapshot['patient_demographics']['age'],
                'sex': emr_snapshot['patient_demographics']['gender'],
                'operation': emr_snapshot['surgery_info']['surgery_name']
            }
            session[user_id]['emr_data'] = emr_snapshot  # Store full EMR data for chatbot to use

        session.modified = True

        # Redirect to home page (chatbot)
        # Note: We set a flag so home() doesn't clear our session
        session['skip_clear'] = True
        session.modified = True

        logger.info(f"[confirm_emr_data] Redirecting to chatbot with patient_id={patient.id}")
        return redirect(url_for('home'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"[confirm_emr_data] Error saving EMR data: {str(e)}")
        flash('儲存資料時發生錯誤，請稍後再試', 'error')
        return redirect(url_for('patient_emr_info'))

@app.route('/reset_session', methods=['POST'])
def reset_session():
    """API endpoint to reset session and start fresh"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', '')
        
        if not user_id:
            return jsonify({'error': 'Missing user ID'}), 400
            
        # Clear specific user session data
        if user_id in session:
            del session[user_id]
        if f'patient_id_{user_id}' in session:
            del session[f'patient_id_{user_id}']
        
        # Initialize fresh session state
        session[user_id] = {
            'current_step': 'initial',
            'patient_info': {},
            'summary_shown': False
        }
        session.modified = True
        
        # Return initial question
        return jsonify({
            'status': 'success',
            'response': questions['name']
        })
        
    except Exception as e:
        logger.error(f"Error in reset_session: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    logger.info(f"[chat] Entry. Full session data: {dict(session)}")
    client_user_id = request.get_json().get('user_id') # Get client_user_id early for logging
    logger.info(f"[chat] Client sent user_id: {client_user_id}")
    logger.info(f"[chat] Server session['user_id']: {session.get('user_id')}")
    if client_user_id and client_user_id in session and isinstance(session.get(client_user_id), dict):
        logger.info(f"[chat] Server session[client_user_id]['current_step']: {session[client_user_id].get('current_step')}")
    elif client_user_id:
        logger.warning(f"[chat] Client user_id '{client_user_id}' not found as a dict key in server session.")
    else:
        logger.warning("[chat] Client did not send a user_id or it was None.")

    try:
        data = request.get_json()
        user_id = data.get('user_id')
        message = data.get('message', '')

        if not user_id:
            return jsonify({'error': 'Missing user ID'}), 400

        # Initialize session data if not exists
        if user_id not in session:
            session[user_id] = {'current_step': 'initial', 'patient_info': {}}

        # Get current step
        current_step = session[user_id].get('current_step', 'initial')
        
        # Get patient_id from session
        patient_id = session.get(f'patient_id_{user_id}')
        if not patient_id and current_step == 'chat':
            return jsonify({'error': 'No patient ID found in session'}), 400
        
        # Handle patient info collection
        if current_step != 'chat':
            try:
                response = handle_patient_info(user_id, current_step, message)
                # Save form flow messages with user/bot type only during form flow
                if patient_id and current_step != 'chat':
                    try:
                        db.session.begin_nested()  # Create savepoint
                        save_chat_history(patient_id, message, None, 'user')
                        save_chat_history(patient_id, None, response, 'bot')
                        db.session.commit()
                        logger.info(f"Form flow messages saved for patient {patient_id}")
                    except Exception as e:
                        logger.error(f"Error saving form flow messages: {str(e)}", exc_info=True)
                        db.session.rollback()
                return jsonify({'response': response})
            except Exception as e:
                logger.error(f"Error in handle_patient_info: {str(e)}", exc_info=True)
                return jsonify({'error': str(e)}), 500
        
        # Handle chat mode
        try:
            # Get patient info from session
            patient_info = session[user_id].get('patient_info', {})
            if not patient_info:
                return jsonify({'error': 'Missing patient info'}), 400
            
            # Add user_id to patient_info for chat history
            patient_info['user_id'] = user_id
            
            # Get response from Azure OpenAI only
            azure_response = get_bot_response(message, patient_info)
            
            # Save chat history - SIMPLIFIED VERSION
            try:
                # Log details before saving
                logger.info(f"Attempting to save chat entry - Details:")
                logger.info(f"Patient ID: {patient_id}")
                logger.info(f"Message: {message[:50]}...")
                logger.info(f"Azure response: {azure_response[:50]}...")

                # Create the chat history entry
                chat = ChatHistory(
                    patient_id=patient_id,
                    message=message,
                    response=azure_response,
                    message_type='chat',
                    created_at=datetime.utcnow()  # Explicitly set timestamp
                )
                
                # Important: Add and commit in separate steps with verification
                db.session.add(chat)
                db.session.flush()  # Get the ID without committing
                chat_id = chat.id
                logger.info(f"Chat entry flushed with ID: {chat_id}")
                
                # Now commit to finalize the transaction
                db.session.commit()
                logger.info(f"💾 Chat history committed to database, ID={chat_id}")
                
                # Verify the entry exists in a NEW session to confirm persistence
                with db.session.no_autoflush:
                    verification = db.session.query(ChatHistory).get(chat_id)
                    if verification:
                        logger.info(f"✅ Verified chat entry exists in database: ID={chat_id}")
                    else:
                        logger.error(f"❌ Could not verify chat entry: ID={chat_id}")
                
            except Exception as e:
                logger.error(f"❌ Error saving chat history: {str(e)}", exc_info=True)
                db.session.rollback()
                # Do not re-raise the exception to prevent cascading failures
            
            return jsonify({'response': azure_response})
            
        except Exception as e:
            logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/self_pay')
def self_pay():
    """Display self-pay items page"""
    user_id = request.args.get('user_id')
    if not user_id:
        return "請從諮詢系統進入自費項目表", 400
    
    # Get patient_id from session using the new format
    patient_id_key = f'patient_id_{user_id}'
    
    # Log session data for debugging
    logger.info(f"Session data in self_pay: {dict(session)}")
    logger.info(f"Looking for patient_id with key: {patient_id_key}")
    
    # Check if patient_id exists in session
    if patient_id_key not in session:
        return "找不到病人資料，請重新開始諮詢", 400
    
    patient_id = session[patient_id_key]
    logger.info(f"Found patient_id: {patient_id}")
    
    try:
        # Fetch patient info from database
        patient = Patient.query.get(patient_id)
        if not patient:
            logger.error(f"Patient with ID {patient_id} not found in database")
            return "找不到病人資料，請重新開始諮詢", 400
        
        patient_info = {
            'name': patient.name,
            'age': patient.age,
            'sex': patient.sex,
            'operation': patient.operation,
            'cfs': patient.cfs,
            'worry': patient.worry
        }
        
        items = SelfPayItem.query.all()
        return render_template('self_pay_form.html', items=items, patient_info=patient_info, user_id=user_id)
    
    except Exception as e:
        logger.error(f"Error in self_pay: {str(e)}")
        return "發生錯誤，請重新開始諮詢", 500

@app.route('/submit_self_pay', methods=['POST'])
def submit_self_pay():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "無效的資料格式"}), 400
            
        selected_items = data.get('items', [])
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({"error": "請從諮詢系統進入自費項目表"}), 400
            
        patient_id = session.get(f'patient_id_{user_id}')
        if not patient_id:
            return jsonify({"error": "請先完成諮詢再選擇自費項目"}), 404
            
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({"error": "找不到病人資料"}), 404
            
        try:
            # Delete existing items for this patient only
            SelfPayItem.query.filter_by(patient_id=patient_id).delete()
            
            # Save new items
            for item_name in selected_items:
                price = {
                    '麻醉深度監測': 1711,
                    '最適肌張力手術輔助處置': 6500,
                    '自控式止痛': 6500,
                    '溫毯': 980,
                    '止吐藥': 99,
                    '腦血氧貼片': 15000
                }.get(item_name)
                
                if price is not None:
                    item = SelfPayItem(
                        patient_id=patient_id,
                        item_name=item_name,
                        price=price,
                        selected_at=utc_now()  # Use the new UTC function
                    )
                    db.session.add(item)
            save_chat_history(
                patient_id=patient_id,
                message="自費項目選擇完成",
                response="感謝您完成諮詢，您可以在管理介面查看完整諮詢記錄。",
                message_type='chat'
            )
            
            db.session.commit()
            # Store success in session for the summary page
            session['self_pay_success'] = True
            return jsonify({
                "success": True,
                "redirect_url": url_for('consultation_summary', patient_id=patient_id)
            })
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error saving self-pay items: {str(e)}")
            return jsonify({"error": "儲存失敗，請稍後再試"}), 500
            
    except Exception as e:
        app.logger.error(f"Error in submit_self_pay: {str(e)}")
        return jsonify({"error": "系統錯誤，請稍後再試"}), 500

@app.route('/consultation_summary/<int:patient_id>')
def consultation_summary(patient_id):
    try:
        patient = Patient.query.get_or_404(patient_id)
        
        # Get chat history with type='chat' (Q&A only, not form flow)
        chat_history = ChatHistory.query.filter(
            ChatHistory.patient_id == patient_id,
            ChatHistory.message_type == 'chat'  # Only actual Q&A, not form flow messages
        ).order_by(ChatHistory.created_at.asc()).all()
        
        # Format responses as HTML if they're not already
        for entry in chat_history:
            if entry.response and not entry.response.startswith('<'):
                entry.response = format_response(entry.response)
        
        # Get self-pay items
        self_pay_items = SelfPayItem.query.filter_by(
            patient_id=patient_id
        ).order_by(SelfPayItem.selected_at.desc()).all()
        
        total_price = sum(item.price for item in self_pay_items)
        
        # Log data for debugging
        app.logger.info(f"Patient: {patient.name}")
        app.logger.info(f"Chat history count: {len(chat_history)}")
        app.logger.info(f"Self-pay items count: {len(self_pay_items)}")
        app.logger.info(f"Total price: {total_price}")
        
        return render_template(
            'consultation_summary.html',
            patient=patient,
            chat_history=chat_history,
            self_pay_items=self_pay_items,
            total_price=total_price,
            consultation_date=utc_now(),
            format_local_time=format_local_time  # Pass the formatter function to template
        )
    except Exception as e:
        app.logger.error(f"Error in consultation_summary: {str(e)}")
        flash('無法載入諮詢總結，請稍後再試', 'error')
        return redirect(url_for('index'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Handle admin login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            logger.info(f"Admin login successful: {username}")
            return redirect(url_for('admin_dashboard'))
            
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Display admin dashboard"""
    try:
        # Get all patients with basic info
        patients = Patient.query.order_by(Patient.created_at.desc()).all()
        total_patients = len(patients)
        
        # Get statistics for Q&A interactions and consultations
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Count recent patients
        recent_patients = Patient.query.filter(
            Patient.created_at >= week_ago
        ).count()
        
        # Count chat interactions
        total_qa_interactions = ChatHistory.query.filter(
            ChatHistory.message_type == 'chat'
        ).count()
        
        recent_qa_interactions = ChatHistory.query.filter(
            ChatHistory.message_type == 'chat',
            ChatHistory.created_at >= week_ago
        ).count()
        
        # Count total consultations (summaries)
        total_consultations = ChatHistory.query.filter(
            ChatHistory.message_type == 'summary'
        ).count()
        
        return render_template(
            'admin_dashboard.html',
            patients=patients,
            total_patients=total_patients,
            total_qa_interactions=total_qa_interactions,
            total_consultations=total_consultations,
            recent_patients=recent_patients,
            recent_qa_interactions=recent_qa_interactions,
            format_local_time=format_local_time
        )
    except Exception as e:
        logger.error(f"Error in admin dashboard: {str(e)}", exc_info=True)
        flash('Error loading dashboard data', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/logout')
@login_required
def admin_logout():
    """Handle admin logout"""
    logout_user()
    flash('Successfully logged out')
    return redirect(url_for('admin_login'))

@app.route('/admin/patient/<int:id>')
@login_required
def patient_detail(id):
    """Display patient details"""
    try:
        patient = Patient.query.get_or_404(id)
        
        # Get chat history with proper type filtering
        chat_history = ChatHistory.query.filter(
            ChatHistory.patient_id == id,
            (
                # Get actual Q&A interactions
                (ChatHistory.message_type == 'chat') |
                # Get form flow messages
                (ChatHistory.message_type.in_(['user', 'bot', 'summary']))
            )
        ).order_by(ChatHistory.created_at).all()
        
        # Format responses as HTML if they're not already
        for entry in chat_history:
            if entry.message_type == 'chat' and entry.response and not entry.response.startswith('<'):
                entry.response = format_response(entry.response)
        
        # Group form flow messages by timestamp for better display
        grouped_history = []
        current_group = None
        
        for entry in chat_history:
            if entry.message_type == 'chat':
                # Q&A interactions are shown as is
                grouped_history.append(entry)
            elif entry.message_type in ['user', 'bot']:
                # Group form flow messages that are close in time
                timestamp = entry.created_at
                if (current_group is None or 
                    (timestamp - current_group['timestamp']).total_seconds() > 5):
                    current_group = {
                        'timestamp': timestamp,
                        'messages': [],
                        'type': 'form_flow'
                    }
                    grouped_history.append(current_group)
                current_group['messages'].append(entry)
            else:  # summary
                # Summary is shown as is
                grouped_history.append(entry)
        
        return render_template(
            'patient_detail.html',
            patient=patient,
            chat_history=grouped_history,
            format_local_time=format_local_time,
            now=datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')  # Add timestamp to force reload
        )
    except Exception as e:
        logger.error(f"Error viewing patient details: {str(e)}", exc_info=True)
        flash('Error loading patient details', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/feedback/<int:chat_id>', methods=['POST'])
@login_required
def submit_feedback(chat_id):
    try:
        feedback = request.form.get('feedback')
        if feedback not in ['like', 'dislike', 'ban']:
            return jsonify({'status': 'error', 'message': 'Invalid feedback type'}), 400

        chat = ChatHistory.query.get(chat_id)
        if not chat:
            return jsonify({'status': 'error', 'message': 'Chat not found'}), 404

        chat.feedback = feedback
        chat.feedback_at = datetime.now()
        db.session.commit()

        return jsonify({'status': 'success'})
    except Exception as e:
        app.logger.error(f"Error submitting feedback: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/chat/prefer-response', methods=['POST'])
@login_required
def prefer_response():
    try:
        chat_id = request.form.get('chat_id')
        model = request.form.get('model')
        
        if not chat_id or not model:
            return jsonify({'status': 'error', 'message': 'Missing chat_id or model'}), 400
            
        if model not in ['gemini', 'openai']:
            return jsonify({'status': 'error', 'message': 'Invalid model'}), 400

        chat = ChatHistory.query.get(chat_id)
        if not chat:
            return jsonify({'status': 'error', 'message': 'Chat not found'}), 404

        chat.preferred_response = model
        chat.preferred_at = datetime.now()  # Add timestamp
        db.session.commit()
        
        app.logger.info(f"Set preferred response for chat {chat_id} to {model}")
        return jsonify({'status': 'success'})
    except Exception as e:
        app.logger.error(f"Error setting preferred response: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/feedback_stats')
@login_required
def feedback_stats():
    try:
        # Get overall feedback counts
        feedback_counts = db.session.query(
            ChatHistory.feedback, 
            func.count(ChatHistory.id)
        ).filter(
            ChatHistory.feedback.isnot(None),
            ChatHistory.message_type == 'chat'  # Only count Q&A interactions
        ).group_by(
            ChatHistory.feedback
        ).all()
        
        # Format the counts for display
        feedback_counts_dict = {
            'like': 0,
            'dislike': 0,
            'ban': 0,
            'total': 0
        }
        
        for feedback, count in feedback_counts:
            if feedback in feedback_counts_dict:
                feedback_counts_dict[feedback] = count
                feedback_counts_dict['total'] += count
        
        # Calculate feedback percentages
        if feedback_counts_dict['total'] > 0:
            feedback_counts_dict['like_percent'] = round((feedback_counts_dict['like'] / feedback_counts_dict['total']) * 100, 1)
            feedback_counts_dict['dislike_percent'] = round((feedback_counts_dict['dislike'] / feedback_counts_dict['total']) * 100, 1)
            feedback_counts_dict['ban_percent'] = round((feedback_counts_dict['ban'] / feedback_counts_dict['total']) * 100, 1)
        else:
            feedback_counts_dict['like_percent'] = 0
            feedback_counts_dict['dislike_percent'] = 0
            feedback_counts_dict['ban_percent'] = 0
        
        # Get detailed feedback data
        feedback_data = db.session.query(
            ChatHistory.id,
            Patient.id.label('patient_id'),
            Patient.name.label('patient_name'),
            ChatHistory.feedback,
            ChatHistory.preferred_response,
            ChatHistory.message
        ).join(
            Patient, ChatHistory.patient_id == Patient.id
        ).filter(
            ChatHistory.message_type == 'chat'
        ).order_by(
            ChatHistory.created_at.desc()
        ).all()
        
        # Get evaluation data keyed by patient_id
        evaluations = {}
        # Get evaluation data with evaluator names
        eval_results = db.session.query(
            ChatbotEvaluation.patient_id,
            func.avg(ChatbotEvaluation.accuracy_score).label('avg_accuracy'),
            func.avg(ChatbotEvaluation.trustworthiness_score).label('avg_trust'),
            func.avg(ChatbotEvaluation.empathy_score).label('avg_empathy'),
            func.group_concat(ChatbotEvaluation.evaluator_name.distinct()).label('evaluators')
        ).group_by(
            ChatbotEvaluation.patient_id
        ).all()
        
        for result in eval_results:
            evaluations[result.patient_id] = {
                'accuracy': round(result.avg_accuracy, 1) if result.avg_accuracy else 'N/A',
                'trust': round(result.avg_trust, 1) if result.avg_trust else 'N/A',
                'empathy': round(result.avg_empathy, 1) if result.avg_empathy else 'N/A',
                'evaluators': result.evaluators.split(',') if result.evaluators else []
            }
        
        return render_template(
            'feedback_stats.html',
            counts=feedback_counts_dict,
            feedback_data=feedback_data,
            evaluations=evaluations
        )
    except Exception as e:
        logger.error(f"Error viewing feedback stats: {str(e)}", exc_info=True)
        flash('Error loading feedback statistics', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/patient/<int:id>/evaluate', methods=['POST'])
def evaluate_chatbot(id):
    try:
        patient = Patient.query.get_or_404(id)
        evaluation = ChatbotEvaluation(
            patient_id=id,
            evaluated_by=current_user.id,
            evaluator_name=request.form.get('evaluator_name'),
            accuracy_score=int(request.form['accuracy']),
            trustworthiness_score=int(request.form['trustworthiness']),
            empathy_score=int(request.form['empathy']),
            comments=request.form.get('comments')
        )
        db.session.add(evaluation)
        db.session.commit()
        flash('評估已成功提交', 'success')
    except Exception as e:
        app.logger.error(f"Error submitting evaluation: {str(e)}")
        flash('提交評估時發生錯誤', 'error')
        db.session.rollback()
    
    return redirect(url_for('patient_detail', id=id))



@app.route('/greeting')
def greeting():
    """Display the greeting page with general surgery information"""
    return render_template('greeting.html')

@app.route('/hospital_admission')
def hospital_admission():
    """住院報到相關問題"""
    return render_template('hospital_admission.html')

@app.route('/surgery_time')
def surgery_time():
    """手術時間相關問題"""
    return render_template('surgery_time.html')

@app.route('/pre_surgery_medication')
def pre_surgery_medication():
    """術前藥物相關問題"""
    return render_template('pre_surgery_medication.html')

@app.route('/anesthesia_safety')
def anesthesia_safety():
    """麻醉安全介紹"""
    return render_template('anesthesia_safety.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), debug=True)
