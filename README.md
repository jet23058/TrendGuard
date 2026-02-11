# 趨勢守衛者 (TrendGuard)

🎯 基於 Jesse Livermore 交易哲學設計的台股觀察清單與分析工具。
結合現代化的網頁技術與 AI 智能分析，協助投資人理性判斷市場趨勢。

## ✨ 功能特色

- **動能掃描** - 自動篩選強勢股
  - 📊 **連續紅K篩選**：支援「至少 N 天」與「剛好 N 天」的精確篩選，快速鎖定動能股。
  - 🔥 **強勢股過濾**：可自訂過濾門檻（如漲幅 > 5%），剔除緩漲或動能不足的標的。
  - 🏆 **市值排行**：提供 Top 100/500 大型股篩選，專注於權值股操作。
  - 🟢 **異動偵測**：自動比對每日清單，標示新進榜（NEW）與被剔除的股票。
  - 🏭 **產業熱點**：自動將股票依產業分類，一眼看穿主流族群。

- **AI 智能投顧** - 整合 Google Gemini 生成每日深度報告
  - 📝 **每日市場分析**：由 AI 模擬專業分析師口吻，撰寫每日盤勢摘要與個股點評。
  - 📊 **全市場多空統計**：自動計算當日掃描範圍內的漲跌家數 (Market Breadth)，掌握大盤氣氛。
  - 🛡️ **人性化與合規**：內建 Humanizer 機制，確保文章語氣自然並嚴格遵守台灣金融法規（中性用語）。

- **個人化庫存管理**
  - ☁️ **雲端同步**：支援 Google 登入 (Firebase)，跨裝置同步您的關注清單。
  - 📸 **OCR 匯入**：上傳券商 App 庫存截圖，自動辨識股票代碼與股數。
  - 📋 **CSV 匯入**：支援 Excel/CSV 格式快速貼上匯入大量持股。
  - 🔄 **未上市同步**：針對未在每日強勢榜單中的庫存股，支援即時行情同步與技術分析。

- **技術分析儀表板**
  - 📉 **互動式 K 線圖**：整合 Recharts 提供互動式價格走勢圖。
  - 🚦 **策略訊號**：自動標示關鍵技術點位（如 KD 黃金交叉、突破均線）。
  - ⚠️ **風險控管**：自動計算並標示 10% 支撐風險位與 20% 獲利目標區。
  - 🚫 **交易限制**：自動檢查證交所清單，標示「禁當沖」與「處置」狀態。

## 🗺️ 專案規劃 (Roadmap)

詳細的開發計畫與架構說明請參考 [PROJECT_PLAN.md](PROJECT_PLAN.md)。

## 🚀 快速開始

### 1. 環境變數設定

複製 `.env.example` 並編輯為 `.env`：

```bash
cp .env.example .env
```

**重要環境變數：**

- `STOCK_DATA_PROVIDER`: 股價資料來源選擇
  - `twse` (預設): 台灣證券交易所 API - **無 API 上限**，適合生產環境
  - `finmind`: FinMind API - 功能豐富，但有速率限制
  
- `FINMIND_API_TOKEN`: FinMind API Token (僅在使用 finmind provider 時需要)
  - 申請網址: https://finmind.github.io/
  - 未登入每小時限制 600 次請求
  - 登入後提升至每小時 1200 次

- `GEMINI_KEY`: Google Gemini API Key (用於 AI 文章生成)
  - 申請網址: https://makersuite.google.com/app/apikey

**範例 `.env` 檔案：**
```env
# 使用 TWSE API (無限制，推薦)
STOCK_DATA_PROVIDER=twse

# 或使用 FinMind (需 Token)
# STOCK_DATA_PROVIDER=finmind
# FINMIND_API_TOKEN=your_token_here

GEMINI_KEY=your_gemini_key_here
```

### 2. 安裝依賴
```bash
# 前端
cd frontend
npm install

# 後端 (Python API)
pip install flask flask-cors FinMind pandas numpy google-generativeai python-dotenv requests
```

### 2. 啟動開發環境
請開啟 **兩個** 終端機視窗分別執行：

**Terminal 1 (前端 React):**
```bash
cd frontend
npm run dev
```

**Terminal 2 (後端 Python server):**
```bash
# 在專案根目錄執行
python backend/server.py
```

前端會自動透過 Proxy 連線至後端，無需安裝 Vercel CLI。

瀏覽器開啟：**http://localhost:5173** (預設)

## 🤖 GitHub Actions 自動更新

專案包含每日自動更新腳本，會在台灣時間每天 17:00 (收盤後) 執行：

### 手動執行
```bash
python scripts/update_daily.py
```

### 自動排程
- 已設定 GitHub Actions workflow
- 每個交易日 (週一至週五) 自動執行
- 更新結果存放於 `frontend/public/data/daily_scan_results.json`

## 📖 使用方式

1. **查看動能股** - 首頁自動列出今日符合「突破關鍵點」的強勢股。
2. **篩選標的** - 使用頂部的「連續紅K」與「市值排行」篩選器，精確鎖定目標。
3. **管理庫存** - 點擊「匯入庫存」按鈕，使用截圖或手動輸入建立您的觀察清單。
4. **閱讀報告** - 每日更新 AI 生成的市場分析文章，掌握盤勢脈動。

## 🏗️ 技術架構

### 資料來源彈性架構 (Facade Pattern)

系統採用 **Facade Design Pattern** 來抽象化股價資料來源，提供以下優勢：

- **無 API 限制方案**: 預設使用 TWSE 官方 API，無需 Token 即可無限制存取
- **彈性切換**: 可透過環境變數輕鬆切換至 FinMind API (功能更豐富)
- **向後相容**: 既有程式碼無需修改，透過 Adapter 層無縫整合

```
Stock Data Facade
├── TWSEProvider (預設)
│   └── 台灣證券交易所官方 API
│       ✅ 無速率限制
│       ✅ 無需 Token
│       ⚠️ 功能較基本
│
└── FinMindProvider (選用)
    └── FinMind 第三方 API
        ✅ 功能豐富 (基本面、籌碼面)
        ⚠️ 免費版 600 req/hr
        ⚠️ 需申請 Token
```

**檔案結構：**
```
TrendGuard/
├── stock_data_facade.py       # Facade 主體 (Provider 模式)
├── stock_facade_adapter.py    # 向後相容 Adapter
├── tests/
│   └── test_stock_data_facade.py  # 完整測試套件
├── frontend/                 # React + Vite 前端
│   ├── src/
│   │   ├── pages/           # 頁面組件 (DailyReport, ArticleList)
│   │   ├── components/      # UI 組件 (StockCard, Charts)
│   │   └── firebase.js      # Firebase 配置
│   └── public/data/         # 靜態資料存儲
├── backend/                  # Python Flask API (即時行情)
├── scripts/                  # 自動化腳本
│   ├── update_daily.py      # 每日資料更新
│   ├── article_generator.py # AI 文章生成
│   └── humanizer-zh-tw/     # AI 文章優化規則庫
├── .github/workflows/        # CI/CD 設定
└── README.md
```

## ⚠️ 免責聲明

本系統僅提供數據運算與客觀條件篩選功能，不提供任何投資建議。使用者應自行判斷風險，過往數據不代表未來績效。

## 📄 License

MIT

