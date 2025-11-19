# Prompt Testing Tool

快速測試麻醉諮詢聊天機器人 Prompt 的獨立工具

## 功能特色

✅ **快速測試** - 無需填寫病患資料，直接選擇模板病患開始對話
✅ **模板病患** - 預設 5 種不同情境的病患模板
✅ **雙模型支援** - 同時測試 Primary Model (Gemini/Ollama) 和 Azure OpenAI
✅ **Prompt 預覽** - 即時查看發送給 AI 的完整 Prompt
✅ **獨立運行** - 與主系統完全分離，不影響生產環境

## 快速開始

### 1. 啟動測試伺服器

```bash
# 在專案根目錄執行
python testing/test_app.py
```

### 2. 訪問測試介面

開啟瀏覽器訪問：`http://localhost:5000`

### 3. 開始測試

1. **選擇模板病患** - 從左側選擇一個預設病患
2. **開始對話** - 在右側輸入問題，測試 AI 回應
3. **查看 Prompt** - 點擊回應下方的「查看 Prompt」按鈕
4. **清除/重置** - 使用左下角按鈕清除對話或重新選擇病患

## 模板病患列表

### 1. elderly_cardiac (王大明)
- **描述**: 75歲男性，心臟手術，CFS 5分（輕度虛弱）
- **適用場景**: 測試老年病患、心臟手術相關 Prompt
- **特點**: 多重慢性病（高血壓、糖尿病、冠狀動脈疾病）

### 2. young_orthopedic (李小華)
- **描述**: 28歲女性，骨科手術，CFS 1分（健康）
- **適用場景**: 測試年輕健康病患、首次手術焦慮
- **特點**: 無慢性病，有藥物過敏（青黴素）

### 3. middle_general (陳美玲)
- **描述**: 52歲女性，一般外科，CFS 3分（控制良好）
- **適用場景**: 測試中年病患、術後止痛相關問題
- **特點**: 高血壓控制良好，關注疼痛管理

### 4. pediatric (張小明)
- **描述**: 8歲男童，耳鼻喉科手術，CFS 1分（健康）
- **適用場景**: 測試兒童病患、家長關注點
- **特點**: 年齡 < 18 歲，觸發兒童專用 Prompt

### 5. high_risk (林老先生)
- **描述**: 82歲男性，骨科手術，CFS 7分（嚴重虛弱）
- **適用場景**: 測試高風險病患、複雜病史處理
- **特點**: 多重慢性病、多種藥物、高 CFS 分數

## 測試建議

### 測試不同年齡層 Prompt
```
- 兒童 (< 18): pediatric (張小明)
- 成人 (18-65): young_orthopedic (李小華), middle_general (陳美玲)
- 老年 (> 65): elderly_cardiac (王大明), high_risk (林老先生)
```

### 測試不同 CFS 分數
```
- CFS 1-3 (健康/控制良好): young_orthopedic, middle_general, pediatric
- CFS 4-5 (輕度虛弱): elderly_cardiac
- CFS 6-9 (嚴重虛弱): high_risk
```

### 測試不同手術類型
```
- 心臟手術: elderly_cardiac
- 骨科手術: young_orthopedic, high_risk
- 一般外科: middle_general
- 耳鼻喉科: pediatric
```

## 常見問題 (FAQ)

### Q: 測試資料會存入資料庫嗎？
**A:** 不會。測試工具使用獨立的 Flask session，不會寫入任何資料到 `patients.db`。

### Q: 可以同時運行測試工具和主系統嗎？
**A:** 可以。測試工具使用 port 5000，主系統使用 port 8080，互不干擾。

### Q: 如何新增自己的模板病患？
**A:** 編輯 `testing/template_patients.py`，在 `TEMPLATE_PATIENTS` 字典中新增項目。

### Q: 測試工具支援哪些 AI 模型？
**A:** 根據 `.env` 設定：
- `USE_LOCAL_MODEL=false` → Gemini + Azure OpenAI
- `USE_LOCAL_MODEL=true` → Ollama + Azure OpenAI

### Q: 為什麼 AI 回應顯示「AI response not available」？
**A:** 檢查：
1. `.env` 檔案中的 API keys 是否正確設定
2. 網路連線是否正常
3. Ollama 服務是否啟動（如使用本地模型）

## 檔案結構

```
testing/
├── test_app.py              # Flask 測試應用程式
├── template_patients.py     # 模板病患資料定義
├── templates/
│   └── prompt_test.html    # 測試介面 HTML
└── README.md               # 本說明文件
```

## 技術細節

### 匯入主系統模組
測試工具會自動匯入主系統的關鍵模組：
- `prompt_templates.py` - Prompt 生成邏輯
- `app_tocloud.py` - AI 回應生成函數

### Session 管理
- 每個瀏覽器 session 獨立
- 支援病患切換和對話清除
- 不影響主系統的 session

### 回應資訊
測試介面會顯示：
- Primary Model 回應 (Gemini/Ollama)
- Azure OpenAI 回應
- 完整 Prompt (Gemini/Ollama 使用)
- System Prompt (Azure 使用)
- User Prompt (Azure 使用)

## 開發與維護

### 新增模板病患範例

```python
# 在 template_patients.py 中新增
"template_id": {
    "name": "病患姓名",
    "age": 年齡,
    "gender": "性別",
    "operation": "手術名稱",
    "cfs_score": CFS分數,
    "concerns": "主要關注點",
    "description": "簡短描述",
    "medical_history": {
        "chronic_conditions": ["慢性病列表"],
        "medications": ["藥物列表"],
        "allergies": ["過敏列表"],
        "past_surgeries": ["過去手術"]
    }
}
```

### 修改測試介面
編輯 `testing/templates/prompt_test.html`，使用標準 HTML/CSS/JavaScript。

## 注意事項

⚠️ **僅供開發測試使用** - 不應部署到生產環境
⚠️ **不記錄資料** - 測試對話不會儲存，關閉瀏覽器即清除
⚠️ **API 用量** - 每次對話會呼叫真實 API，注意用量和費用

## 支援

如有問題或建議，請參考主專案的 `CLAUDE.md` 或聯絡開發團隊。
