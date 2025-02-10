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
        current_step[user_id] = "greeting"

    # If it's the first message, send greeting
    if not chat_histories[user_id]:
        response = "您好！我是麻醉諮詢助手。為了更好地為您服務，請告訴我您的姓名。"
        current_step[user_id] = "name"
        chat_histories[user_id].append({"role": "bot", "message": response})
        return jsonify({"response": response})

    # Get current step
    user_step = current_step.get(user_id, "name")
    
    # Process the message based on current step
    response = handle_patient_info(user_id, user_step, message)
    
    # Save bot response
    chat_histories[user_id].append({"role": "bot", "message": response})
    
    return jsonify({"response": response})

def handle_patient_info(user_id, current_step, message):
    try:
        if current_step == "greeting":
            current_step[user_id] = "name"
            return "您好！我是麻醉諮詢助手。為了更好地為您服務，請告訴我您的姓名。"
            
        elif current_step == "name":
            patient_info[user_id]["name"] = message
            current_step[user_id] = "age"
            return f"您好，{message}！請問您的年齡是？"
            
        elif current_step == "age":
            try:
                age = int(message.replace("歲", "").strip())
                patient_info[user_id]["age"] = age
                current_step[user_id] = "sex"
                return "請問您的性別是？"
            except ValueError:
                return "抱歉，我沒有理解您的年齡，請直接輸入數字，例如：25"
            
        elif current_step == "sex":
            if any(gender in message for gender in ["男", "女"]):
                patient_info[user_id]["sex"] = message
                current_step[user_id] = "operation"
                return "請問您預計要進行什麼手術？"
            else:
                return "抱歉，請選擇您的性別（男/女）"
            
        elif current_step == "operation":
            patient_info[user_id]["operation"] = message
            current_step[user_id] = "cfs"
            return "您是否能夠自行外出，不需要他人協助？"
            
        elif current_step == "cfs":
            patient_info[user_id]["cfs"] = message
            current_step[user_id] = "medical_history"
            return "請問您有什麼慢性病史嗎？例如：高血壓、糖尿病、心臟病等。如果沒有，請說「沒有」。"
            
        elif current_step == "medical_history":
            patient_info[user_id]["medical_history"] = message
            current_step[user_id] = "worry"
            return "您最擔心什麼？例如：怕痛、怕噁心、怕冷等。"
            
        elif current_step == "worry":
            patient_info[user_id]["worry"] = message
            current_step[user_id] = "chat"
            
            # Generate summary
            summary = generate_summary(patient_info[user_id])
            return summary + "\n\n您可以問我關於麻醉的問題，我會盡力為您解答。完成諮詢後，可以前往自費項目選擇頁面。"
            
        elif current_step == "chat":
            # Handle general chat after collecting basic info
            return get_bot_response(message, user_id)
            
    except Exception as e:
        print(f"Error in handle_patient_info: {str(e)}")
        return "抱歉，處理您的資訊時發生錯誤。請重新輸入。"

def generate_summary(info):
    summary = f"以下是您提供的資訊：\n"
    summary += f"• 姓名：{info.get('name', '未提供')}\n"
    summary += f"• 年齡：{info.get('age', '未提供')}歲\n"
    summary += f"• 性別：{info.get('sex', '未提供')}\n"
    summary += f"• 預定手術：{info.get('operation', '未提供')}\n"
    
    cfs = "可以自行外出" if info.get('cfs') == "是" else "需要他人協助"
    summary += f"• 行動能力：{cfs}\n"
    
    medical_history = info.get('medical_history', '無')
    if medical_history == "沒有" or medical_history == "無":
        medical_history = "無特殊病史"
    summary += f"• 病史：{medical_history}\n"
    
    worry = info.get('worry', '無特殊擔憂')
    summary += f"• 擔憂：{worry}"
    
    return summary

def get_bot_response(message, user_id):
    try:
        # 準備上下文資訊
        info = patient_info[user_id]
        
        # 確保所有必要的鍵都存在，如果不存在則提供預設值
        safe_info = {
            'name': info.get('name', ''),
            'age': info.get('age', ''),
            'sex': info.get('sex', ''),
            'cfs': info.get('cfs', '尚未評估'),
            'medical_history': info.get('medical_history', '無'),
            'operation': info.get('operation', ''),
            'worry': info.get('worry', '無')
        }
        
        # 根據問題類型提供不同的上下文
        if "根據我的身體狀況" in message:
            context = f"""
## Role: Anesthesia Consultant

### Patient Information:
- 年齡：{safe_info['age']}
- 性別：{safe_info['sex']}
- 身體功能狀態：{safe_info['cfs']}
- 過去病史：{safe_info['medical_history']}
- 預定手術：{safe_info['operation']}
- 擔心的部分：{safe_info['worry']}

### 自費項目建議規則：
- 年齡>50歲: 建議使用麻醉深度監測系統
- CFS評分>4: 建議使用麻醉深度監測系統和最適肌張力手術輔助處置
- 怕痛: 建議使用自控式止痛
- 容易暈車: 建議使用止吐藥和麻醉深度監測系統
- 怕冷: 建議使用溫毯並解釋保溫重要性
- 失眠: 建議使用麻醉深度監測系統
- 衰弱: 建議使用麻醉深度監測系統和最適肌張力手術輔助處置
- 都要建議溫毯，因為手術室的溫度通常較低，加上麻醉藥物可能會影響體溫調節

請根據病人的年齡、身體狀況（CFS評分）、病史和擔憂，提供完整的個人化建議，包括：
1. 需要特別注意的事項
2. 建議的自費項目和原因
3. 麻醉風險評估
4. 術後照護重點

使用傳統中文回答，以專業且溫和的口吻說明。回答要有條理且詳細。"""

        elif "麻醉類型" in message:
            context = f"""
## Role: Anesthesia Consultant

### Patient Information:
- 預定手術：{safe_info['operation']}
- 身體功能狀態：{safe_info['cfs']}
- 過去病史：{safe_info['medical_history']}

請著重說明以下幾點：
1. 這個手術通常使用什麼類型的麻醉
2. 各種可能的麻醉方式及其優缺點
3. 麻醉的過程說明
4. 麻醉後的恢復過程

使用傳統中文回答，避免使用專業術語，用病人容易理解的方式解釋。"""

        elif "術前準備" in message:
            context = f"""
## Role: Anesthesia Consultant

### Patient Information:
- 預定手術：{safe_info['operation']}
- 過去病史：{safe_info['medical_history']}

請著重說明以下術前準備事項：
1. 生活習慣調整（如戒菸、戒酒）
2. 藥物調整（特別是抗凝血劑）
3. 禁食時間和規定
4. 術前檢查項目
5. 手術前一天的注意事項
6. 手術當天的準備事項

使用傳統中文回答，條列式說明，重點清楚。"""

        else:
            context = f"""
## Role: Anesthesia Consultant

### Patient Information:
- 姓名：{safe_info['name']}
- 年齡：{safe_info['age']}
- 性別：{safe_info['sex']}
- 身體功能狀態：{safe_info['cfs']}
- 過去病史：{safe_info['medical_history']}
- 預定手術：{safe_info['operation']}
- 擔心的部分：{safe_info['worry']}

請以專業、溫和的口吻回答病人的問題，並特別注意以下幾點：
1. 根據病人的身體狀況（CFS評分）給予合適的建議
2. 針對病人擔心的部分提供詳細說明
3. 如果病人符合自費項目的建議條件，請適時提出建議
4. 使用傳統中文回答
5. 回答要簡潔有重點"""
        
        # 生成回應
        response = model.generate_content(context + "\n\n" + message)
        
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