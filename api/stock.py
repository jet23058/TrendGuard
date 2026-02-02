from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os
from datetime import datetime, timedelta
import requests

# Helper to fetch data from FinMind using Requests (No Pandas/FinMind SDK)
def fetch_finmind_data(dataset, data_id, start_date):
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": dataset,
        "data_id": data_id,
        "start_date": start_date
    }
    token = os.environ.get("FINMIND_API_TOKEN")
    if token:
        params["token"] = token
        
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            res = r.json()
            if res.get("msg") == "success":
                return res.get("data", [])
        return []
    except Exception as e:
        print(f"FinMind API Error: {e}")
        return []

def get_stock_name(ticker_code):
    """Get Chinese name using FinMind (Pure Requests)"""
    try:
        data = fetch_finmind_data("TaiwanStockInfo", ticker_code, "")
        if data:
            return data[0].get("stock_name", ticker_code)
        return ticker_code
    except:
        return ticker_code

# Pure Python Indicators
def calculate_ma(prices, window):
    """Calculate Simple Moving Average"""
    if len(prices) < window:
        return [None] * len(prices)
    
    mas = [None] * (window - 1)
    for i in range(window - 1, len(prices)):
        window_slice = prices[i - window + 1 : i + 1]
        mas.append(sum(window_slice) / window)
    return mas

def calculate_kd(highs, lows, closes):
    """Calculate K, D (9, 3, 3)"""
    length = len(closes)
    k_vals = [50.0] * length # Default 50
    d_vals = [50.0] * length
    
    # Needs at least 9 days
    if length < 9:
        return k_vals, d_vals

    # Initial previous K/D
    prev_k = 50.0
    prev_d = 50.0

    for i in range(length):
        if i < 8:
            k_vals[i] = prev_k
            d_vals[i] = prev_d
            continue
            
        # RSV Window: i-8 to i (inclusive 9 days)
        window_highs = highs[i-8 : i+1]
        window_lows = lows[i-8 : i+1]
        
        max_h = max(window_highs)
        min_l = min(window_lows)
        
        if max_h == min_l:
            rsv = 50.0
        else:
            rsv = ((closes[i] - min_l) / (max_h - min_l)) * 100
            
        # K = 2/3 * PrevK + 1/3 * RSV
        curr_k = (2/3) * prev_k + (1/3) * rsv
        # D = 2/3 * PrevD + 1/3 * K
        curr_d = (2/3) * prev_d + (1/3) * curr_k
        
        k_vals[i] = curr_k
        d_vals[i] = curr_d
        
        prev_k = curr_k
        prev_d = curr_d
        
    return k_vals, d_vals

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        ticker = query.get('ticker', [None])[0]

        if not ticker:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing ticker"}).encode())
            return

        try:
            # 1. Clean ticker
            ticker_code = ticker.replace('.TW', '').replace('.TWO', '')
            
            # 2. Fetch Data
            start_date = (datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d')
            raw_data = fetch_finmind_data("TaiwanStockPrice", ticker_code, start_date)
            
            if not raw_data:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Stock not found"}).encode())
                return

            # Parse Data
            dates = []
            opens = []
            highs = []
            lows = []
            closes = []
            volumes = []
            
            for item in raw_data:
                dates.append(item["date"])
                opens.append(float(item["open"]))
                highs.append(float(item["max"]))
                lows.append(float(item["min"]))
                closes.append(float(item["close"]))
                volumes.append(int(item["Trading_Volume"])) 
            
            # 3. Calculate Indicators
            ma5 = calculate_ma(closes, 5)
            ma10 = calculate_ma(closes, 10)
            ma20 = calculate_ma(closes, 20)
            ma60 = calculate_ma(closes, 60)
            
            k_vals, d_vals = calculate_kd(highs, lows, closes)
            
            # 4. Livermore Logic
            latest_idx = -1
            current_price = closes[latest_idx]
            latest_k = k_vals[latest_idx]
            latest_d = d_vals[latest_idx]
            
            # Consecutive Red (Backwards)
            consecutive_red = 0
            for i in range(len(closes)-1, -1, -1):
                c = closes[i]
                o = opens[i]
                v = volumes[i]
                
                # Check flat low vol (Shares < 1000)
                is_flat_low_vol = (c == o) and (v < 1000) 
                
                if c >= o and not is_flat_low_vol:
                    consecutive_red += 1
                else:
                    break
            
            # Stop Loss
            tech_stop = lows[latest_idx]
            money_stop = current_price * 0.90
            stop_loss = max(tech_stop, money_stop)
            
            # 5. Prepare OHLC (Last 60)
            ohlc_data = []
            lookback = 60
            start_idx = max(0, len(dates) - lookback)
            
            for i in range(start_idx, len(dates)):
                ohlc_data.append({
                    "date": dates[i],
                    "open": opens[i],
                    "high": highs[i],
                    "low": lows[i],
                    "close": closes[i],
                    "volume": volumes[i],
                    "k": round(k_vals[i], 1),
                    "d": round(d_vals[i], 1),
                    "ma5": round(ma5[i], 2) if ma5[i] else None,
                    "ma10": round(ma10[i], 2) if ma10[i] else None,
                    "ma20": round(ma20[i], 2) if ma20[i] else None,
                    "ma60": round(ma60[i], 2) if ma60[i] else None
                })
            
            # Latest Changes
            if len(closes) >= 2:
                prev_close = closes[-2]
                change_pct = ((current_price - prev_close) / prev_close) * 100
            else:
                change_pct = 0.0
                
            name = get_stock_name(ticker_code)
            
            data = {
                "ticker": ticker_code,
                "name": name,
                "currentPrice": round(current_price, 2),
                "changePct": round(change_pct, 2),
                "k": round(latest_k, 1),
                "d": round(latest_d, 1),
                "ohlc": ohlc_data,
                "ma5": round(ma5[latest_idx], 2) if ma5[latest_idx] else None,
                "ma10": round(ma10[latest_idx], 2) if ma10[latest_idx] else None,
                "ma20": round(ma20[latest_idx], 2) if ma20[latest_idx] else None,
                "ma60": round(ma60[latest_idx], 2) if ma60[latest_idx] else None,
                "volume": int(volumes[latest_idx]),
                "consecutiveRed": consecutive_red,
                "stopLoss": round(stop_loss, 2)
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        except Exception as e:
            print(f"Error: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
