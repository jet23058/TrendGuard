#!/usr/bin/env python3
"""
利弗摩爾強勢突破掃描器
每日 14:30 執行，篩選符合條件的強勢股

篩選條件：
1. 股價站上所有均線 (MA5, MA10, MA20, MA60)
2. 連續兩日紅 K (收盤 > 開盤)
3. 收盤價突破近 N 日新高
"""
import json
import os
from datetime import datetime
from pathlib import Path

import yfinance as yf
import pandas as pd

# 嘗試導入 twstock 取得中文名稱
try:
    import twstock
    HAS_TWSTOCK = True
except ImportError:
    HAS_TWSTOCK = False
    print("Warning: twstock not installed, using yfinance for stock names")

# --- 設定 ---
LOOKBACK_DAYS = 20  # 突破幾日新高
TEST_MODE = os.environ.get('TEST_MODE', 'true').lower() == 'true'  # GitHub Actions 設為 false
OUTPUT_DIR = Path("frontend/public/data")

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
    '2460', '2467', '3092', '3308', '4912', '5288', '5289', '2399'
]


from typing import Optional

def get_stock_name(code: str) -> tuple:
    """取得股票中文名稱與產業別"""
    if HAS_TWSTOCK and code in twstock.codes:
        info = twstock.codes[code]
        return info.name, info.group if hasattr(info, 'group') else "其他"
    
    # Fallback: 使用 yfinance
    try:
        ticker = f"{code}.TW"
        yf_info = yf.Ticker(ticker).info
        name = yf_info.get('longName', yf_info.get('shortName', code))
        # 處理英文名稱過長
        if len(name) > 15:
            name = name[:12] + "..."
        return name, "其他"
    except Exception:
        return code, "其他"


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
    print("正在整理台股清單...")
    for code, info in twstock.codes.items():
        if info.type == "股票" and info.market in ["上市", "上櫃"]:
            targets.append(code)
    
    print(f"共 {len(targets)} 檔股票待掃描")
    return targets


def check_livermore_criteria(code: str) -> Optional[dict]:
    """
    檢查是否符合利弗摩爾突破條件
    
    條件：
    1. 股價 > MA5/MA10/MA20/MA60 (多頭排列)
    2. 連續 2 日以上紅 K
    3. 收盤價突破近 N 日新高
    """
    try:
        # 決定後綴
        suffix = ".TW"
        if HAS_TWSTOCK and code in twstock.codes:
            if twstock.codes[code].market == "上櫃":
                suffix = ".TWO"
        
        ticker = f"{code}{suffix}"
        df = yf.download(ticker, period="6mo", progress=False)
        
        if len(df) < LOOKBACK_DAYS + 2:
            return None
        
        # 處理 MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        
        # 計算均線
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        
        today = df.iloc[-1]
        yesterday = df.iloc[-2]
        
        current_price = float(today['Close'])
        open_price = float(today['Open'])
        
        # 計算近 N 日最高價 (不含今日)
        past_data = df['High'].iloc[-(LOOKBACK_DAYS+1):-1]
        prev_high = float(past_data.max())
        
        # 計算連續紅 K 天數
        consecutive_red = 0
        for i in range(len(df)-1, -1, -1):
            c = float(df['Close'].iloc[i])
            o = float(df['Open'].iloc[i])
            if c > o:
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
        
        # 必須同時符合三個條件
        if not (is_breakout and is_above_all_ma and is_two_red_k):
            return None
        
        # 計算停損點
        tech_stop = float(today['Low'])
        money_stop = current_price * 0.90
        stop_loss = max(tech_stop, money_stop)
        
        # 取得中文名稱
        name, sector = get_stock_name(code)
        
        # 漲跌幅
        change_pct = ((current_price - float(yesterday['Close'])) / float(yesterday['Close'])) * 100
        
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
        
        return {
            "ticker": code,
            "name": name,
            "sector": sector,
            "currentPrice": round(current_price, 2),
            "changePct": round(change_pct, 2),
            "prevHigh": round(prev_high, 2),
            "consecutiveRed": consecutive_red,
            "stopLoss": round(stop_loss, 2),
            "k": latest_k,
            "d": latest_d,
            "volume": int(today['Volume']),
            "recommendation": {
                "type": "buy",
                "text": f"🔥 突破 {LOOKBACK_DAYS} 日新高！連續 {consecutive_red} 根紅 K，站上所有均線，符合利弗摩爾關鍵點買進條件。停損設 {round(stop_loss, 1)}",
                "priority": 90 + consecutive_red  # 連紅越多優先級越高
            },
            "ohlc": ohlc_data
        }
        
    except Exception as e:
        # 靜默忽略錯誤
        return None


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

    prev_map = {s['ticker']: s for s in previous_data['stocks']}
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



def main():
    """主程式"""
    print(f"\n=== 利弗摩爾強勢突破掃描 ===")
    print(f"掃描時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"突破天數: {LOOKBACK_DAYS} 日\n")
    
    # 確保目錄存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "daily_recommendations.json"
    
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
    
    results = []
    total = len(target_list)
    
    for i, code in enumerate(target_list):
        if i % 10 == 0:
            print(f"\r進度: {i}/{total}...", end="", flush=True)
        
        data = check_livermore_criteria(code)
        if data:
            results.append(data)
    
    print(f"\n\n掃描完成！")
    print(f"符合條件: {len(results)} 檔\n")
    
    # 按連紅天數排序 (越多越強)
    results.sort(key=lambda x: x['recommendation']['priority'], reverse=True)
    
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

    # 準備 JSON 輸出
    output = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "updatedAt": datetime.now().isoformat(),
        "scanType": "livermore_breakout",
        "criteria": {
            "lookbackDays": LOOKBACK_DAYS,
            "description": f"突破 {LOOKBACK_DAYS} 日新高 + 站上所有均線 + 連續2日紅K"
        },
        "stocks": results,
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
    output_file = OUTPUT_DIR / "daily_recommendations.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已輸出至 {output_file}")
    
    return output


if __name__ == "__main__":
    main()
