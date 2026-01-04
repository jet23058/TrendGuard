# 利弗摩爾台股戰情室 (Livermore Trader Dashboard)

🎯 基於 Jesse Livermore 交易哲學設計的台股觀察清單與分析工具

![UI Preview](/Users/lin/.gemini/antigravity/brain/7a0baf77-a5d6-478e-ad38-5057c52b7f16/uploaded_image_1767511840110.png)

## ✨ 功能特色

- **異動偵測** - 自動比對今日 vs 昨日持股
  - 🟢 新加入的股票（綠色標籤 + NEW）
  - 🔘 被去除的股票（灰色刪除線）
- **K線圖表** - 每檔股票提供：
  - 近 1 個月 K 線圖（紅漲綠跌）
  - KD 指標疊加 (9,3,3 參數)
  - 超買/超賣參考線
- **交易建議** - 基於利弗摩爾規則：
  - 10% 硬性停損警告
  - 20% 獲利加碼建議
  - KD 金叉買點偵測
  - 量縮盤整換股建議

## 🚀 快速開始

### 安裝依賴
```bash
cd frontend
npm install
```

### 啟動應用
```bash
npm run dev
```

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
- 更新結果存放於 `frontend/public/data/daily_recommendations.json`

## 📖 使用方式

1. **匯入庫存** - 點擊右上角「匯入庫存」按鈕
2. **搜尋股票** - 輸入代碼或名稱（如 2330 或 台積電）
3. **設定成本** - 輸入您的平均成本與股數
4. **確認匯入** - 系統自動分析並顯示K線與建議

## 🏗️ 技術架構

```
TrendGuard/
├── frontend/                 # React 前端
│   ├── src/
│   │   ├── App.jsx          # 主應用元件
│   │   └── index.css        # TailwindCSS
│   └── public/data/         # 每日更新資料
├── scripts/
│   └── update_daily.py      # 每日更新腳本
├── .github/workflows/
│   └── daily-update.yml     # GitHub Actions
└── README.md
```

## ⚠️ 免責聲明

本系統使用模擬數據，僅供參考，不構成投資建議。投資有風險，請謹慎評估。

## 📄 License

MIT
