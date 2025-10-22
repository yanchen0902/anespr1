# 麻醉前諮詢聊天機器人 (Anesthesiology Pre-Consultation Chatbot)

## 專案概述 (Project Overview)

本系統是為麻醉科設計的智能諮詢助手，提供手術前麻醉相關諮詢服務。系統通過結構化的對話流程收集患者資訊，並使用先進的AI模型提供相關的麻醉前準備建議。

This system is an intelligent consultation assistant designed for anesthesiology, providing pre-surgical anesthesia consultation services. The system collects patient information through a structured dialogue flow and uses advanced AI models to provide relevant pre-anesthesia preparation advice.

---

## 主要功能 (Key Features)

### 患者諮詢流程 (Patient Consultation Flow)
- ✅ 按步驟收集患者基本資訊（姓名、年齡、性別、手術類型等）
- ✅ 支持手術類型選擇按鈕（心臟、肺臟、肝臟、腎臟、骨折等）
- ✅ 骨折位置細分選項（上肢、下肢、肋骨、脊椎）
- ✅ 支持多選醫療病史和擔憂項目
- ✅ AI 智能問答系統（使用 Gemini/Ollama + Azure OpenAI）
- ✅ 諮詢摘要生成

### AI 雙模型系統 (Dual AI Model System)
- **主要模型**: Google Gemini 2.0 Flash 或 Ollama Gemma3（可通過環境變數切換）
- **備用模型**: Azure OpenAI（始終調用以進行比較和備份）
- **模型切換**: 通過 `USE_LOCAL_MODEL` 環境變數控制
- **回應儲存**: 兩個模型的回應都儲存在數據庫中供比較

### 語音互動 (Voice Interaction)
- 🎤 中文語音辨識（zh-TW）
- 🔊 文字轉語音（TTS）機器人回應
- 🎙️ 麥克風權限處理
- 📊 視覺錄音反饋
- ⚡ 自動發送語音辨識結果

### 管理員功能 (Admin Features)
- 🔐 安全的管理員登入系統
- 📊 患者諮詢記錄儀表板（總計、週統計）
- 🔍 患者詳細諮詢對話查看
- ⭐ AI回應品質評估系統（準確性、可信度、同理心）
- 👍 回應反饋系統（喜歡、不喜歡、禁用）
- 📈 反饋統計分析頁面
- 🔄 模型回應比較功能

### 數據管理 (Data Management)
- 💾 優化對話歷史儲存機制
- 🗄️ 患者資訊數據庫存儲（SQLite/MySQL）
- 👥 支持同名患者識別
- 🔄 雙模型回應記錄

---

## 技術棧 (Tech Stack)

- **後端框架**: Python 3.9+ / Flask 2.x
- **數據庫**:
  - 本地開發: SQLite (`patients.db`)
  - 生產環境: Google Cloud SQL (MySQL)
- **AI 模型**:
  - Google Gemini 2.0 Flash API
  - Azure OpenAI API
  - Ollama (Gemma3) - 本地模型
- **ORM**: SQLAlchemy / Flask-SQLAlchemy
- **認證**: Flask-Login
- **部署**: Google App Engine (可選)
- **前端**: HTML5, CSS3, JavaScript (Web Speech API)

---

## 專案結構 (Project Structure)

### 完整文件列表

```
anespr1/
├── 📁 核心應用文件 (Core Application Files)
├── app_tocloud.py              # 主應用程序（Flask routes, AI integration）
├── models.py                   # 數據庫模型定義
├── prompt_templates.py         # AI prompt 模板（醫療場景專用）
├── requirements.txt            # Python 依賴（生產環境）
├── requirements.linux.txt      # ✅ Linux 部署依賴
├── .env.example                # 環境變數範例
├── .env.linux                  # ✅ Linux 環境變數範例
├── CLAUDE.md                   # 開發者參考文檔（詳細）
├── DEPLOYMENT.md               # 部署指南
├── README.md                   # 本文件
│
├── 📁 前端文件 (Frontend Files)
├── templates/                  # HTML 模板
│   ├── index.html              # 患者主界面
│   ├── admin_dashboard.html    # 管理員儀表板
│   ├── patient_detail.html     # 患者詳情頁面
│   ├── consultation_summary.html  # 諮詢摘要
│   ├── feedback_stats.html     # 反饋統計
│   ├── login.html              # 管理員登入
│   ├── patient_emr_info.html   # 病歷資訊輸入
│   ├── patient_id_input.html   # 患者 ID 輸入
│   └── *.html                  # 其他資訊頁面
│
├── static/                     # 靜態資源
│   ├── css/style.css           # 樣式表
│   └── images/                 # 圖片資源
│
├── 📁 數據庫相關 (Database Related)
├── migrations/                 # ⚠️ 數據庫遷移腳本（全新安裝不需要！）
│   ├── README.md               # 遷移文檔
│   ├── add_feedback_fields.py  # 添加反饋欄位
│   ├── add_openai_response.py  # 添加 OpenAI 回應欄位
│   ├── add_evaluation_table.py # 創建評估表
│   └── add_evaluator_name.py   # 添加評估者名稱
│
├── init_db.py                  # ✅ 初始化數據庫（Linux 部署用這個！）
├── create_admin.py             # ✅ 創建管理員帳號（Linux 部署用這個！）
├── check_database.py           # ✅ 檢查數據庫狀態（診斷工具）
├── patients.db                 # SQLite 數據庫（本地開發）
│
├── 📁 測試工具 (Testing Tools - Optional)
├── test_ollama_gemma.py        # Ollama 模型連接測試
├── test_login.py               # 登入功能測試
│
├── 📁 Google Cloud 專用文件 (Google Cloud ONLY - Linux 不需要)
├── create_admin_cloud.py       # ❌ 僅用於 Google Cloud App Engine
├── setup_mysql.py              # ❌ 僅用於 Google Cloud SQL 設置
├── app.yaml                    # ❌ 僅用於 Google App Engine 配置
└── .gcloudignore               # ❌ 僅用於 GCloud 部署
```

### 📋 Linux 部署文件清單

**✅ Linux 工程師必需的文件：**
- `app_tocloud.py`, `models.py`, `prompt_templates.py`
- `requirements.linux.txt` (依賴列表)
- `.env.linux` → 複製為 `.env` 並填入配置
- `init_db.py` (初始化數據庫)
- `create_admin.py` (創建管理員)
- `templates/` 和 `static/` 整個資料夾

**📚 可選但有用的文件：**
- `check_database.py` (診斷數據庫問題)
- `test_ollama_gemma.py` (測試 Ollama 連接)
- `CLAUDE.md`, `README.md` (文檔)

**❌ Linux 部署不需要的文件：**
- `create_admin_cloud.py` (僅 Google Cloud)
- `setup_mysql.py` (僅 Google Cloud)
- `app.yaml` (僅 Google App Engine)
- `.gcloudignore` (僅 Google Cloud)
- `migrations/` 資料夾 (全新安裝不需要，僅用於升級現有數據庫)
- `patients.db` (開發數據庫，不要上傳到生產環境)

---

## 環境配置 (Environment Setup)

### 必要的環境變數 (Required Environment Variables)

創建 `.env` 文件（參考 `.env.example`）:

```bash
# AI Model Configuration
GOOGLE_API_KEY=your_gemini_api_key_here
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name

# Model Selection (True = Ollama, False = Gemini)
USE_LOCAL_MODEL=False

# Ollama Configuration (if using local model)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:latest

# Database Configuration (for cloud deployment)
# DATABASE_URL=mysql+pymysql://user:password@host/database
```

**重要提示 (Important Notes)**:
- ⚠️ `.env` 文件中 `=` 前後不要有空格
- ⚠️ 不要將 `.env` 文件提交到 Git（已在 `.gitignore` 中）
- ⚠️ `USE_LOCAL_MODEL=False` 使用 Gemini + Azure OpenAI
- ⚠️ `USE_LOCAL_MODEL=True` 使用 Ollama + Azure OpenAI

---

## 本地開發環境 (Local Development Setup)

### 1. 安裝 Python 依賴

```bash
# 創建虛擬環境（推薦）
python -m venv venv

# 啟動虛擬環境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 2. 配置環境變數

```bash
# 複製範例文件
cp .env.example .env

# 編輯 .env 並填入你的 API keys
# 使用文本編輯器打開 .env 並填入實際的 API 金鑰
```

### 3. 初始化數據庫

```bash
# 全新安裝（創建所有表）
python init_db.py

# 這將創建:
# - patients.db (SQLite 數據庫)
# - 所有必要的表
# - 默認管理員帳號 (username: admin, password: admin123)
```

### 4. 創建管理員用戶（可選，如果需要額外管理員）

```bash
python create_admin.py
```

### 5. 運行本地開發服務器

```bash
python app_tocloud.py
```

應用程序將在 `http://localhost:8080` 上運行

**訪問界面**:
- 患者端: `http://localhost:8080/`
- 管理員登入: `http://localhost:8080/admin/login`
- 默認管理員帳號: `admin` / `admin123`

---

## Linux 部署 (Linux Deployment)

> **⚠️ 重要提示 (IMPORTANT NOTE FOR ENGINEERS):**
> **全新 Linux 部署只需運行 `init_db.py`，不需要使用 `migrations/` 資料夾！**
> **For fresh Linux deployment, only run `init_db.py` - you do NOT need the `migrations/` folder!**
> `migrations/` 資料夾僅用於升級現有數據庫，全新安裝會自動創建最新架構。
> The `migrations/` folder is only for upgrading existing databases. Fresh installations automatically create the latest schema.

### 系統需求

- Python 3.9 或更高版本
- pip
- 虛擬環境支持（推薦）
- MySQL/MariaDB（生產環境）或 SQLite（測試環境）

### Linux 快速部署步驟 (全新安裝)

```bash
# 1. 克隆或上傳項目到 Linux 服務器
cd /path/to/anespr1

# 2. 創建虛擬環境
python3 -m venv venv
source venv/bin/activate

# 3. 安裝 Linux 依賴
pip install -r requirements.linux.txt

# 4. 配置環境變數
cp .env.linux .env
# 編輯 .env 並填入實際配置
nano .env

# 5. 初始化數據庫（創建所有表，使用最新架構）
python3 init_db.py
# ⚠️ 注意：不要運行 migrations/ 資料夾中的腳本！init_db.py 會自動創建最新架構

# 6. 創建管理員
python3 create_admin.py

# 7. 測試運行
python3 app_tocloud.py

# 8. 生產部署（使用 gunicorn）
gunicorn -w 4 -b 0.0.0.0:8080 app_tocloud:app
```

### 使用 systemd 服務（推薦）

創建服務文件 `/etc/systemd/system/anespr1.service`:

```ini
[Unit]
Description=Anesthesiology Pre-Consultation Chatbot
After=network.target

[Service]
User=your_user
WorkingDirectory=/path/to/anespr1
Environment="PATH=/path/to/anespr1/venv/bin"
ExecStart=/path/to/anespr1/venv/bin/gunicorn -w 4 -b 0.0.0.0:8080 app_tocloud:app
Restart=always

[Install]
WantedBy=multi-user.target
```

啟動服務:
```bash
sudo systemctl daemon-reload
sudo systemctl start anespr1
sudo systemctl enable anespr1
sudo systemctl status anespr1
```

---

## 數據庫管理 (Database Management)

### 全新安裝 (Fresh Installation - 推薦用於 Linux 部署)

```bash
python init_db.py
```

這將創建所有表並使用最新的架構。**全新安裝不需要運行任何 migration 腳本！**

> **✅ 對於全新 Linux 部署：只運行 `init_db.py` 即可！**
>
> `init_db.py` 會自動創建包含所有最新欄位的完整數據庫架構：
> - Patient, ChatHistory, SelfPayItem, ChatbotEvaluation, User 表
> - 所有反饋欄位 (feedback, feedback_at)
> - 所有 OpenAI 欄位 (openai_response, preferred_response)
> - 所有評估欄位 (evaluator_name, accuracy_score, etc.)

### 從舊版本升級 (Upgrading Existing Database - 僅用於已有數據的情況)

如果你有現有的數據庫需要升級:

1. **備份數據庫**
   ```bash
   cp patients.db patients.db.backup
   ```

2. **檢查當前架構**
   ```bash
   python check_database.py
   ```

3. **運行必要的遷移**
   ```bash
   # 查看遷移文檔
   cat migrations/README.md

   # 運行需要的遷移腳本
   python migrations/add_feedback_fields.py
   python migrations/add_openai_response.py
   python migrations/add_evaluation_table.py
   python migrations/add_evaluator_name.py
   ```

詳細的遷移說明請參閱 `migrations/README.md`

---

## Google Cloud 部署 (Deployment to Google Cloud)

### 先決條件

1. 安裝 Google Cloud SDK
2. 配置 Google Cloud 項目

### 部署步驟

```bash
# 1. 確保已配置 app.yaml
cp app.yaml.example app.yaml
# 編輯 app.yaml 並更新配置

# 2. 設置 Cloud SQL（如果使用）
python setup_mysql.py

# 3. 創建雲端管理員
python create_admin_cloud.py

# 4. 部署應用
gcloud app deploy

# 5. 查看應用
gcloud app browse
```

### Cloud SQL 配置

- **項目 ID**: anespr1-asia-east
- **實例**: anespr1-asia-east:asia-east1:anespr1
- **連接**: `mysql+pymysql://root:anespr123@/patients?unix_socket=/cloudsql/anespr1-asia-east:asia-east1:anespr1`

更多部署細節請參閱 `DEPLOYMENT.md`

---

## 使用說明 (Usage Instructions)

### 患者端操作流程 (Patient Side)

1. 訪問應用主頁 (`/`)
2. 輸入基本資訊:
   - 姓名
   - 年齡
   - 性別
3. 選擇手術類型（點擊按鈕或手動輸入）
4. 選擇醫療病史（可多選）
5. 填寫擔憂事項
6. 進入 AI 諮詢聊天界面:
   - 輸入問題（文字或語音）
   - 查看 AI 回應
   - 繼續對話或結束諮詢
7. 查看諮詢摘要
8. 可選：填寫自費項目表單

### 管理員端操作 (Admin Side)

1. **登入**: 訪問 `/admin/login`
   - 預設帳號: `admin`
   - 預設密碼: `admin123`

2. **儀表板** (`/admin/dashboard`):
   - 查看總病患數、諮詢數統計
   - 瀏覽患者列表
   - 點擊「查看詳情」進入患者詳細頁面

3. **患者詳情頁面** (`/admin/patient/<id>`):
   - 查看患者基本資訊
   - 查看完整對話記錄
   - 比較 Gemini 和 OpenAI 的回應
   - 對每個回應進行反饋（👍 喜歡 / 👎 不喜歡 / 🚫 禁用）
   - 選擇偏好的模型回應
   - 對整體諮詢進行評分（準確性、可信度、同理心）

4. **統計頁面** (`/admin/feedback_stats`):
   - 查看整體反饋統計
   - 分析 AI 回應質量
   - 查看評估分數分佈

---

## 開發與測試 (Development & Testing)

### 測試腳本

```bash
# 測試 Ollama 模型連接
python test_ollama_gemma.py

# 測試登入功能
python test_login.py

# 檢查數據庫狀態
python check_database.py
```

### 日誌記錄

應用程序使用 Python logging 模塊。日誌級別和格式在 `app_tocloud.py` 中配置。

查看日誌:
```bash
# 控制台輸出（開發模式）
python app_tocloud.py

# 生產環境（使用 gunicorn）
gunicorn --log-level debug app_tocloud:app
```

---

## 系統優化記錄 (System Optimization Records)

### 最近更新 (Recent Updates)

- ✅ **2025-01-29**: Azure OpenAI Prompt 結構優化
  - 實現分離的系統和用戶提示
  - 改進回應質量

- ✅ **2025-09-21**: 模型切換系統增強
  - 雙模型回應系統（主模型 + Azure OpenAI）
  - 通過環境變數切換 Gemini/Ollama
  - 數據庫儲存兩種回應供比較

- ✅ 解決會話 cookie 過大問題，優化會話存儲
- ✅ 增強用戶界面，添加手術類型選擇按鈕
- ✅ 改進評估標準術語，更符合醫療實踐
- ✅ 修復聊天歷史保存功能
- ✅ 實現患者精確識別，解決同名患者問題
- ✅ 添加語音交互功能（語音輸入和 TTS）

詳細更新記錄請參閱 `CLAUDE.md`

---

## 常見問題 (FAQ)

### Q: 如何切換 AI 模型？
**A**: 在 `.env` 文件中設置 `USE_LOCAL_MODEL`:
- `USE_LOCAL_MODEL=False` → 使用 Gemini + Azure OpenAI
- `USE_LOCAL_MODEL=True` → 使用 Ollama + Azure OpenAI

### Q: 如何重置管理員密碼？
**A**: 運行 `python create_admin.py` 並創建新的管理員帳號，或直接在數據庫中更新。

### Q: 數據庫遷移失敗怎麼辦？
**A**:
1. 檢查數據庫備份
2. 查看 `migrations/README.md`
3. 運行 `python check_database.py` 診斷問題
4. 如有必要，從備份恢復並重試

### Q: 如何備份數據？
**A**:
- **SQLite**: `cp patients.db patients.db.backup`
- **MySQL**: 使用 `mysqldump` 或雲端備份工具

### Q: 語音功能不工作？
**A**:
- 確保使用 HTTPS（或 localhost）
- 瀏覽器需支持 Web Speech API（Chrome/Edge）
- 檢查麥克風權限

---

## 安全注意事項 (Security Considerations)

- 🔒 **生產環境必須更改默認管理員密碼**
- 🔒 不要將 `.env` 文件提交到版本控制
- 🔒 使用 HTTPS 部署（特別是語音功能需要）
- 🔒 定期備份數據庫
- 🔒 限制管理員帳號數量
- 🔒 遵守醫療數據隱私法規（HIPAA, GDPR 等）

---

## 技術支持與文檔 (Technical Support & Documentation)

- **開發者文檔**: `CLAUDE.md` - 詳細的開發指南和代碼參考
- **部署指南**: `DEPLOYMENT.md` - 完整的部署流程
- **遷移文檔**: `migrations/README.md` - 數據庫遷移說明
- **問題報告**: 請聯繫系統管理員或開發團隊

---

## 授權 (License)

© 2025 麻醉科預約系統團隊 保留所有權利

---

## 貢獻者 (Contributors)

本系統為醫療專業人員設計，需要醫療領域專業知識進行提示詞更新和功能擴展。

---

**版本**: 2.0
**最後更新**: 2025-10-21
**狀態**: 生產就緒 (Production Ready)
