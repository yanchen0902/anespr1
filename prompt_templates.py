"""
Prompt templates for anesthesiology consultation system.
This module contains all the prompt templates used for different surgery types and question types.
"""

# Part 1: Age-specific anesthesia assistant prompts
# Pediatric prompt (under 18 years)
PEDIATRIC_PROMPT = """你是兒童麻醉諮詢助手。用像跟家長聊天的口吻回答，簡單、溫暖、150-200字內。醫學詞彙要立刻用白話解釋。

**重點**：術前8小時不吃東西；兩週內感冒要延期；孩子怕打針就用吸氣麻醉；術後家長陪伴很重要。
"""

# Adult prompt (18-64 years)
ADULT_PROMPT = """你是麻醉諮詢助手。用聊天的口吻回答，簡單、友善、150-200字內。醫學詞彙要立刻用白話解釋。

**重點**：術前8小時不吃東西、慢性病藥要調整；術中會監測狀況；術後止痛和恢復過程。
"""

# Geriatric prompt (65+ years)
GERIATRIC_PROMPT = """你是高齡病患麻醉諮詢助手。用親切耐心的口吻對家屬說明，簡單清楚、150-200字內。醫學詞彙要立刻用白話解釋。

**重點**：術前評估心肺記憶力；術前8小時不吃東西；術後可能短暫混亂、恢復較慢；麻醉深度監測器可降低風險。
"""

# Default prompt (fallback if age is unknown)
GENERAL_PROMPT = ADULT_PROMPT

# Part 3: Surgery-specific prompts
SURGERY_SPECIFIC_PROMPTS = {
    'heart': """心臟手術會用人工心肺機，術後住加護病房；自費腦血氧監測器能降低風險。""",

    'neurosurgery': """腦手術用全身麻醉，術後住加護病房；脊椎手術恢復室觀察即可。""",

    'lung': """肺手術用特殊管子讓一邊肺休息，術後要做肺部復健；麻醉深度監測器健保給付。""",

    'liver': """肝手術可能流較多血會準備輸血，術中會放特別的管子監測。""",

    'kidney': """腎手術會避免傷腎的麻醉藥，術後要多補水、保護腎臟。""",

    'fracture': """骨折手術下肢可考慮半身麻醉；術後用神經阻斷或自控式止痛，早點復健。""",

    'gi': """腸胃手術要禁食8小時防誤吸，術後可用硬膜外或腹橫肌阻斷止痛。""",

    'gynecology': """剖腹產用半身麻醉（抗凝血劑要告知）；子宮卵巢手術用全身麻醉。""",

    'urology': """膀胱鏡、攝護腺刮除可半身麻醉；達文西手術一定要全身麻醉。""",

    'ent': """耳鼻喉手術用全身麻醉，術後要觀察呼吸道順不順暢。""",

    'eye': """眼科手術用全身麻醉（兒童、複雜手術），會避免升高眼壓的藥。""",

    'thyroid': """甲狀腺手術會用神經監測器保護聲帶，術後觀察脖子腫脹和聲音變化。"""
}

# Part 4: Question-specific prompts
QUESTION_SPECIFIC_PROMPTS = {
    'fasting': """術前8小時不吃固體食物防誤吸；慢性病藥可配一點水吃。""",

    'pain': """止痛方式：打針、自控式按鈕、神經阻斷、硬膜外；痛前給藥比痛了才給效果好。""",
    
    'risks': """### 風險問題要詳細說明（200-250字）:

**風險等級**: 根據身體狀況給ASA等級（虛弱者3以上、心臟手術4）

**全身麻醉常見副作用**:
- 噁心想吐（10人有2-3人）
- 喉嚨痛（10個插管的人有4人）
- 頭痛頭暈、術後發抖

**半身麻醉常見副作用**: 麻的時間太長或太短、打針處麻麻的

**自費降低風險**:
- 麻醉深度監測器（防止手術中醒來）
- 肌肉鬆弛監測器（劑量剛好）
- 保溫毯（防低體溫）
- 止吐藥物
- 腦血氧監測器（心臟手術）

麻醉醫師會積極預防和處理這些問題。""",
    
    'recovery': """恢復室觀察1-2小時後回病房；大手術住加護病房幾天。醒來可能想吐、喉嚨痛、頭暈，要多休息做深呼吸。""",

    'anesthesia_types': """**用一句話說明各類型**: 全身麻醉完全睡著；半身麻醉下半身沒感覺但人醒著；局部麻醉只有手術處沒感覺。選擇要考慮手術部位和身體狀況，最終要跟麻醉醫師討論。""",

    'preparation': """### 術前準備要詳細說明（200-250字）:

**必做事項**:
- 禁食8小時（固體食物）
- 告知用藥：抗凝血劑、糖尿病藥物一定要說
- 術前檢查：抽血、X光等
- 卸掉指甲油（影響血氧監測）

**重要提醒**:
- 看住院須知了解流程
- 麻醉醫師會來評估，有問題都可以問
- 任何疑慮要提出來，不要憋在心裡

準備好個人物品。""",

    'general': """說明術前術中術後流程，根據手術類型客製化。

**自費建議**: 50歲以上建議麻醉深度監測；怕痛用自控式止痛；易暈或手術>2小時用止吐藥；怕冷或手術>1小時用保溫毯；心臟手術用腦血氧監測。"""
}

# Part 2: Patient info section formatting
def create_patient_info_section(patient_info):
    """Format patient information into a consistent section"""
    if not patient_info:
        return "### 病人資訊: 尚未提供完整資訊"
    
    name = patient_info.get('name', '未知')
    age = patient_info.get('age', '未知')
    sex_value = patient_info.get('sex', '未知')
    operation = patient_info.get('operation', '未知')
    medical_history = patient_info.get('medical_history', '無')
    worry = patient_info.get('worry', '無特別擔憂')
    
    patient_info_section = f"""### 病人資訊:
    - 姓名: {name}
    - 年齡: {age}歲
    - 性別: {sex_value}
    - 手術: {operation}
    - 病史: {medical_history}
    - 擔憂: {worry}"""
    
    return patient_info_section

# Helper functions for determining surgery and question types
def get_surgery_type(operation):
    """Determine the type of surgery based on the operation description"""
    if not operation:
        return 'general'
    
    operation = operation.lower()
    if any(word in operation for word in ['心臟', '心', '冠狀動脈', '瓣膜']):
        return 'heart'
    elif any(word in operation for word in ['肺', '胸腔', '氣胸']):
        return 'lung'
    elif any(word in operation for word in ['肝', '膽']):
        return 'liver'
    elif any(word in operation for word in ['腎', '腎臟']):
        return 'kidney'
    elif any(word in operation for word in ['骨折', '關節', '髖', '膝', '肘','骨']):
        return 'fracture'
    elif any(word in operation for word in ['腦', '腦部', '顱', '顱內', '脊椎', '神經外科','腦瘤','椎間盤']):
        return 'neurosurgery'
    elif any(word in operation for word in ['腸', '胃', '闌尾', '腹', '消化', '大腸', '小腸']):
        return 'gi'
    elif any(word in operation for word in ['子宮', '卵巢', '婦科', '剖腹產']):
        return 'gynecology'
    elif any(word in operation for word in ['攝護腺', '膀胱', '尿', '泌尿']):
        return 'urology'
    elif any(word in operation for word in ['耳', '鼻', '喉', '扁桃腺']):
        return 'ent'
    elif any(word in operation for word in ['眼', '白內障', '視網膜']):
        return 'eye'
    elif any(word in operation for word in ['甲狀腺', '甲狀線']):
        return 'thyroid'
    
    return 'general'

def get_question_type(message):
    """Determine the type of question based on keywords"""
    if not message:
        return 'general'
    
    message = message.lower()
    if any(word in message for word in ['禁食', '不能吃', '可以吃', '喝水', '進食']):
        return 'fasting'
    elif any(word in message for word in ['痛', '疼', '止痛', '舒緩', '不舒服']):
        return 'pain'
    elif any(word in message for word in ['風險', '危險', '併發症', '副作用', '後遺症', '恐懼']):
        return 'risks'
    elif any(word in message for word in ['恢復', '康復', '醒來', '出院', '返家', '多久']):
        return 'recovery'
    elif any(word in message for word in ['方式', '全身', '局部', '半身', '硬膜外', '脊椎']):
        return 'anesthesia_types'
    elif any(word in message for word in ['準備', '術前', '檢查', '評估', '注意事項']):
        return 'preparation'
    
    return 'general'
def get_age_appropriate_prompt(patient_info):
    """Select the appropriate prompt based on patient's age."""
    age = patient_info.get('age', None) if patient_info else None
    
    # Select appropriate prompt based on age group
    if age is not None:
        try:
            age_value = int(age)
            if age_value < 10:
                return PEDIATRIC_PROMPT
            elif age_value >= 65:
                return GERIATRIC_PROMPT
            else:
                return ADULT_PROMPT
        except (ValueError, TypeError):
            # If age can't be parsed as an integer, use default adult prompt
            return GENERAL_PROMPT
    else:
        # If no age information, use default prompt
        return GENERAL_PROMPT

# Main function to generate the complete four-part prompt (legacy)
def get_prompt(message, patient_info):
    """Generate a complete four-part prompt based on patient info and message"""
    # Part 1: Get age-appropriate general prompt
    general_part = get_age_appropriate_prompt(patient_info)
    
    # Part 2: Patient info section
    patient_info_part = create_patient_info_section(patient_info)
    
    # Part 3: Determine surgery type and get relevant prompt
    surgery_type = get_surgery_type(patient_info.get('operation', '')) if patient_info else 'general'
    surgery_part = SURGERY_SPECIFIC_PROMPTS.get(surgery_type, "### 一般手術麻醉考量:\n- 根據手術部位選擇適當麻醉方式\n- 術前評估整體健康狀況\n- 術中維持穩定生命徵象\n- 術後疼痛控制及恢復照護")
    
    # Part 4: Determine question type and get relevant prompt
    question_type = get_question_type(message)
    question_part = QUESTION_SPECIFIC_PROMPTS.get(question_type, QUESTION_SPECIFIC_PROMPTS['general'])
    
    # Combine all parts into the final prompt
    return f"""
{general_part}

{patient_info_part}

{surgery_part}

{question_part}

問題: {message}
"""

# New function for Azure OpenAI with separate system and user prompts
def get_separated_prompts(message, patient_info):
    """Generate separate system and user prompts for Azure OpenAI
    
    Returns:
        tuple: (system_prompt, user_prompt)
            - system_prompt: Part 1 (age-appropriate prompt) + Part 3 (surgery-specific)
            - user_prompt: Part 2 (patient info) + Part 4 (question-specific) + message
    """
    # Part 1: Get age-appropriate general prompt (SYSTEM)
    general_part = get_age_appropriate_prompt(patient_info)
    
    # Part 2: Patient info section (USER)
    patient_info_part = create_patient_info_section(patient_info)
    
    # Part 3: Determine surgery type and get relevant prompt (SYSTEM)
    surgery_type = get_surgery_type(patient_info.get('operation', '')) if patient_info else 'general'
    surgery_part = SURGERY_SPECIFIC_PROMPTS.get(surgery_type, "### 一般手術麻醉考量:\n- 根據手術部位選擇適當麻醉方式\n- 術前評估整體健康狀況\n- 術中維持穩定生命徵象\n- 術後疼痛控制及恢復照護")
    
    # Part 4: Determine question type and get relevant prompt (USER)
    question_type = get_question_type(message)
    question_part = QUESTION_SPECIFIC_PROMPTS.get(question_type, QUESTION_SPECIFIC_PROMPTS['general'])
    
    # Combine system context (Part 1 + Part 3)
    system_prompt = f"""
{general_part}

{surgery_part}
"""
    
    # Combine user context (Part 2 + Part 4 + message)
    user_prompt = f"""
{patient_info_part}

{question_part}

問題: {message}
"""
    
    return system_prompt.strip(), user_prompt.strip()

# Backward compatibility with existing code
def format_prompt(template, patient_info_section, message):
    """Format a prompt template with patient info and message (legacy support)"""
    return template.format(
        patient_info_section=patient_info_section,
        message=message
    )
