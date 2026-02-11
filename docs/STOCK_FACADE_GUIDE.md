# Stock Data Facade 使用指南

## 概述

Stock Data Facade 是一個設計模式實作，允許系統靈活地在不同股價資料來源之間切換，而不需要修改業務邏輯程式碼。

## 為什麼需要 Facade？

### 問題
- **FinMind API 限制**: 免費版每小時 600 次請求，Token 版 1200 次
- **單一資料源風險**: 若 API 失效，整個系統停擺
- **擴展性差**: 新增資料源需要大幅修改程式碼

### 解決方案
使用 Facade Pattern 抽象化資料來源：
- ✅ 無縫切換 TWSE / FinMind
- ✅ TWSE 無 API 限制
- ✅ 向後相容既有程式碼
- ✅ 易於擴展新資料源

## 快速開始

### 1. 基本使用

```python
from stock_data_facade import StockDataFacade

# 建立 Facade (預設使用 TWSE)
facade = StockDataFacade()

# 取得股價資料
data = facade.get_stock_price('2330', '2024-01-01', '2024-01-31')
print(f"取得 {len(data)} 筆資料")
print(f"最新收盤價: {data[-1]['close']}")

# 取得股票資訊
info = facade.get_stock_info('2330')
print(f"股票名稱: {info['stock_name']}")
```

### 2. 切換資料源

#### 方法一: 透過環境變數 (推薦)

在 `.env` 檔案中設定：
```env
STOCK_DATA_PROVIDER=twse  # 或 finmind
```

```python
from stock_data_facade import StockDataFacade

# 會自動讀取環境變數
facade = StockDataFacade()
print(f"當前使用: {facade.get_provider_name()}")
```

#### 方法二: 程式碼指定

```python
from stock_data_facade import StockDataFacade

# 明確指定使用 TWSE
facade = StockDataFacade(provider='twse')

# 動態切換到 FinMind
facade.set_provider('finmind')
```

### 3. 整合到既有程式碼

使用 Adapter 層維持向後相容：

```python
# 舊程式碼 (使用 FinMind DataLoader)
from FinMind.data import DataLoader

loader = DataLoader()
df = loader.taiwan_stock_daily(stock_id='2330', 
                                 start_date='2024-01-01', 
                                 end_date='2024-01-31')

# 新程式碼 (使用 Facade，介面完全相同)
from stock_facade_adapter import FacadeDataLoader

loader = FacadeDataLoader()  # 自動使用 TWSE 或環境變數設定
df = loader.taiwan_stock_daily(stock_id='2330', 
                                 start_date='2024-01-01', 
                                 end_date='2024-01-31')
```

## 資料格式

### 統一輸出格式

兩種 Provider 都返回相同格式，確保程式碼無需修改：

```python
[
  {
    "date": "2024-01-02",
    "open": 580.0,
    "high": 585.0,
    "low": 578.0,
    "close": 582.0,
    "volume": 25000  # 單位: 張 (lots)
  },
  ...
]
```

### 股票資訊格式

```python
{
  "stock_id": "2330",
  "stock_name": "台積電"
}
```

## Provider 比較

| 特性 | TWSE Provider | FinMind Provider |
|------|---------------|------------------|
| API 限制 | ❌ 無限制 | ⚠️ 600/hr (免費) |
| Token 需求 | ❌ 不需要 | ⚠️ 提升限制需 Token |
| 資料完整性 | ✅ 官方資料 | ✅ 完整 |
| 功能豐富度 | ⚠️ 基本價量 | ✅ 含基本面/籌碼面 |
| 穩定性 | ✅ 官方 API | ✅ 第三方服務 |
| 推薦場景 | 生產環境 | 開發/分析 |

## 配置說明

### 環境變數

```env
# 資料源選擇 (預設: twse)
STOCK_DATA_PROVIDER=twse

# FinMind Token (選用，僅使用 finmind 時需要)
FINMIND_API_TOKEN=your_token_here
```

### 何時使用 TWSE？
- ✅ 生產環境
- ✅ 高頻率請求
- ✅ 不需要基本面資料
- ✅ 無 FinMind Token

### 何時使用 FinMind？
- ✅ 開發環境
- ✅ 需要基本面/籌碼面資料
- ✅ 有 FinMind Token
- ✅ 請求頻率低於限制

## 測試

執行完整測試套件：

```bash
# 執行 Facade 測試
python -m pytest tests/test_stock_data_facade.py -v

# 查看測試覆蓋率
python -m pytest tests/test_stock_data_facade.py --cov=stock_data_facade
```

## 常見問題

### Q: 如何確認當前使用哪個 Provider？

```python
from stock_data_facade import StockDataFacade

facade = StockDataFacade()
print(f"當前使用: {facade.get_provider_name()}")
```

### Q: TWSE 和 FinMind 的 volume 單位不同嗎？

是的，TWSE API 返回的成交量已轉換為「張」(lots)，而 FinMind 原始資料為「股」(shares)，但 Facade 已自動統一為「張」。

### Q: 可以新增其他資料源嗎？

可以！只需實作 `StockDataProvider` 抽象類別：

```python
from stock_data_facade import StockDataProvider

class YourCustomProvider(StockDataProvider):
    def fetch_stock_price(self, stock_id, start_date, end_date):
        # 實作你的資料源邏輯
        pass
    
    def fetch_stock_info(self, stock_id):
        # 實作你的資料源邏輯
        pass
```

然後在 `StockDataFacade._create_provider()` 中註冊。

### Q: 為什麼 TWSE 取得股票名稱會返回股票代碼？

TWSE API 沒有簡單的股票資訊查詢端點，目前 fallback 為返回股票代碼。建議：
- 使用 `twstock` 套件補充
- 或切換至 FinMind provider 取得完整資訊

## 架構圖

```
┌─────────────────────────────────────┐
│   Application Code (既有程式碼)      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  FacadeDataLoader (Adapter Layer)   │
│  - 向後相容 FinMind DataLoader       │
│  - 自動轉換 DataFrame 格式           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│     StockDataFacade (主要介面)       │
│  - 統一的資料存取介面                 │
│  - Provider 切換邏輯                 │
└──────────────┬──────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌─────────────┐  ┌─────────────┐
│ TWSE        │  │ FinMind     │
│ Provider    │  │ Provider    │
│             │  │             │
│ - 無限制     │  │ - 功能豐富   │
│ - 官方 API   │  │ - 有限制     │
└─────────────┘  └─────────────┘
```

## 最佳實踐

1. **環境變數管理**: 使用 `.env` 檔案，不要在程式碼中硬編碼
2. **錯誤處理**: 兩種 Provider 都會在錯誤時返回空陣列，確保程式不會崩潰
3. **Token 保護**: `.env` 已在 `.gitignore` 中，切勿提交到版本控制
4. **生產環境**: 建議使用 TWSE Provider 避免 API 限制
5. **開發環境**: 可使用 FinMind Provider 測試完整功能

## 授權

MIT License
