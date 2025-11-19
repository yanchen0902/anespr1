"""
Template Patient Data for Prompt Testing
Quick-access patient profiles for testing chatbot prompts without manual data entry
"""

TEMPLATE_PATIENTS = {
    "elderly_cardiac": {
        "name": "王大明",
        "age": 75,
        "gender": "男",
        "operation": "心臟繞道手術",
        "cfs_score": 5,
        "concerns": "擔心麻醉風險，有心臟病史",
        "description": "75歲男性，心臟手術，CFS 5分（輕度虛弱）",
        "medical_history": {
            "chronic_conditions": ["高血壓", "糖尿病", "冠狀動脉疾病"],
            "medications": ["降血壓藥", "降血糖藥", "抗凝血劑"],
            "allergies": [],
            "past_surgeries": ["膽囊切除術（10年前）"]
        }
    },

    "young_orthopedic": {
        "name": "李小華",
        "age": 28,
        "gender": "女",
        "operation": "膝關節鏡手術",
        "cfs_score": 1,
        "concerns": "第一次手術，很緊張",
        "description": "28歲女性，骨科手術，CFS 1分（健康）",
        "medical_history": {
            "chronic_conditions": [],
            "medications": [],
            "allergies": ["青黴素"],
            "past_surgeries": []
        }
    },

    "middle_general": {
        "name": "陳美玲",
        "age": 52,
        "gender": "女",
        "operation": "腹腔鏡膽囊切除術",
        "cfs_score": 3,
        "concerns": "怕痛，想了解術後止痛方式",
        "description": "52歲女性，一般外科，CFS 3分（控制良好）",
        "medical_history": {
            "chronic_conditions": ["高血壓"],
            "medications": ["降血壓藥"],
            "allergies": [],
            "past_surgeries": ["剖腹產（20年前）"]
        }
    },

    "pediatric": {
        "name": "張小明",
        "age": 8,
        "gender": "男",
        "operation": "扁桃腺切除術",
        "cfs_score": 1,
        "concerns": "家長擔心全身麻醉對小孩的影響",
        "description": "8歲男童，耳鼻喉科手術，CFS 1分（健康）",
        "medical_history": {
            "chronic_conditions": [],
            "medications": [],
            "allergies": [],
            "past_surgeries": []
        }
    },

    "high_risk": {
        "name": "林老先生",
        "age": 82,
        "gender": "男",
        "operation": "髖關節置換術",
        "cfs_score": 7,
        "concerns": "多重慢性病，擔心無法承受手術",
        "description": "82歲男性，骨科手術，CFS 7分（嚴重虛弱）",
        "medical_history": {
            "chronic_conditions": ["高血壓", "糖尿病", "慢性腎臟病", "心律不整", "COPD"],
            "medications": ["降血壓藥", "降血糖藥", "心律藥物", "利尿劑", "支氣管擴張劑"],
            "allergies": ["磺胺類藥物"],
            "past_surgeries": ["白內障手術", "疝氣修補術", "心導管檢查"]
        }
    }
}

def get_template_patient(template_id):
    """Get a template patient by ID"""
    return TEMPLATE_PATIENTS.get(template_id)

def get_all_templates():
    """Get all available template patients"""
    return TEMPLATE_PATIENTS

def create_patient_session_data(template_id):
    """
    Create session data for a template patient
    Returns dict that can be directly used to populate Flask session
    """
    patient = get_template_patient(template_id)
    if not patient:
        return None

    return {
        'patient_name': patient['name'],
        'patient_age': patient['age'],
        'patient_gender': patient['gender'],
        'operation': patient['operation'],
        'cfs_score': patient['cfs_score'],
        'concerns': patient['concerns'],
        'current_step': 'chat',  # Start directly at chat
        'medical_history': patient['medical_history']
    }
