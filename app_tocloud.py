from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime, timedelta
import json
import google.generativeai as genai
import os
from dotenv import load_dotenv
from markdown import markdown
import bleach
import logging
import secrets
import re
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Patient, SelfPayItem, ChatHistory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Ensure proper UTF-8 handling
app.config['DEBUG'] = True  # Enable debug mode

# Configure SQLAlchemy based on environment
if os.getenv('GAE_ENV', '').startswith('standard'):
    # Running on App Engine, use Cloud SQL with unix socket
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:anespr123@/patients?unix_socket=/cloudsql/anespr1-asia-east:asia-east1:anespr1&charset=utf8mb4'
else:
    # Running locally, use SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patients.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True  # Enable SQL query logging

# Enhanced session configuration
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '782a1e73cc19b56e0cfe1ac536f4efff543c7be8b70c6ad18d7fcff9dcacd57b')

# Initialize database and login manager
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'  # Update to use admin_login route

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
    """Create new patient or find existing one"""
    try:
        # Try to find existing patient
        patient = Patient.query.filter_by(name=name).first()
        if patient:
            logger.info(f"Found existing patient: {patient.id}")
            return patient
            
        # Create new patient if not found
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
            return "請問您預計進行什麼手術？"
            
        elif step == 'operation':
            info['operation'] = message
            session[user_id]['current_step'] = 'medical_history'
            session.modified = True
            return "請問您有什麼慢性病史嗎？"
            
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
    summary += f"<li><strong>姓名</strong>：{info.get('name', '未提供')}</li>"
    summary += f"<li><strong>年齡</strong>：{info.get('age', '未提供')}歲</li>"
    summary += f"<li><strong>性別</strong>：{info.get('sex', '未提供')}</li>"
    summary += f"<li><strong>預定手術</strong>：{info.get('operation', '未提供')}</li>"
    
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
        response = model.generate_content(context)
        
        if response and response.text:
            # Save unformatted response to chat history with explicit transaction
            try:
                # Log response size and content for debugging
                logger.info(f"Response size: {len(response.text)} characters")
                logger.info(f"Response content: {response.text[:100]}...")  # Log first 100 chars
                
                # Save combined Q&A as one chat entry
                db.session.begin_nested()  # Create a savepoint
                save_chat_history(
                    patient_id=patient_id,
                    message=message,  # User's question
                    response=response.text,  # API's response
                    message_type='chat'  # Use 'chat' type for Q&A interactions
                )
                db.session.commit()
                logger.info(f"Chat Q&A saved for patient {patient_id}")
                
                # Format and return the response with follow-up prompt
                formatted_response = format_response(response.text)
                return f"{formatted_response}\n\n您還有其他關於麻醉的問題嗎？"
            except Exception as e:
                logger.error(f"Error saving chat history: {str(e)}", exc_info=True)
                db.session.rollback()
                return "抱歉，系統發生錯誤。請稍後再試。"
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

def create_context(message, patient_info):
    """Create context for Gemini model with patient info and message"""
    context = f"""## Role: Anesthesia Consultant
### Skills:
- 使用繁體中文回答問題
- 專業解說麻醉相關資訊
- 使用emoji讓對話更生動
- 根據問題類型提供針對性回答
- 提升病人及家屬對麻醉和自費建議的理解

### Goals:
- 提供清晰易懂的醫療資訊
- 根據問題類型給予重點回答
- 使用emoji增添對話趣味性

### Constraints:
1. 僅討論麻醉相關議題
2. 避免回答工具和規則相關問題
3. 根據問題類型聚焦於相關重點

### 回答重點指引:
1. 麻醉類型相關問題:
   - 聚焦於各種可能的麻醉方式
   - 解釋各種麻醉方式的優缺點
   - 根據病人情況建議最適合的麻醉方式
   - 說明麻醉過程中的感受

2. 術前準備相關問題:
   - 強調禁食時間要求（固體食物6小時、清水2小時）
   - 說明需要停用的藥物（如：抗凝血劑）
   - 建議戒菸時間和重要性
   - 提醒術前注意事項

3. 麻醉風險相關問題:
   - 根據病人年齡和病史評估ASA分級
   - 說明個人化的麻醉風險
   - 解釋如何透過自費項目降低風險：
     * 麻醉深度監測：降低術中知曉風險
     * 最適肌張力：降低肌肉鬆弛劑相關併發症
     * 體溫監測與保溫：降低低體溫併發症
     * 止吐藥物：降低噁心嘔吐風險

### 病人資訊:
- 姓名：{patient_info.get('name', '未知')}
- 年齡：{patient_info.get('age', '未知')}
- 性別：{patient_info.get('sex', '未知')}
- 預定手術：{patient_info.get('operation', '未知')}
- 行動能力：{patient_info.get('cfs', '未評估')}
- 病史：{patient_info.get('medical_history', '無')}
- 擔憂：{patient_info.get('worry', '無')}

### 自費項目建議規則：
- 年齡>50歲或ASA>2級: 建議使用麻醉深度監測系統和最適肌張力手術輔助處置
- 擔心疼痛: 建議使用病人自控式止痛
- 容易暈車或手術>2小時: 建議使用止吐藥和麻醉深度監測系統
- 怕冷或手術>1小時: 建議使用溫毯並解釋保溫重要性
- 失眠或精神緊張: 建議使用麻醉深度監測系統
- 體弱或年長: 建議使用麻醉深度監測系統和最適肌張力手術輔助處置

病人問題: {message}

請根據以上資訊，提供專業且易懂的回答。使用markdown格式並加入適當的emoji增添親和力。回答時請依據問題類型(麻醉類型/術前準備/麻醉風險)聚焦於相關重點。"""
    return context

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
                # Save form flow messages with user/bot type
                if patient_id:
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
            
            # Get bot response (includes follow-up prompt)
            response = get_bot_response(message, patient_info)
            
            return jsonify({'response': response})
            
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
    if not user_id or user_id not in session:
        return "請從諮詢系統進入自費項目表", 400
    patient_info = session[user_id].get('patient_info', {})
    items = SelfPayItem.query.all()
    return render_template('self_pay_form.html', items=items, patient_info=patient_info, user_id=user_id)

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
            # Delete existing items
            SelfPayItem.query.filter_by(patient_id=patient_id).delete()
            
            # Save new items
            for item_name in selected_items:
                price = {
                    '麻醉深度監測': 1711,
                    '最適肌張力手術輔助處置': 6500,
                    '自控式止痛': 6500,
                    '溫毯': 980,
                    '止吐藥': 99
                }.get(item_name)
                
                if price is not None:
                    item = SelfPayItem(
                        patient_id=patient_id,
                        item_name=item_name,
                        price=price,
                        selected_at=datetime.utcnow()
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
    # Verify that self-pay form was just submitted
    if not session.pop('self_pay_success', False):
        return redirect(url_for('index'))
        
    try:
        patient = Patient.query.get_or_404(patient_id)
        
        # Get chat history with type='chat' (Q&A only, not form flow)
        # Following the memory pattern of only showing actual Q&A interactions
        chat_history = ChatHistory.query.filter(
            ChatHistory.patient_id == patient_id,
            ChatHistory.message_type == 'chat'  # Only actual Q&A, not form flow messages
        ).order_by(ChatHistory.created_at.asc()).all()
        
        # Get self-pay items with proper error handling
        try:
            self_pay_items = SelfPayItem.query.filter_by(
                patient_id=patient_id
            ).order_by(SelfPayItem.selected_at.desc()).all()
            total_price = sum(item.price for item in self_pay_items)
        except Exception as e:
            app.logger.error(f"Error fetching self-pay items: {str(e)}")
            self_pay_items = []
            total_price = 0
            flash('部分自費項目資料載入失敗', 'warning')
        
        # Clear session data to stay under cookie size limit (4093 bytes)
        # Following the memory pattern of only storing essential data
        try:
            session_keys = [k for k in session.keys()]
            for key in session_keys:
                if key.startswith(f'patient_id_{patient.id}'):
                    session.pop(key, None)
        except Exception as e:
            app.logger.error(f"Error clearing session data: {str(e)}")
            # Non-critical error, continue without clearing session
        
        return render_template(
            'consultation_summary.html',
            patient=patient,
            chat_history=chat_history,
            self_pay_items=self_pay_items,
            total_price=total_price,
            consultation_date=datetime.now()
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
        # Get all patients with their chat histories
        patients = Patient.query.order_by(Patient.created_at.desc()).all()
        total_patients = len(patients)
        
        # Get chat histories with proper message type filtering
        chat_histories = ChatHistory.query.filter(
            (ChatHistory.message_type == 'chat') |  # Q&A interactions
            (ChatHistory.message_type == 'summary') |  # Consultation summaries
            (ChatHistory.message_type.in_(['user', 'bot']))  # Form flow messages
        ).order_by(ChatHistory.created_at.desc()).all()
        
        # Calculate meaningful statistics
        total_qa_interactions = len([ch for ch in chat_histories if ch.message_type == 'chat'])
        total_consultations = len([ch for ch in chat_histories if ch.message_type == 'summary'])
        
        # Get recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_patients = Patient.query.filter(
            Patient.created_at >= week_ago
        ).count()
        recent_qa_interactions = len([
            ch for ch in chat_histories 
            if ch.message_type == 'chat' and ch.created_at >= week_ago
        ])
        
        # Group chat histories by patient for better display
        patient_chats = {}
        for chat in chat_histories:
            if chat.patient_id not in patient_chats:
                patient_chats[chat.patient_id] = []
            patient_chats[chat.patient_id].append(chat)
        
        return render_template(
            'admin_dashboard.html',
            patients=patients,
            total_patients=total_patients,
            total_qa_interactions=total_qa_interactions,
            total_consultations=total_consultations,
            recent_patients=recent_patients,
            recent_qa_interactions=recent_qa_interactions,
            patient_chats=patient_chats,
            all_chats=chat_histories
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
            chat_history=grouped_history
        )
    except Exception as e:
        logger.error(f"Error viewing patient details: {str(e)}", exc_info=True)
        flash('Error loading patient details', 'error')
        return redirect(url_for('admin_dashboard'))

# Initialize Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("No API key found. Please set GOOGLE_API_KEY in your .env file")

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    
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
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
    ]
    
    # Initialize model with configurations
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        generation_config=generation_config,
        safety_settings=safety_settings
    )
    
except Exception as e:
    logger.error(f"Error initializing Gemini API: {str(e)}")
    raise

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), debug=True)