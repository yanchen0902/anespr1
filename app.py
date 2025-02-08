from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['JSON_AS_ASCII'] = False

# 儲存聊天記錄和病人資訊
chat_histories = {}
patient_info = {}

# 問題流程
questions = {
    "name": "請問您的姓名是？",
    "age": "請問您的年齡是？",
    "sex": "請問您的性別是？（男/女）",
    "operation": "請問您預計要進行什麼手術？"
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
    data = request.json
    user_message = data.get('message', '')
    user_id = data.get('user_id', 'default')
    
    if user_id not in chat_histories:
        chat_histories[user_id] = []
        patient_info[user_id] = {"step": "name"}
        return jsonify({"response": questions["name"]})
    
    # 根據目前步驟處理回應
    current_step = patient_info[user_id].get("step")
    
    # 儲存使用者訊息
    chat_histories[user_id].append({"role": "user", "message": user_message})
    
    # 處理各個步驟
    response = handle_patient_info(user_id, current_step, user_message)
    
    # 儲存機器人回應
    chat_histories[user_id].append({"role": "bot", "message": response})
    
    return jsonify({"response": response})

def handle_patient_info(user_id, current_step, message):
    if current_step == "name":
        patient_info[user_id]["name"] = message
        patient_info[user_id]["step"] = "age"
        return questions["age"]
        
    elif current_step == "age":
        try:
            age = int(message)
            if age < 0 or age > 150:
                return "請輸入有效的年齡（0-150歲）"
            patient_info[user_id]["age"] = age
            patient_info[user_id]["step"] = "sex"
            return questions["sex"]
        except ValueError:
            return "請輸入有效的年齡數字"
            
    elif current_step == "sex":
        if message not in ["男", "女"]:
            return "請輸入「男」或「女」"
        patient_info[user_id]["sex"] = message
        patient_info[user_id]["step"] = "operation"
        return questions["operation"]
        
    elif current_step == "operation":
        patient_info[user_id]["operation"] = message
        patient_info[user_id]["step"] = "chat"
        
        # 顯示收集到的資訊並開始一般對話
        info = patient_info[user_id]
        summary = f"""感謝您提供以下資訊：
姓名：{info['name']}
年齡：{info['age']}
性別：{info['sex']}
預定手術：{info['operation']}

接下來我可以為您回答關於麻醉的問題，例如：
1. 這個手術需要什麼類型的麻醉？
2. 麻醉前需要做什麼準備？
3. 麻醉有什麼風險？

請問您想了解什麼？"""
        return summary
        
    else:
        return get_gemini_response(user_id, message)

def get_gemini_response(user_id, message):
    try:
        # 準備上下文資訊
        info = patient_info[user_id]
        
        # 建立進階提示詞
        context = f"""
## Role: Anesthesia Consultant
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

### 病人資訊：
- 姓名：{info['name']}
- 年齡：{info['age']}
- 性別：{info['sex']}
- 預定手術：{info['operation']}

### 自費項目建議規則：
- 年齡>50歲: 建議使用麻醉深度監測系統和最適肌張力手術輔助處置
- 擔心疼痛: 建議使用病人自控式止痛
- 容易暈車: 建議使用止吐藥和麻醉深度監測系統
- 怕冷: 建議使用溫毯並解釋保溫重要性
- 失眠: 建議使用麻醉深度監測系統
- 體弱: 建議使用麻醉深度監測系統和最適肌張力手術輔助處置

### 相關資訊連結：
- 自控式止痛: https://epaper.ntuh.gov.tw/health/201612/project_1.html
- 最適肌張力手術輔助處置: https://www.hch.gov.tw/?aid=626&pid=60&page_name=detail&iid=508
- 麻醉深度監測系統: https://heho.com.tw/archives/325974

病人的問題是: {message}
"""
        # 呼叫 Gemini API
        response = model.generate_content(context)
        return response.text
        
    except Exception as e:
        print(f"Gemini API error: {str(e)}")
        return "抱歉，我現在無法提供完整的回答。請稍後再試，或直接詢問您的醫師。"

if __name__ == '__main__':
    app.run(debug=True)