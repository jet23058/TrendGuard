# 趨勢守衛者 (TrendGuard)

🎯 基於 Jesse Livermore 交易哲學設計的台股觀察清單與分析工具。
結合現代化的網頁技術與 AI 智能分析，協助投資人理性判斷市場趨勢。

## ✨ 功能特色

- **動能掃描** - 自動篩選強勢股
  - 📊 **連續紅K篩選**：支援「至少 N 天」與「剛好 N 天」的精確篩選，快速鎖定動能股。
  - 🟢 **異動偵測**：自動比對每日清單，標示新進榜（NEW）與被剔除的股票。
  - 🏭 **產業熱點**：自動將股票依產業分類，一眼看穿主流族群。

- **AI 智能投顧** - 整合 Google Gemini 生成每日深度報告
  - 📝 **每日市場分析**：由 AI 模擬專業分析師口吻，撰寫每日盤勢摘要與個股點評。
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

## 🚀 快速開始

### 1. 安裝依賴
```bash
# 前端
cd frontend
npm install

# 後端 (Python API)
pip install flask flask-cors yfinance pandas numpy
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

瀏覽器開啟：**http://localhost:5174**

## 🤖 GitHub Actions 自動更新

專案包含每日自動更新腳本，會在台灣時間每天 18:00 (收盤後) 執行：

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
2. **篩選標的** - 使用頂部的「連續紅K」篩選器，切換「至少」或「剛好」模式尋找特定型態。
3. **管理庫存** - 點擊「匯入庫存」按鈕，使用截圖或手動輸入建立您的觀察清單。
4. **閱讀報告** - 每日更新 AI 生成的市場分析文章，掌握盤勢脈動。

## 🏗️ 技術架構

```
TrendGuard/
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
