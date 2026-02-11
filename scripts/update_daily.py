#!/usr/bin/env python3
"""
篩選條件：
1. 股價站上所有均線 (MA5, MA10, MA20, MA60)
2. 連續兩日紅 K (收盤 > 開盤)
3. 收盤價突破近 N 日新高
4. (修正) 警示/處置股也必須符合上述技術條件才能入選
"""
import json
import os
import sys
import concurrent.futures
import time
import threading
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

# Stock Data Provider (選擇使用 TWSE 或 FinMind)
USE_FACADE = os.environ.get('USE_STOCK_FACADE', 'true').lower() == 'true'

if USE_FACADE:
    # Use new Facade pattern for flexible data source
    from stock_facade_adapter import FacadeDataLoader as DataLoader, get_stock_facade
    _finmind_loader = None
    
    def get_finmind_loader():
        """Get or create Stock Data Facade singleton"""
        global _finmind_loader
        if _finmind_loader is None:
            _finmind_loader = DataLoader()
            token = os.environ.get("FINMIND_API_TOKEN")
            if token:
                _finmind_loader.login_by_token(api_token=token)
        return _finmind_loader
else:
    # Traditional FinMind API for Taiwan stock data
    from FinMind.data import DataLoader
    
    # Initialize FinMind DataLoader (singleton)
    _finmind_loader = None
    
    def get_finmind_loader():
        """Get or create FinMind DataLoader singleton"""
        global _finmind_loader
        if _finmind_loader is None:
            _finmind_loader = DataLoader()
            token = os.environ.get("FINMIND_API_TOKEN")
            if token:
                _finmind_loader.login_by_token(api_token=token)
                print("✅ FinMind logged in with token")
        return _finmind_loader

try:
    import twstock
    # 強制更新股票代碼表，確保擁有最新上市櫃清單
    # twstock.__update_codes() # 注意: 這可能需要下載，若 CI 環境受限可能失敗，視情況啟用
    HAS_TWSTOCK = True
except ImportError:
    HAS_TWSTOCK = False
    print("Warning: twstock not installed, using FinMind for stock names")

import re
import requests
from datetime import timedelta





def roc_to_date(roc_str):
    """Convert ROC date string (e.g., '114/01/05') to datetime object"""
    try:
        parts = roc_str.split('/')
        year = int(parts[0]) + 1911
        return datetime(year, int(parts[1]), int(parts[2]))
    except:
        return None

def fetch_market_alerts():
    """Fetch TWSE/TPEx Warning and Disposition data with Risk Analysis"""
    alerts = {}
    history_db = {} # {code: [dates]}
    
    today = datetime.now()
    today_str = today.strftime('%Y%m%d')
    # Look back 40 days to ensure we have enough trading days for the 30-day rule
    start_str = (today - timedelta(days=40)).strftime('%Y%m%d') 
    
    # 1. Fetch TWSE Warning History (Notice)
    try:
        url = "https://www.twse.com.tw/rwd/zh/announcement/notice"
        params = {'response': 'json', 'startDate': start_str, 'endDate': today_str}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        
        if 'data' in data:
            for item in data['data']:
                code = item[1]
                date_roc = item[5] # e.g. "114/01/30"
                reason = item[4]
                
                if code not in history_db:
                    history_db[code] = []
                history_db[code].append(date_roc)
                
                # If it's today's alert, initialize the alert object
                alert_dt = roc_to_date(date_roc)
                if alert_dt and (today - alert_dt).days <= 1:
                    alerts[code] = {
                        "type": "warning",
                        "badge": "警示",
                        "color": "yellow",
                        "info": "注意股",
                        "detail": reason,
                        "history": []
                    }
    except Exception as e:
        print(f"Error fetching TWSE notice: {e}")

    # 2. Fetch TWSE Disposition (Punish)
    try:
        url = "https://www.twse.com.tw/rwd/zh/announcement/punish"
        params = {'response': 'json', 'startDate': start_str, 'endDate': today_str}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        
        if 'data' in data:
            for item in data['data']:
                code = item[2]
                period_str = item[6] 
                content = item[8]
                
                if '～' in period_str:
                    start_roc, end_roc = period_str.split('～')
                    start_dt = roc_to_date(start_roc)
                    end_dt = roc_to_date(end_roc)
                    
                    if start_dt and end_dt and start_dt <= today + timedelta(days=1) and today <= end_dt + timedelta(days=1): 
                        freq = "處置"
                        match = re.search(r'每(\S+)分鐘', content)
                        if match:
                            freq = f"{match.group(1)}分盤"
                        elif "人工管制" in content:
                            freq = "人工管制"
                            
                        alerts[code] = {
                            "type": "disposition",
                            "badge": "處置",
                            "color": "red",
                            "info": f"{freq} (至 {end_roc})",
                            "detail": f"期間: {period_str}\n措施: {item[7]}",
                            "is_disposed": True
                        }
    except Exception as e:
        print(f"Error fetching TWSE punish: {e}")

    # 3. Fetch TPEX (OTC) Alerts
    try:
        base_url = "https://www.tpex.org.tw/openapi/v1"
        
        # 3.1 TPEX Warning History
        r = requests.get(f"{base_url}/tpex_trading_warning_information", timeout=10)
        if r.status_code == 200:
            for item in r.json():
                code = item.get('SecuritiesCompanyCode')
                date_roc = item.get('Date') # Compact "1140130"
                reason = item.get('TradingInformation', '')
                
                # Convert to slash format for consistency
                if len(date_roc) == 7:
                    fmt_date = f"{date_roc[:3]}/{date_roc[3:5]}/{date_roc[5:]}"
                else:
                    fmt_date = date_roc
                    
                if code not in history_db:
                    history_db[code] = []
                history_db[code].append(fmt_date)
                
                # Check if recent
                alert_dt = None
                if len(date_roc) == 7:
                    alert_dt = datetime(int(date_roc[:3]) + 1911, int(date_roc[3:5]), int(date_roc[5:]))
                
                if alert_dt and (today - alert_dt).days <= 1:
                    if code not in alerts:
                        alerts[code] = {
                            "type": "warning",
                            "badge": "警示",
                            "color": "yellow",
                            "info": "注意股",
                            "detail": reason,
                            "history": []
                        }

        # 3.2 TPEX Disposition
        r = requests.get(f"{base_url}/tpex_disposal_information", timeout=10)
        if r.status_code == 200:
            for item in r.json():
                code = item.get('SecuritiesCompanyCode')
                period_str = item.get('DispositionPeriod', '')
                content = item.get('DisposalCondition', '')
                
                if '~' in period_str:
                    try:
                        start_roc, end_roc = period_str.split('~')
                        def parse_roc_compact(d_str):
                            if len(d_str) == 7:
                                return datetime(int(d_str[:3]) + 1911, int(d_str[3:5]), int(d_str[5:]))
                            return roc_to_date(d_str)
                            
                        start_dt = parse_roc_compact(start_roc)
                        end_dt = parse_roc_compact(end_roc)
                        
                        if start_dt and end_dt and start_dt <= today + timedelta(days=1) and today <= end_dt + timedelta(days=1):
                            freq = "處置"
                            match = re.search(r'每(\S+)分鐘', content)
                            if match:
                                freq = f"{match.group(1)}分盤"
                            elif "人工管制" in content:
                                freq = "人工管制"
                                
                            alerts[code] = {
                                "type": "disposition",
                                "badge": "處置",
                                "color": "red",
                                "info": f"{freq} (至 {end_roc})",
                                "detail": f"期間: {period_str}\n措施: {content}",
                                "is_disposed": True
                            }
                    except: pass
    except Exception as e:
        print(f"Error fetching TPEX alerts: {e}")

    # 4. Risk Analysis (Calculating Disposition Proximity)
    for code, alert_obj in alerts.items():
        if alert_obj.get('type') == 'disposition':
            continue # Already disposed
            
        hist = sorted(list(set(history_db.get(code, []))), reverse=True)
        alert_obj['history'] = hist
        
        # Calculate Risk Metrics
        # Rule 1: 3 consecutive days
        consecutive = 0
        # This is tricky because we need trading days. 
        # For simplicity, we count consecutive entries in the sorted history.
        consecutive = 1
        # Check if previous days were also in history
        # (Need a calendar or just check if dates are close)
        # For now, let's just use the count in recent window.
        
        count_30 = len(hist)
        count_6 = 0
        # Approx count in last 6 trading days (approx 10 calendar days)
        cutoff_6 = today - timedelta(days=10)
        for d_str in hist:
            d_dt = roc_to_date(d_str)
            if d_dt and d_dt >= cutoff_6:
                count_6 += 1
        
        # Determine Risk Level
        risk_level = "low"
        risk_msg = ""
        
        if count_6 >= 3:
            risk_level = "high"
            risk_msg = f"觸發 4/6 處置風險 (目前 {count_6}/6)"
        elif count_6 >= 2:
            risk_level = "medium"
            risk_msg = f"近期注意次數增加 ({count_6}/6)"
            
        if count_30 >= 10:
            risk_level = "high"
            risk_msg = f"觸發 12/30 處置風險 (目前 {count_30}/30)"
            
        alert_obj['risk'] = {
            "level": risk_level,
            "message": risk_msg,
            "count_6": count_6,
            "count_30": count_30
        }

    return alerts

def fetch_allowed_day_trade_targets():
    """取得所有可現股當沖的股票代碼 (上市+上櫃)"""
    allowed = set()
    
    # 1. TWSE (上市)
    try:
        # TWTB4U: 當日沖銷交易標的及成交量值
        # 若不帶日期，預設回傳最近交易日
        url = "https://www.twse.com.tw/exchangeReport/TWTB4U?response=json"
        r = requests.get(url, timeout=10)
        data = r.json()
        if 'tables' in data:
            for t in data['tables']:
                # 尋找包含標的清單的表格 (通常是第二個，欄位含'證券代號')
                if 'fields' in t and '證券代號' in t['fields']:
                    if len(t.get('data', [])) > 100: # 簡單檢核資料量
                        for row in t['data']:
                            allowed.add(row[0]) # 代號
                        print(f"已取得上市當沖標的: {len(t['data'])} 檔")
    except Exception as e:
        print(f"Error fetching TWSE day trade list: {e}")

    # 2. TPEX (上櫃)
    try:
        # TPEX 需要指定日期，嘗試回推最近 5 天直到抓到資料
        found = False
        base_date = datetime.now()
        
        for i in range(5):
            d = base_date - timedelta(days=i)
            roc_year = d.year - 1911
            date_str = f"{roc_year}/{d.month:02d}/{d.day:02d}"
            
            url = f"https://www.tpex.org.tw/web/stock/trading/intraday_stat/intraday_trading_stat_result.php?l=zh-tw&o=json&d={date_str}"
            try:
                r = requests.get(url, timeout=5)
                data = r.json()
                if 'tables' in data:
                    for t in data['tables']:
                         if 'fields' in t and '證券代號' in t['fields']:
                            count = len(t.get('data', []))
                            if count > 50: # 簡單檢核
                                for row in t['data']:
                                    allowed.add(row[0])
                                print(f"已取得上櫃當沖標的 ({date_str}): {count} 檔")
                                found = True
                                break
                    if found: break
            except:
                continue
                
    except Exception as e:
        print(f"Error fetching TPEX day trade list: {e}")
        
    print(f"總計可當沖標的: {len(allowed)} 檔")
    return allowed

# --- 設定 ---
LOOKBACK_DAYS = 20  # 突破幾日新高
TEST_MODE = os.environ.get('TEST_MODE', 'true').lower() == 'true'  # GitHub Actions 設為 false
OUTPUT_DIR = Path("frontend/public/data")
MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 5)) # Parallel workers

# 測試用股票清單 (擴大範圍)
TEST_STOCKS = [
    # 權值股
    '2330', '2317', '2454', '2303', '2308', '2412', '2882', '2881', '2886', '2891',
    # 航運股
    '2603', '2609', '2615', '2618',
    # AI/半導體
    '3035', '6770', '6443', '3037', '3008', '3034', '2379', '3443', '6669',
    # 電子代工
    '3231', '2382', '2356', '4938', '2324', '2353',
    # 金融股
    '2884', '2885', '2887', '2880', '2883',
    # 其他熱門
    '2002', '1301', '1303', '2912', '9910', '2377', '3017', '2327', '6446', '3533',
    # 01/02 使用者提供清單 (用於確保連續性/剔除判定準確)
    '3455', '3516', '8064', '3481', '3289', '3402', '3580', '5452', '8431', '5351', 
    '2330', '2337', '2449', '2454', '3006', '3711', '4967', '6531', '8110', '5263', 
    '1460', '8423', '8438', '5704', '3163', '2025', '3360', '6265', '3624', '3689', 
    '2460', '2467', '3092', '3308', '4912', '5288', '5289', '2399',
    # 測試用: 南亞科 (若不在上述清單中)
    '2408'
]

from typing import Optional

def get_stock_name(code: str) -> tuple:
    """取得股票中文名稱、產業別與市場別"""
    market = "上市" # Default
    
    if HAS_TWSTOCK and code in twstock.codes:
        info = twstock.codes[code]
        market = info.market
        return info.name, info.group if hasattr(info, 'group') else "其他", market
    
    # Fallback: 使用 FinMind
    try:
        loader = get_finmind_loader()
        df = loader.TaiwanStockInfo()
        stock_info = df[df['stock_id'] == code]
        if not stock_info.empty:
            # FinMind doesn't explicitly separate Listed/OTC in simple info sometimes, 
            # but usually it's there. For now default to '上市' or guess.
            return stock_info.iloc[0]['stock_name'], stock_info.iloc[0]['industry_category'], market
    except Exception:
        pass
    return code, "其他", market


def get_all_tw_targets() -> list:
    """取得要掃描的股票清單"""
    if TEST_MODE:
        # 去除重複的股票代碼
        unique_stocks = sorted(list(set(TEST_STOCKS)))
        print(f"[測試模式] 僅掃描 {len(unique_stocks)} 檔測試股票...")
        return unique_stocks
    
    # 完整掃描模式
    if not HAS_TWSTOCK:
        print("twstock 未安裝，使用測試清單")
        return TEST_STOCKS
    
    targets = []
    print("正在整理台股清單 (含股票與商品型 ETF)...")
    for code, info in twstock.codes.items():
        if info.market in ["上市", "上櫃"]:
            if info.type == "股票" or info.type == "ETF":
                targets.append(code)
    
    print(f"共 {len(targets)} 檔標的待掃描")
    return targets


def check_livermore_criteria(code: str, market_alerts: Optional[dict] = None, allowed_day_trade_targets: Optional[set] = None) -> tuple[Optional[dict], Optional[float]]:
    """
    檢查是否符合利弗摩爾突破條件
    
    Returns:
        (full_data, change_pct)
        - full_data: 符合條件的完整資料，若不符合則為 None
        - change_pct: 該股票的漲跌幅 (float)，若無法取得資料則為 None
    """
    try:
        # Check alerts first
        alert_data = market_alerts.get(code) if market_alerts else None
        
        # 使用 FinMind API 取得股票資料
        loader = get_finmind_loader()
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 根據 Provider 動態調整歷史資料天數
        # TWSE Provider 需要逐月請求，所以縮短天數避免太多請求
        # FinMind Provider 一次請求即可，所以可以拿較多資料
        if USE_FACADE:
            # 使用 Facade 時，查詢 provider 類型
            facade = get_stock_facade()
            if facade.get_provider_name() == 'twse':
                # TWSE: 只抓 60 天（約 3 個月），減少 API 請求
                lookback_days = 60
            else:
                # FinMind: 抓 180 天（約 6 個月）
                lookback_days = 180
        else:
            # 傳統 FinMind: 抓 180 天
            lookback_days = 180
        
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        raw_df = loader.taiwan_stock_daily(
            stock_id=code,
            start_date=start_date,
            end_date=end_date
        )
        
        if raw_df is None or len(raw_df) < LOOKBACK_DAYS + 2:
            return None, None
        
        # FinMind 返回的欄位名稱與 yfinance 不同，需要轉換
        # FinMind: date, stock_id, Trading_Volume, Trading_money, open, max, min, close, spread, Trading_turnover
        df = raw_df.copy()
        df = df.rename(columns={
            'open': 'Open',
            'max': 'High',
            'min': 'Low',
            'close': 'Close',
            'Trading_Volume': 'Volume'
        })
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        
        # 計算均線
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        current_price = float(today['Close'])
        prev_close = float(yesterday['Close'])

        # [DEBUG] 新增：印出每檔股票的掃描狀態，便於除錯
        print(f"[DEBUG] {code} Date:{df.index[-1].strftime('%Y-%m-%d')} Close:{current_price} Open:{today['Open']} Vol:{today['Volume']}")
        
        # 漲跌幅 (即便不符合條件也要回傳，用於市場統計)
        change_pct = ((current_price - prev_close) / prev_close) * 100
        
        open_price = float(today['Open'])
        
        # 計算近 N 日最高價 (不含今日)
        past_data = df['High'].iloc[-(LOOKBACK_DAYS+1):-1]
        prev_high = float(past_data.max())
        
        # 計算連續紅 K 天數
        # 修正: 排除「無量一字線」 (Open==Close 且 成交量 < 100張)
        consecutive_red = 0
        for i in range(len(df)-1, -1, -1):
            c = float(df['Close'].iloc[i])
            o = float(df['Open'].iloc[i])
            v = int(df['Volume'].iloc[i])
            
            # 判斷是否為無量一字線 (量少於 100 張)
            # 注意: FinMind volume 單位為張
            is_flat_low_vol = (c == o) and (v < 100)
            
            if c >= o and not is_flat_low_vol:  # 收盤 >= 開盤，且非無量一字線
                consecutive_red += 1
            else:
                break
        
        # 條件檢查
        is_breakout = current_price > prev_high
        is_above_all_ma = (
            current_price > float(today['MA5']) and
            current_price > float(today['MA10']) and
            current_price > float(today['MA20']) and
            not pd.isna(today['MA60']) and current_price > float(today['MA60'])
        )
        is_two_red_k = consecutive_red >= 2
        
        has_alert = alert_data is not None
        
        # 修正: 必須符合突破、均線與紅K條件，否則直接剔除 (但回傳漲跌幅)
        if not (is_breakout and is_above_all_ma and is_two_red_k):
            return None, change_pct
        
        # 計算支撐點
        tech_stop = float(today['Low'])
        money_stop = current_price * 0.90
        stop_loss = max(tech_stop, money_stop)
        
        # 取得中文名稱、產業、市場
        name, sector, market = get_stock_name(code)
        
        # 計算 KD 指標 (9, 3, 3)
        k_period = 9
        d_period = 3
        
        # 計算 RSV 並平滑得到 K, D
        df['low_9'] = df['Low'].rolling(window=k_period).min()
        df['high_9'] = df['High'].rolling(window=k_period).max()
        df['RSV'] = ((df['Close'] - df['low_9']) / (df['high_9'] - df['low_9'])) * 100
        df['RSV'] = df['RSV'].fillna(50)
        
        # K = 2/3 * 前日K + 1/3 * RSV
        df['K'] = df['RSV'].ewm(span=3, adjust=False).mean()
        df['D'] = df['K'].ewm(span=d_period, adjust=False).mean()
        
        # 計算 5 日均量
        df['vol_ma5'] = df['Volume'].rolling(window=5).mean()
        
        # 取得 K 線數據 (最近 30 天)
        ohlc_data = []
        for idx, row in df.tail(30).iterrows():
            ohlc_data.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(float(row['Open']), 2),
                "high": round(float(row['High']), 2),
                "low": round(float(row['Low']), 2),
                "close": round(float(row['Close']), 2),
                "volume": int(row['Volume']),
                "volMa5": int(row['vol_ma5']) if not pd.isna(row['vol_ma5']) else int(row['Volume']),
                "k": round(float(row['K']), 1) if not pd.isna(row['K']) else 50,
                "d": round(float(row['D']), 1) if not pd.isna(row['D']) else 50,
                "ma5": round(float(row['MA5']), 2) if not pd.isna(row['MA5']) else None,
                "ma10": round(float(row['MA10']), 2) if not pd.isna(row['MA10']) else None,
                "ma20": round(float(row['MA20']), 2) if not pd.isna(row['MA20']) else None
            })
        
        # 取得最新 KD 值
        latest_k = round(float(df['K'].iloc[-1]), 1) if not pd.isna(df['K'].iloc[-1]) else 50
        latest_d = round(float(df['D'].iloc[-1]), 1) if not pd.isna(df['D'].iloc[-1]) else 50
        
        # [NEW] 計算波動率 (判斷箱型整理)
        # 取近 20 日收盤價計算變異係數 (CV = std / mean)
        last_20_closes = df['Close'].tail(20)
        volatility = last_20_closes.std() / last_20_closes.mean()
        is_box_breakout = volatility < 0.05  # 波動率小於 5% 視為盤整
        
        # 動態調整 Signal 文字
        signal_text = f"🔥 股價創 {LOOKBACK_DAYS} 日新高"
        priority_score = 90 + consecutive_red
        
        # Tags List for Frontend
        tags = []
        if is_box_breakout:
            tags.append("盤整突破")
            signal_text = f"🚀 突破箱型整理 (低波動) + 創高"
            priority_score += 5
            
        signal_text += f"，均線多頭"
        
        if has_alert:
             # 如果是警示股且符合技術條件，加註警語
             signal_text = f"⚠️ {alert_data.get('badge', '注意')}股 - {signal_text}"
             priority_score += 10 # 稍微提高權重
        
        # 計算是否可當沖
        cant_day_trade = False
        # 1. 不在當沖清單中 (僅在清單有抓到時才判斷)
        if allowed_day_trade_targets is not None and len(allowed_day_trade_targets) > 0:
             if code not in allowed_day_trade_targets:
                 cant_day_trade = True
        
        # 2. 處置股 (通常不可當沖)
        if alert_data and alert_data.get('type') == 'disposition':
             cant_day_trade = True

        full_data = {
            "ticker": code,
            "name": name,
            "sector": sector,
            "market": market, # 新增市場別
            "tags": tags,     # 新增標籤
            "currentPrice": round(current_price, 2),
            "changePct": round(change_pct, 2),
            "canDayTrade": not cant_day_trade,
            "prevHigh": round(prev_high, 2),
            "consecutiveRed": consecutive_red,
            "stopLoss": round(stop_loss, 2),
            "k": latest_k,
            "d": latest_d,
            "volume": int(today['Volume']),
            "signal": {
                "type": "breakout", # 統一為 breakout，因為現在都必須符合技術條件
                "text": f"{signal_text}。技術支撐位 {round(stop_loss, 1)}",
                "priority": priority_score
            },
            "ohlc": ohlc_data,
            "alert": alert_data  # Add Alert Info (None if normal)
        }
        
        return full_data, change_pct
        
    except Exception as e:
        # 靜默忽略錯誤
        return None, None


def calculate_changes(previous_data: Optional[dict], current_stocks: list) -> dict:
    """
    計算與前一日的差異 (新進、續漲、剔除)
    """
    if not previous_data or 'stocks' not in previous_data:
        return {
            "new": current_stocks,
            "continued": [],
            "removed": []
        }

    # Detect if we are updating on the same day
    prev_date = previous_data.get('date', '')
    is_same_day = prev_date == datetime.now().strftime("%Y-%m-%d")
    
    prev_map = {s['ticker']: s for s in previous_data['stocks']}
    
    # If same day, we need to reconstruct "Yesterday's State" to properly calculate Today's changes
    # Yesterday's Stocks = (Today's Stocks - Today's New) + Today's Removed
    if is_same_day and 'changes' in previous_data:
        print("ℹ️ 檢測到同日更新，正在重建昨日狀態以維持差異計算準確性...")
        current_existing_tickers = set(prev_map.keys())
        
        # 1. Provide tickers that were "New" today (so they weren't there yesterday)
        today_new_tickers = {s['ticker'] for s in previous_data['changes'].get('new', [])}
        
        # 2. Provide tickers that were "Removed" today (so they WERE there yesterday)
        today_removed_list = previous_data['changes'].get('removed', [])
        today_removed_map = {s['ticker']: s for s in today_removed_list}
        
        # Reconstruct Yesterday's set
        # Yesterday = (Current - New) U Removed
        reconstructed_prev_tickers = (current_existing_tickers - today_new_tickers) | set(today_removed_map.keys())
        
        # Rebuild prev_map for calculation
        # We need the stock objects. For 'removed', we have them. 
        # For 'continued' (Current - New), they are in prev_map.
        
        real_prev_map = {}
        for t in reconstructed_prev_tickers:
            if t in today_removed_map:
                real_prev_map[t] = today_removed_map[t]
            elif t in prev_map:
                real_prev_map[t] = prev_map[t]
                
        prev_map = real_prev_map
        print(f"   重建完成: 昨日共有 {len(prev_map)} 檔股票")

    curr_map = {s['ticker']: s for s in current_stocks}
    
    prev_tickers = set(prev_map.keys())
    curr_tickers = set(curr_map.keys())
    
    # 新進: 今有昨無
    new_tickers = curr_tickers - prev_tickers
    new_list = [curr_map[t] for t in new_tickers]
    
    # 續漲: 今有昨有
    continued_tickers = curr_tickers & prev_tickers
    continued_list = [curr_map[t] for t in continued_tickers]
    
    # 剔除: 今無昨有
    removed_tickers = prev_tickers - curr_tickers
    removed_list = [prev_map[t] for t in removed_tickers]
    
    return {
        "new": sorted(new_list, key=lambda x: x['ticker']),
        "continued": sorted(continued_list, key=lambda x: x['ticker']),
        "removed": sorted(removed_list, key=lambda x: x['ticker'])
    }


def update_existing_alerts():
    """僅更新現有檔案中的警示資訊"""
    print(f"\n=== 市場警示更新模式 ===")
    output_file = OUTPUT_DIR / "daily_scan_results.json"
    
    if not output_file.exists():
        print("錯誤：找不到掃描結果檔案，無法更新警示")
        sys.exit(1)
        
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        market_alerts = fetch_market_alerts()
        print(f"取得市場警示資料: {len(market_alerts)} 筆")
        
        updated_count = 0
        stocks = data.get('stocks', [])
        
        for stock in stocks:
            code = stock['ticker']
            alert_data = market_alerts.get(code)
            
            # Update alert field (even if None, to clear old alerts if they expired)
            if stock.get('alert') != alert_data:
                stock['alert'] = alert_data
                updated_count += 1
                if alert_data:
                    print(f"⚠️ {code} {stock['name']} 新增/更新警示: {alert_data['badge']}")
        
        # Update timestamps
        # If quoteTime doesn't exist (legacy), use old updatedAt as quoteTime
        if 'quoteTime' not in data:
            data['quoteTime'] = data.get('updatedAt')
            
        data['alertUpdateTime'] = datetime.now().isoformat()
        data['updatedAt'] = datetime.now().isoformat() # General update time
        
        # Save
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"✅ 已更新 {updated_count} 筆警示狀態")
        print(f"警示更新時間: {data['alertUpdateTime']}")
        
        return data
        
    except Exception as e:
        print(f"更新警示失敗: {e}")
        sys.exit(1)

# -----------------------------------------------
# Article Generation Integration
# -----------------------------------------------
try:
    from article_generator import generate_daily_article, save_to_json, generate_articles_index
except ModuleNotFoundError:
    from scripts.article_generator import generate_daily_article, save_to_json, generate_articles_index

def process_single_stock(code, market_alerts, allowed_day_trade_targets):
    """Worker function for parallel processing"""
    try:
        # Small delay to prevent burst rate limit
        time.sleep(0.1) 
        data, change_pct = check_livermore_criteria(code, market_alerts, allowed_day_trade_targets)
        return code, data, change_pct
    except Exception as e:
        print(f"Error processing {code}: {e}")
        return code, None, None

def main():
    """主程式"""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--update-alerts', action='store_true', help='Update existing alerts only')
    parser.add_argument('--generate-article-only', action='store_true', help='Generate article from existing data only')
    args = parser.parse_args()

    # Check arguments
    if args.update_alerts:
        data = update_existing_alerts()
        
        # Merge article generation for alert updates
        try:
            print("正在更新盤勢分析文章 (含警示資訊)...")
            article = generate_daily_article(data)
            save_to_json(article)
            print("✅ 已更新每日分析文章並儲存")
        except Exception as e:
            print(f"⚠️ 文章更新失敗: {e}")
            
        return

    # Check Manual Article Trigger
    if args.generate_article_only:
        print("🚀 Manual Trigger: Generating Article Only")
        output_file = OUTPUT_DIR / "daily_scan_results.json"
        
        if not output_file.exists():
            print(f"❌ Error: {output_file} not found. Cannot generate article.")
            sys.exit(1)
            
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            article = generate_daily_article(data)
            if save_to_json(article):
                print("✅ Manual article generation and save completed successfully.")
            else:
                print("⚠️ Article generated but NOT saved (check errors above).")
                sys.exit(1)
            return
        except Exception as e:
            print(f"❌ Failed to generate article: {e}")
            sys.exit(1)

    print(f"\n=== 利弗摩爾強勢突破掃描 ===")
    print(f"掃描時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"突破天數: {LOOKBACK_DAYS} 日\n")
    
    # 確保目錄存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "daily_scan_results.json"
    
    # 讀取舊資料 (用於計算差異)
    previous_data = None
    if output_file.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                previous_data = json.load(f)
        except Exception as e:
            print(f"無法讀取舊資料: {e}")

    # 取得股票清單
    target_list = get_all_tw_targets()
    total = len(target_list)
    
    # 警告：無 Token 時掃描大量股票風險
    token = os.environ.get("FINMIND_API_TOKEN")
    
    # [NEW] Anonymous Optimization: Prioritize and Limit
    if not token and total > 600:
        print(f"⚠️ 未設定 Token，啟用「匿名安全模式」")
        print(f"   將限制掃描前 550 檔熱門股票，以避免觸發 API 限制 (600次/hr)。")
        
        # Load ranks to prioritize
        rank_file = OUTPUT_DIR / "market_cap_rank.json"
        ranks = {}
        if rank_file.exists():
            try:
                with open(rank_file, 'r', encoding='utf-8') as f:
                    ranks = json.load(f).get("ranks", {})
            except: pass
            
        # Sort: Ranked stocks first (low rank number), then others
        target_list.sort(key=lambda x: ranks.get(x, 99999))
        
        # Slice
        target_list = target_list[:550]
        total = len(target_list)
        print(f"   ✅ 已篩選前 {total} 檔高市值股票進行掃描。")
    elif not token:
        print(f"⚠️ 警告: 未設定 Token，但股票數量 {total} 在限制範圍內，繼續執行。")
    
    # 取得市場警示 (處置/注意)
    market_alerts = fetch_market_alerts()
    print(f"取得市場警示資料: {len(market_alerts)} 筆")
    

    
    # 取得可當沖標的清單
    allowed_day_trade_targets = fetch_allowed_day_trade_targets()
    
    results = []
    
    # 市場寬度統計 (Market Breadth)
    market_stats = {
        "up": 0,
        "down": 0,
        "flat": 0,
        "total_scanned": 0
    }
    
    print(f"🚀 開始平行掃描 (Workers: {MAX_WORKERS})...")
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit tasks
        futures = {executor.submit(process_single_stock, code, market_alerts, allowed_day_trade_targets): code for code in target_list}
        
        completed_count = 0
        for future in concurrent.futures.as_completed(futures):
            code = futures[future]
            try:
                _, data, change_pct = future.result()
                
                completed_count += 1
                if completed_count % 10 == 0:
                    print(f"\r進度: {completed_count}/{total} ({(completed_count/total)*100:.1f}%)", end="", flush=True)
                
                # 統計市場漲跌
                if change_pct is not None:
                    market_stats["total_scanned"] += 1
                    if change_pct > 0:
                        market_stats["up"] += 1
                    elif change_pct < 0:
                        market_stats["down"] += 1
                    else:
                        market_stats["flat"] += 1
                        
                if data:
                    results.append(data)
                    
            except Exception as exc:
                print(f"\nError processing {code}: {exc}")

    elapsed = time.time() - start_time
    print(f"\n\n掃描完成！耗時: {elapsed:.2f} 秒")
    print(f"市場統計: 上漲 {market_stats['up']} / 下跌 {market_stats['down']} / 平盤 {market_stats['flat']}")
    print(f"符合條件: {len(results)} 檔\n")
    

    
    # Restore sort by priority (Signal Strength)
    results.sort(key=lambda x: x['signal']['priority'], reverse=True)
    
    # 計算差異
    changes = calculate_changes(previous_data, results)

    # 輸出結果
    if results:
        print("=" * 60)
        print(f"{'代號':<8} {'名稱':<10} {'現價':>8} {'連紅':>4} {'狀態':<6}")
        print("=" * 60)
        
        # 建立快速查找 map
        new_tickers = {s['ticker'] for s in changes['new']}
        
        for r in results:
            status = "✨新進" if r['ticker'] in new_tickers else "⟳續漲"
            print(f"{r['ticker']:<8} {r['name']:<10} {r['currentPrice']:>8.2f} {r['consecutiveRed']:>4} {status:<6}")

    current_iso = datetime.now().isoformat()
    
    # 準備 JSON 輸出
    output = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "updatedAt": current_iso,
        "quoteTime": current_iso, 
        "alertUpdateTime": current_iso,
        "scanType": "livermore_breakout",
        "criteria": {
            "lookbackDays": LOOKBACK_DAYS,
            "description": f"突破 {LOOKBACK_DAYS} 日新高 + 站上所有均線 + 連續2日紅K"
        },
        "stocks": results,
        "marketStats": market_stats, # 新增市場統計欄位
        "summary": {
            "total": len(results),
            "buySignals": len(results),
            "counts": {
                "new": len(changes['new']),
                "continued": len(changes['continued']),
                "removed": len(changes['removed'])
            }
        },
        "changes": changes
    }
    
    # 寫入 JSON
    output_file = OUTPUT_DIR / "daily_scan_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # [NEW] Save History JSON for Article Page
    history_dir = OUTPUT_DIR / "history"
    history_dir.mkdir(exist_ok=True)
    history_file = history_dir / f"{output['date']}.json"
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"✅ History saved to {history_file}")
    
    print(f"\n✅ 已輸出至 {output_file}")

    # -----------------------------------------------
    # Auto Generate Article
    # -----------------------------------------------
    try:
        print("正在產生盤勢分析文章...")
        article = generate_daily_article(output)
        save_to_json(article)
        print("✅ 已產生每日分析文章並儲存")
    except Exception as e:
        print(f"⚠️ 文章產生失敗 (不影響主流程): {e}")
    
    return output



if __name__ == "__main__":
    main()
    # Always regenerate index after main process
    try:
        generate_articles_index()
    except Exception as e:
        print(f"Index generation failed: {e}")
