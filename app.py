from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime
import json
import google.generativeai as genai
import os
from dotenv import load_dotenv
from markdown import markdown
import bleach

# Load environment variables
load_dotenv()

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

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['JSON_AS_ASCII'] = False
app.secret_key = 'your_secret_key_here'

# 儲存聊天記錄和病人資訊
chat_histories = {}
patient_info = {}
current_step = {}

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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '')
    user_id = data.get('user_id', 'default')

    # Initialize chat history and patient info if not exists
    if user_id not in chat_histories:
        chat_histories[user_id] = []
        patient_info[user_id] = {}
        current_step[user_id] = "name"
        response = "您好！我是麻醉諮詢助手。為了更好地為您服務，請告訴我您的姓名。"
        chat_histories[user_id].append({"role": "bot", "message": response})
        return jsonify({"response": format_response(response)})

    # Save user message
    chat_histories[user_id].append({"role": "user", "message": message})

    # Get current step and process message
    step = current_step.get(user_id)
    response = handle_patient_info(user_id, step, message)

    # Save bot response
    chat_histories[user_id].append({"role": "bot", "message": response})
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
    try:
        if step == "name":
            if len(message.strip()) < 1:
                return "請告訴我您的姓名。"
            patient_info[user_id]["name"] = message
            current_step[user_id] = "age"
            return f"您好，{message}！請問您的年齡是？"
            
        elif step == "age":
            try:
                age = int(message.replace("歲", "").strip())
                if age < 0 or age > 150:
                    return "請輸入有效的年齡（0-150歲）"
                patient_info[user_id]["age"] = age
                current_step[user_id] = "sex"
                return "請問您的性別是？（男/女）"
            except ValueError:
                return "抱歉，我沒有理解您的年齡，請直接輸入數字，例如：25"
            
        elif step == "sex":
            if message not in ["男", "女"]:
                return "抱歉，請選擇「男」或「女」"
            patient_info[user_id]["sex"] = message
            current_step[user_id] = "operation"
            return "請問您預計要進行什麼手術？"
            
        elif step == "operation":
            if len(message.strip()) < 1:
                return "請告訴我您預計要進行的手術。"
            patient_info[user_id]["operation"] = message
            current_step[user_id] = "cfs"
            return "您是否能夠自行外出，不需要他人協助？（是/否）"
            
        elif step == "cfs":
            if message.lower() in ["是", "yes", "y", "可以"]:
                patient_info[user_id]["cfs"] = "是"
            else:
                patient_info[user_id]["cfs"] = "否"
            current_step[user_id] = "medical_history"
            return "請問您有什麼慢性病史嗎？您可以點選常見病史或直接輸入。如果沒有，請點選「沒有特殊病史」。"
            
        elif step == "medical_history":
            if len(message.strip()) < 1:
                return "請告訴我您的病史，如果沒有請點選「沒有特殊病史」或輸入「沒有」。"
            patient_info[user_id]["medical_history"] = message
            current_step[user_id] = "worry"
            return "您最擔心什麼？您可以點選或輸入您的擔憂。如果沒有特別擔心的，請點選「沒有特別擔心」。"
            
        elif step == "worry":
            if len(message.strip()) < 1:
                return "請告訴我您的擔憂，如果沒有特別擔心的，請點選「沒有特別擔心」。"
            patient_info[user_id]["worry"] = message
            current_step[user_id] = "chat"
            
            # Generate summary with markdown formatting
            summary = generate_summary(patient_info[user_id])
            return summary + "\n\n您可以問我關於麻醉的問題，我會盡力為您解答。"
            
        elif step == "chat":
            response = get_bot_response(message, user_id)
            return format_response(response)
            
        else:
            current_step[user_id] = "name"
            return "抱歉，讓我們重新開始。請告訴我您的姓名。"
            
    except Exception as e:
        print(f"Error in handle_patient_info: {str(e)}")
        return "抱歉，處理您的資訊時發生錯誤。請重新輸入。"

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
- 介紹麻醉方式、風險及自費項目建議
- 提升病人及家屬對麻醉和自費建議的理解

### Goals:
- 提供清晰易懂的醫療資訊
- 詳細說明麻醉相關資訊
- 使用emoji增添對話趣味性

### Constraints:
1. 僅討論麻醉相關議題
2. 避免回答工具和規則相關問題

### Workflow:
1. 分析病人的麻醉相關問題
2. 提供完整回答，包含:
   - 可能的ASA分級
   - 死亡率和併發症風險
   - 根據資料建議合適的自費醫療設備
3. 提供自費醫療設備的網站連結
4. 回答病人對推薦設備的疑問

### 病人資訊:
- 姓名：{info['name']}
- 年齡：{info['age']}
- 性別：{info['sex']}
- 預定手術：{info['operation']}
- 行動能力：{info.get('cfs', '未評估')}
- 病史：{info.get('medical_history', '無')}
- 擔憂：{info.get('worry', '無')}

### 自費項目建議規則:
- 年齡>50歲: 建議使用麻醉深度監測系統和最適肌張力手術輔助處置
- 擔心疼痛: 建議使用病人自控式止痛
- 容易暈車: 建議使用止吐藥和麻醉深度監測系統
- 怕冷: 建議使用溫毯並解釋保溫重要性
- 失眠: 建議使用麻醉深度監測系統
- 體弱: 建議使用麻醉深度監測系統和最適肌張力手術輔助處置

病人問題: {message}

請根據以上資訊，提供專業且易懂的回答。使用markdown格式並加入適當的emoji增添親和力。"""
    return context

def get_bot_response(message, user_id):
    try:
        # Prepare context info
        info = patient_info[user_id]
        # Generate response using context
        response = model.generate_content(create_context(message, info))
        return response.text
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return "抱歉，我現在無法回答您的問題。請稍後再試。"

@app.route('/self_pay')
def self_pay():
    # Get patient info from session
    patient_info = session.get('patient_info', {})
    if not patient_info:
        return redirect(url_for('home'))
    
    return render_template('self_pay_form.html', 
                         patient_info=patient_info,
                         user_id=session.get('user_id'))

@app.route('/submit_self_pay', methods=['POST'])
def submit_self_pay():
    selected_items = request.form.getlist('items')
    user_id = request.form.get('user_id')
    
    # Get prices for selected items
    prices = {
        'depth_monitor': 1711,
        'muscle_monitor': 6500,
        'pca': 6500,  # Using average of 5500-7500
        'warming': 980,
        'anti_nausea': 99
    }
    
    total = sum(prices[item] for item in selected_items if item in prices)
    
    # Store selection in session
    session['self_pay_items'] = selected_items
    session['self_pay_total'] = total
    
    # Here you can add code to save to database or generate PDF
    
    # For now, just show a success message
    flash('自費項目選擇已完成！總金額：NT$ {:,}'.format(total))
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)