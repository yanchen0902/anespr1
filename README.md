# 麻醉前諮詢聊天機器人 (Anesthesiology Pre-Consultation Chatbot)

## 專案概述 (Project Overview)

本系統是為麻醉科設計的智能諮詢助手，提供手術前麻醉相關諮詢服務。系統通過結構化的對話流程收集患者資訊，並使用先進的AI模型提供相關的麻醉前準備建議。

This system is an intelligent consultation assistant designed for anesthesiology, providing pre-surgical anesthesia consultation services. The system collects patient information through a structured dialogue flow and uses advanced AI models to provide relevant pre-anesthesia preparation advice.

## 主要功能 (Key Features)

### 患者諮詢流程 (Patient Consultation Flow)
- 按步驟收集患者基本資訊（姓名、年齡、性別、手術類型等）
- 支持手術類型選擇按鈕（心臟、肺臟、肝臟、腎臟、骨折等）
- 骨折位置細分選項（上肢、下肢、肋骨、脊椎）
- 支持多選醫療病史和擔憂項目

### 語音互動 (Voice Interaction)
- 中文語音辨識（zh-TW）
- 麥克風權限處理
- 視覺錄音反饋
- 自動發送語音辨識結果
- 機器人回應文字轉語音功能

### 管理員功能 (Admin Features)
- 安全的管理員登入系統
- 患者諮詢記錄查看
- 諮詢對話品質評估（符合醫療常規、語意流暢度）
- 回應反饋系統（喜歡、不喜歡、禁用）
- 反饋統計頁面

### 數據管理 (Data Management)
- 優化對話歷史儲存機制
- 患者資訊數據庫存儲
- 支持同名患者識別

## 技術棧 (Tech Stack)

- **後端**: Python Flask
- **AI模型**: Google Gemini API, OpenAI API
- **數據庫**: Cloud SQL (MySQL)
- **部署**: Google App Engine
- **前端**: HTML, CSS, JavaScript

## 環境配置 (Environment Setup)

### 本地開發環境 (Local Development)

1. 安裝Python依賴:
```
pip install -r requirements.txt
```

2. 設置環境變數:
複製`.env.example`到`.env`並填入必要的API密鑰和配置

3. 初始化數據庫:
```
python init_db.py
```

4. 創建管理員用户:
```
python create_admin.py
```

5. 運行本地服務器:
```
python app_tocloud.py
```

### 部署到Google Cloud (Deployment to Google Cloud)

1. 確保已安裝並配置Google Cloud SDK

2. 配置app.yaml:
複製`app.yaml.example`到`app.yaml`並更新適當的配置

3. 設置Cloud SQL:
```
python setup_mysql.py
```

4. 部署應用:
```
gcloud app deploy
```

## 數據庫配置 (Database Configuration)

### Cloud SQL 配置
- 項目ID: anespr1-asia-east
- Cloud SQL 實例: anespr1-asia-east:asia-east1:anespr1
- 連接字符串: mysql+pymysql://root:anespr123@/patients?unix_socket=/cloudsql/anespr1-asia-east:asia-east1:anespr1

## 使用說明 (Usage Instructions)

### 患者端 (Patient Side)
1. 訪問應用主頁
2. 按提示輸入個人資訊（姓名、年齡等）
3. 選擇手術類型和相關醫療條件
4. 在聊天界面提問麻醉相關問題
5. 可選使用語音功能進行交互

### 管理員端 (Admin Side)
1. 訪問`/admin`頁面並登入
2. 在主面板查看所有患者記錄
3. 查看個別患者的詳細對話記錄
4. 對AI回應進行評價和反饋
5. 查看回應反饋統計

## 系統優化記錄 (System Optimization Records)

- 解決會話cookie過大問題，優化會話存儲
- 增強用戶界面，添加手術類型選擇按鈕
- 改進評估標準術語，更符合醫療實踐
- 修復聊天歷史保存功能
- 實現患者精確識別，解決同名患者問題
- 添加語音交互功能

## 授權 (License)

© 2025 麻醉科預約系統團隊 保留所有權利
