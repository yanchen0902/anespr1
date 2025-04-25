from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime, timedelta
import json
import google.generativeai as genai
import openai
import os
from dotenv import load_dotenv
from markdown import markdown
import bleach
import logging
import secrets
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

@app.before_request
def make_session_permanent():
    session.permanent = True
    # Initialize user_id in session if not exists
    if 'user_id' not in session:
        session['user_id'] = str(datetime.utcnow().timestamp())
        session.modified = True
        logger.info(f"New user session initialized with ID: {session['user_id']}")
    
    # Log request information for debugging
    logger.info(f"Request from IP: {request.remote_addr}")
    logger.info(f"Session ID: {session.get('_id', 'No ID')}")
    logger.info(f"User ID: {session.get('user_id', 'No user_id')}")
    logger.info(f"Current session data: {dict(session)}")

# 問題流程 - Preserved from original app_tocloud2.py
questions = {
    "name": "您好！我是您的麻醉諮詢助手。為了提供您最適合的建議，請讓我先了解一些基本資訊。請問您的大名是？",
    "age": "請問您的年齡是？",
    "sex": "請問您的性別是？",
    "cfs": "您是否能夠自行外出，不需要他人協助？（是/否）",
    "medical_history": "請問您有什麼重要的病史嗎？例如：高血壓、糖尿病、心臟病等。如果沒有，請回答「無」",
    "operation": "請問您預計要進行什麼手術？",
    "worry": "您最擔心什麼？您可以點選或輸入您的擔憂。如果沒有特別擔心的，請點選「沒有特別擔心」。"
}



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
            return "請問您有什麼慢性病史嗎？(可複選，若不在選項之種，請輸入文字)"
            
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
    """Get response from Gemini model"""
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
        
        # Create context and get response from model
        context = create_context(message, patient_info)
        model = get_gemini_model()
        response = model.generate_content(context)
        
        if response and response.text:
            # Format the response first
            formatted_response = format_response(response.text)
            
            # Return the response with follow-up prompt
            return f"{formatted_response}\n\n您還有其他關於麻醉的問題嗎？"
        else:
            logger.error("Empty response from model")
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
        
        return html
    except Exception as e:
        logger.error(f"Error formatting response: {str(e)}", exc_info=True)
        return response  # Return original text if formatting fails

def get_question_type(message):
    """Determine the type of question based on keywords"""
    message = message.lower()
    
    anesthesia_keywords = ['類型', '全身', '局部', '半身', '無痛', '清醒', '睡著']
    preparation_keywords = ['準備', '禁食', '藥物', '注意', '戒菸', '抽菸', '吃藥']
    risk_keywords = ['風險', '危險', '併發症', '副作用', '死亡', '意外', '醒來', '恢復']
    self_pay_keywords = ['自費', '費用', '價格', '多少錢', '監測', '溫毯', '止吐']
    
    if any(keyword in message for keyword in anesthesia_keywords):
        return 'anesthesia'
    elif any(keyword in message for keyword in preparation_keywords):
        return 'preparation'
    elif any(keyword in message for keyword in risk_keywords):
        return 'risk'
    elif any(keyword in message for keyword in self_pay_keywords):
        return 'self_pay'
    else:
        return 'general'

def create_context(message, patient_info):
    """Create context for Gemini model with patient info and message"""
    question_type = get_question_type(message)
    
    # Base patient info section
    patient_info_section = f"""### 病人資訊:
姓名：{patient_info.get('name', '未知')}
年齡：{patient_info.get('age', '未知')}
性別：{patient_info.get('sex', '未知')}
手術：{patient_info.get('operation', '未知')}
行動：{patient_info.get('cfs', '未評估')}
病史：{patient_info.get('medical_history', '無')}
擔憂：{patient_info.get('worry', '無')}"""

    # Different prompts for different question types
    prompts = {
        'anesthesia': f"""## Role: 麻醉諮詢助手
### 回答原則:
- 使用繁體中文，簡潔明瞭，盡量在200字以內
- 專注於麻醉方式說明
- 適當使用emoji說明過程
- 除了下肢手術、剖腹產、泌尿科手術，其餘不考慮半身麻醉

### 回答重點:
- 建議的麻醉類型及原因
- 麻醉過程簡要說明
- 術中可能的感受

{patient_info_section}

問題: {message}""",

        'preparation': f"""## Role: 麻醉諮詢助手
### 回答原則:
- 使用繁體中文，簡潔明瞭，盡量在200字以內
- 重點式條列說明
- 使用emoji強調重要事項
- 除了下肢手術、剖腹產、泌尿科手術，其餘不考慮半身麻醉

### 術前準備重點:
- 禁食要求（固體8小時、清水2小時）
- 需要停用的藥物(抗凝血藥物、糖尿病藥物)
- 戒菸、運動
- 個人化注意事項

{patient_info_section}

問題: {message}""",

        'risk': f"""## Role: 麻醉諮詢助手
### 回答原則:
- 使用繁體中文，清楚說明，盡量在200字以內
- 針對個人情況分析
- 使用emoji緩和說明氣氛
- 除了下肢手術、剖腹產、泌尿科手術，其餘不考慮半身麻醉

### 風險評估重點:
- 根據年齡和病史評估ASA等級
- 衰弱者 ASA等級為3以上
- 心臟手術者ASA等級為4
- 可能發生的併發症
- 如何降低風險：
  * 解釋如何透過自費項目降低風險：
     * 麻醉深度監測：降低術中知曉風險
     * 最適肌張力：降低肌肉鬆弛劑相關併發症
     * 體溫監測與保溫：降低低體溫併發症
     * 止吐藥物：降低噁心嘔吐風險


{patient_info_section}

問題: {message}""",

        'self_pay': f"""## Role: 麻醉諮詢助手
### 回答原則:
- 使用繁體中文，簡潔說明，盡量在200字以內
- 針對性建議自費項目
- 使用emoji增加親和力
- 除了下肢手術、剖腹產、泌尿科手術，其餘不考慮半身麻醉

### 自費建議規則:
- 年齡>50或風險較高: 建議麻醉深度監測、最適肌張力
- 擔心疼痛: 建議自控式止痛
- 易暈或手術>2小時: 建議止吐藥、麻醉深度監測
- 怕冷或手術>1小時: 建議溫毯
- 焦慮或失眠: 建議麻醉深度監測
- 心臟手術: 建議腦血氧監測

{patient_info_section}

問題: {message}""",

        'general': f"""## Role: 麻醉諮詢助手
### 回答原則:
- 使用繁體中文，簡潔明瞭，盡量在300字以內
- 專注於麻醉相關資訊
- 適當使用emoji增加親和力
- 根據問題重點回答
- 除了下肢手術、剖腹產、泌尿科手術，其餘不考慮半身麻醉

### 基本重點:
- 術前準備說明
- 麻醉方式相關解釋
- 麻醉風險說明
- 自費項目建議

{patient_info_section}

問題: {message}"""
    }

    return prompts.get(question_type, prompts['general'])

# Initialize Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
logger.info(f"Using API key from environment: {GOOGLE_API_KEY[:5]}...{GOOGLE_API_KEY[-4:] if GOOGLE_API_KEY else 'None'}")

if not GOOGLE_API_KEY:
    logger.warning("No API key found in environment variables")
    raise ValueError("No API key found. Please set GOOGLE_API_KEY in your .env file")

# Model configuration
generation_config = {
    "temperature": 1,              # Maximum creativity
    "top_p": 0.95,                # High diversity in responses
    "top_k": 40,                  # Top-k sampling parameter
    "max_output_tokens": 8192,     # Increased maximum response length
}

# Safety settings
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
]

def get_gemini_model():
    """Get or initialize the Gemini model"""
    if not hasattr(get_gemini_model, '_model'):
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            get_gemini_model._model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            logger.info("Gemini model initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Gemini model: {str(e)}")
            raise
    return get_gemini_model._model

# Initialize model
try:
    model = get_gemini_model()
    logger.info("Gemini model initialized at startup")
except Exception as e:
    logger.error(f"Failed to initialize Gemini model at startup: {str(e)}")
    model = None

# Initialize OpenAI API
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    logger.error("OpenAI API key not found in environment variables")
else:
    logger.info(f"OpenAI API key loaded: {OPENAI_API_KEY[:5]}...{OPENAI_API_KEY[-4:]}")
    openai.api_key = OPENAI_API_KEY

def get_openai_response(message, patient_info):
    """Get response from OpenAI model"""
    try:
        if not openai.api_key:
            logger.error("OpenAI API key not set")
            return "抱歉，OpenAI API 金鑰未設定。"
            
        context = create_context(message, patient_info)
        logger.info("Sending request to OpenAI...")
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一位專業的麻醉諮詢助手，請根據病人的資訊提供適當的建議。"},
                {"role": "user", "content": context}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        logger.info("Received response from OpenAI")
        
        if not response or not response.choices:
            logger.error("Empty response from OpenAI")
            return "抱歉，OpenAI 回應為空。"
            
        return format_response(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error getting OpenAI response: {str(e)}", exc_info=True)
        return f"抱歉，OpenAI 回應出現錯誤：{str(e)}"

@app.route('/')
def home():
    """Reset session and start fresh"""
    # Clear any existing session data
    session.clear()
    return render_template('index.html')

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
            
            # Get responses from both models
            gemini_response = get_bot_response(message, patient_info)
            openai_response = get_openai_response(message, patient_info)
            
            # Save chat history with both responses - SIMPLIFIED VERSION
            try:
                # Log details before saving
                logger.info(f"Attempting to save chat entry - Details:")
                logger.info(f"Patient ID: {patient_id}")
                logger.info(f"Message: {message[:50]}...")
                logger.info(f"Gemini response: {gemini_response[:50]}...")
                logger.info(f"OpenAI response: {openai_response[:50]}...")
                
                # Create the chat history entry
                chat = ChatHistory(
                    patient_id=patient_id,
                    message=message,
                    response=gemini_response,
                    openai_response=openai_response,
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
            
            return jsonify({'response': gemini_response})
            
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
            
            # Save a final chat entry to mark completion
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
            format_local_time=format_local_time
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
        eval_results = db.session.query(
            ChatbotEvaluation.patient_id,
            func.avg(ChatbotEvaluation.accuracy_score).label('avg_accuracy'),
            func.avg(ChatbotEvaluation.trustworthiness_score).label('avg_trust'),
            func.avg(ChatbotEvaluation.empathy_score).label('avg_empathy')
        ).group_by(
            ChatbotEvaluation.patient_id
        ).all()
        
        for result in eval_results:
            evaluations[result.patient_id] = {
                'accuracy': round(result.avg_accuracy, 1) if result.avg_accuracy else 'N/A',
                'trust': round(result.avg_trust, 1) if result.avg_trust else 'N/A',
                'empathy': round(result.avg_empathy, 1) if result.avg_empathy else 'N/A'
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



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), debug=True)
