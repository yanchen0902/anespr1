from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime
import json
import google.generativeai as genai
import os
from dotenv import load_dotenv
from markdown import markdown
import bleach
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Patient, SelfPayItem, ChatHistory, init_login_manager

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')  # Make sure to set this in .env

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patients.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True  # Enable SQL query logging

# Initialize database
db.init_app(app)

# Create tables within application context
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")

# Initialize Flask-Login
init_login_manager(app)

# 問題流程
questions = {
    "name": "請問您的姓名是？",
    "age": "請問您的年齡是？",
    "sex": "請問您的性別是？（男/女）",
    "cfs": "您是否能夠自行外出，不需要他人協助？",
    "medical_history": "請告訴我您的過去病史（例如：高血壓、糖尿病、心臟病等）？如果沒有，請回答「無」",
    "operation": "請問您預計要進行什麼手術？",
    "worry": "您有什麼擔心的地方嗎？"
}

# 麻醉相關資訊和建議
anesthesia_info = {
    "全身麻醉": {
        "描述": "全身麻醉會讓您在手術過程中完全睡著",
        "準備事項": [
            "手術前6-8小時禁食",
            "手術前24小時內避免吸菸",
            "告知醫師目前服用的所有藥物"
        ]
    },
    "區域麻醉": {
        "描述": "區域麻醉會使身體特定部位失去知覺",
        "準備事項": [
            "依據手術類型可能需要禁食",
            "大多數藥物可以照常服用",
            "遵循麻醉醫師的具體指示"
        ]
    }
}

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
    print(f"Error initializing Gemini API: {str(e)}")
    raise

@app.route('/')
def home():
    return render_template('greeting.html')

@app.route('/chat')
def chat():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat_post():
    data = request.get_json()
    message = data.get('message', '')
    user_id = data.get('user_id', 'default')

    # Initialize chat history and patient info if not exists
    if user_id not in session:
        session[user_id] = {}
        session[user_id]['chat_history'] = []
        session[user_id]['patient_info'] = {}
        session[user_id]['current_step'] = "name"
        response = "您好！我是麻醉諮詢助手。為了更好地為您服務，請告訴我您的姓名。"
        session[user_id]['chat_history'].append({"role": "bot", "message": response})
        return jsonify({"response": format_response(response)})

    # Save user message
    session[user_id]['chat_history'].append({"role": "user", "message": message})

    # Get current step and process message
    step = session[user_id]['current_step']
    response = handle_patient_info(user_id, step, message)

    # Save bot response
    session[user_id]['chat_history'].append({"role": "bot", "message": response})
    return jsonify({"response": format_response(response)})

def format_response(response):
    """Convert response to HTML with markdown formatting"""
    try:
        # Convert markdown to HTML
        html_response = markdown(response, extensions=['extra'])
        
        # Define allowed HTML tags and attributes
        allowed_tags = [
            'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'strong', 'em', 'a',
            'code', 'pre', 'blockquote', 'table', 'thead',
            'tbody', 'tr', 'th', 'td', 'br', 'hr'
        ]
        allowed_attributes = {
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'title']
        }
        
        # Clean and sanitize HTML
        clean_html = bleach.clean(
            html_response,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
        
        return clean_html
    except Exception as e:
        print(f"Error in format_response: {str(e)}")
        return response  # Return original response if formatting fails

def handle_patient_info(user_id, step, message):
    if 'patient_info' not in session[user_id]:
        session[user_id]['patient_info'] = {}
    
    info = session[user_id]['patient_info']
    
    if step == "name":
        if len(message.strip()) < 1:
            return "請告訴我您的姓名。"
        info['name'] = message
        session[user_id]['current_step'] = "age"
        session.modified = True
        return "您好，" + message + "！請問您的年齡是？"
            
    elif step == "age":
        try:
            age = int(message.replace("歲", "").strip())
            if age < 0 or age > 150:
                return "請輸入有效的年齡（0-150歲）"
            info['age'] = age
            session[user_id]['current_step'] = "sex"
            session.modified = True
            return "請問您的性別是？（男/女）"
        except ValueError:
            return "抱歉，我沒有理解您的年齡，請直接輸入數字，例如：25"
            
    elif step == "sex":
        if message not in ["男", "女"]:
            return "抱歉，請選擇「男」或「女」" 
        info['sex'] = message
        session[user_id]['current_step'] = "operation"
        session.modified = True
        return "請問您預計要進行什麼手術？"
            
    elif step == "operation":
        if len(message.strip()) < 1:
            return "請告訴我您預計要進行的手術。"
        info['operation'] = message
        session[user_id]['current_step'] = "cfs"
        session.modified = True
        return "您是否能夠自行外出，不需要他人協助？（是/否）"
            
    elif step == "cfs":
        if message.lower() in ["是", "yes", "y", "可以"]:
            info['cfs'] = "是"
        else:
            info['cfs'] = "否"
        session[user_id]['current_step'] = "medical_history"
        session.modified = True
        return "請問您有什麼重要的病史嗎？例如：高血壓、糖尿病、心臟病等。如果沒有，請回答「無」。"
            
    elif step == "medical_history":
        if len(message.strip()) < 1:
            return "請告訴我您的病史，如果沒有請點選「沒有特殊病史」。"
        info['medical_history'] = message
        session[user_id]['current_step'] = "worry"
        session.modified = True
        return "您最擔心什麼？您可以點選或輸入您的擔憂。如果沒有特別擔心的，請點選「沒有特別擔心」。"
            
    elif step == "worry":
        if len(message.strip()) < 1:
            return "請告訴我您的擔憂，如果沒有特別擔心的，請點選「沒有特別擔心」。"
        info['worry'] = message
        
        # Save patient data to database
        print(f"Attempting to save patient data: {info}")  # Debug print
        try:
            # Create new patient
            patient = Patient()
            patient.name = info.get('name', '')
            patient.age = info.get('age', 0)
            patient.sex = info.get('sex', '')
            patient.operation = info.get('operation', '')
            patient.cfs = info.get('cfs', '')
            patient.medical_history = info.get('medical_history', '')
            patient.worry = info.get('worry', '')
            
            # Add and commit
            print("Adding patient to session...")
            db.session.add(patient)
            print("Committing changes...")
            db.session.commit()
            print(f"Successfully saved patient with ID: {patient.id}")
            
        except Exception as e:
            print(f"Error saving patient data: {str(e)}")
            import traceback
            print(traceback.format_exc())
            db.session.rollback()
        
        session[user_id]['current_step'] = "chat"
        session.modified = True
            
        # Generate summary with markdown formatting
        summary = generate_summary(info)
        return summary + "\n\n您可以問我關於麻醉的問題，我會盡力為您解答。"
            
    elif step == "chat":
        response = get_bot_response(message, user_id)
        return format_response(response)
            
    else:
        session[user_id]['current_step'] = "name"
        return "抱歉，讓我們重新開始。請告訴我您的姓名。"

def generate_summary(info):
    """Generate a markdown-formatted summary of patient information"""
    summary = "## 您提供的資訊摘要\n\n"
    summary += f"* **姓名**：{info.get('name', '未提供')}\n"
    summary += f"* **年齡**：{info.get('age', '未提供')}歲\n"
    summary += f"* **性別**：{info.get('sex', '未提供')}\n"
    summary += f"* **預定手術**：{info.get('operation', '未提供')}\n"
    
    cfs = "可以自行外出" if info.get('cfs') == "是" else "需要他人協助"
    summary += f"* **行動能力**：{cfs}\n"
    
    medical_history = info.get('medical_history', '無')
    if medical_history in ["沒有", "無"]:
        medical_history = "無特殊病史"
    summary += f"* **病史**：{medical_history}\n"
    
    worry = info.get('worry', '無特殊擔憂')
    if worry in ["沒有", "無"]:
        worry = "無特殊擔憂"
    summary += f"* **擔憂**：{worry}"
    
    return summary

def create_context(message, info):
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
3. 根據問題類型聚焦回答重點

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
- 姓名：{info['name']}
- 年齡：{info['age']}
- 性別：{info['sex']}
- 預定手術：{info['operation']}
- 行動能力：{info.get('cfs', '未評估')}
- 病史：{info.get('medical_history', '無')}
- 擔憂：{info.get('worry', '無')}

### 自費項目建議規則:
- 年齡>50歲或ASA>2級: 建議使用麻醉深度監測系統和最適肌張力手術輔助處置
- 擔心疼痛: 建議使用病人自控式止痛
- 容易暈車或手術>2小時: 建議使用止吐藥和麻醉深度監測系統
- 怕冷或手術>1小時: 建議使用溫毯並解釋保溫重要性
- 失眠或精神緊張: 建議使用麻醉深度監測系統
- 體弱或年長: 建議使用麻醉深度監測系統和最適肌張力手術輔助處置

病人問題: {message}

請根據以上資訊，提供專業且易懂的回答。使用markdown格式並加入適當的emoji增添親和力。回答時請依據問題類型(麻醉類型/術前準備/麻醉風險)聚焦於相關重點。"""
    return context

def get_bot_response(message, user_id):
    info = session[user_id].get('patient_info', {})
    
    # Create context for the model
    context = create_context(message, info)
    
    try:
        # Get response from API
        response = model.generate_content(context).text
        
        # Save to database if we have a patient
        try:
            # Find the patient by name and created_at (most recent)
            patient = Patient.query.filter_by(name=info.get('name')).order_by(Patient.created_at.desc()).first()
            if patient:
                # Save both user message and bot response
                user_msg = ChatHistory(
                    patient_id=patient.id,
                    message=message,
                    response=None,
                    message_type='user'
                )
                bot_msg = ChatHistory(
                    patient_id=patient.id,
                    message=None,
                    response=response,
                    message_type='bot'
                )
                db.session.add(user_msg)
                db.session.add(bot_msg)
                db.session.commit()
                print(f"Saved chat history for patient {patient.name}")
        except Exception as e:
            print(f"Error saving chat history: {str(e)}")
            db.session.rollback()
        
        return response
    except Exception as e:
        print(f"Error getting API response: {str(e)}")
        return "抱歉，我現在無法回答您的問題。請稍後再試。"

@app.route('/self_pay')
def self_pay():
    # Get user_id from URL parameter
    user_id = request.args.get('user_id')
    
    # Get patient info from global dictionary
    user_info = session.get(user_id, {}).get('patient_info', {})
    if not user_info:
        return redirect(url_for('home'))
    
    return render_template('self_pay_form.html', 
                         patient_info=user_info,
                         user_id=user_id)

@app.route('/submit_self_pay', methods=['POST'])
def submit_self_pay():
    data = request.get_json()
    user_id = data.get('user_id')
    selected_items = data.get('selected_items', [])
    
    patient = Patient.query.get(user_id)
    if patient:
        for item in selected_items:
            self_pay_item = SelfPayItem(
                patient_id=user_id,
                item_name=item['name'],
                price=float(item['price'])
            )
            db.session.add(self_pay_item)
        db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    today = datetime.utcnow().date()
    today_count = Patient.query.filter(
        db.func.date(Patient.created_at) == today
    ).count()
    
    month_start = today.replace(day=1)
    month_count = Patient.query.filter(
        Patient.created_at >= month_start
    ).count()
    
    patients = Patient.query.order_by(Patient.created_at.desc()).limit(50).all()
    
    return render_template('admin.html',
                         today_count=today_count,
                         month_count=month_count,
                         patients=patients)

@app.route('/admin/patient/<id>')
@login_required
def patient_detail(id):
    patient = Patient.query.get_or_404(id)
    return render_template('patient_detail.html', patient=patient)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)