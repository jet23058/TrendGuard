from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# FinMind migration
try:
    from FinMind.data import DataLoader
    HAS_FINMIND = True
except ImportError:
    HAS_FINMIND = False

# Try to import twstock for Chinese names
try:
    import twstock
    HAS_TWSTOCK = True
except ImportError:
    HAS_TWSTOCK = False

# Initialize FinMind DataLoader
_finmind_loader = None

def get_finmind_loader():
    global _finmind_loader
    if not HAS_FINMIND:
        raise ImportError("FinMind module is not available in Vercel environment.")
        
    if _finmind_loader is None:
        _finmind_loader = DataLoader()
        token = os.environ.get("FINMIND_API_TOKEN")
        if token:
            _finmind_loader.login_by_token(api_token=token)
    return _finmind_loader

def get_stock_name(ticker_code):
    """Get Chinese name using twstock if available"""
    if HAS_TWSTOCK and ticker_code in twstock.codes:
        return twstock.codes[ticker_code].name
    
    # Fallback to FinMind
    try:
        loader = get_finmind_loader()
        info_df = loader.taiwan_stock_info()
        if info_df is not None and not info_df.empty:
            row = info_df[info_df['stock_id'] == ticker_code]
            if not row.empty:
                return row.iloc[0].get('stock_name', ticker_code)
        return ticker_code
    except:
        return ticker_code

def get_stock_history(ticker_code):
    """Helper to fetch stock history using FinMind"""
    try:
        loader = get_finmind_loader()
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d')
        
        # Clean ticker
        code = ticker_code.replace('.TW', '').replace('.TWO', '')
        
        df = loader.taiwan_stock_daily(
            stock_id=code,
            start_date=start_date,
            end_date=end_date
        )
        
        if df is None or df.empty:
            return None, pd.DataFrame()
            
        # Standardize columns to match logic
        df = df.rename(columns={
            'date': 'Date',
            'open': 'Open',
            'max': 'High',
            'min': 'Low',
            'close': 'Close',
            'Trading_Volume': 'Volume'
        })
        
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date').sort_index()
        
        # Convert types
        cols = ['Open', 'High', 'Low', 'Close']
        df[cols] = df[cols].astype(float)
        df['Volume'] = df['Volume'].astype(int)
        
        return None, df
    except Exception as e:
        print(f"FinMind error: {e}")
        return None, pd.DataFrame()

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
            
            # Fetch using FinMind
            _, df = get_stock_history(ticker_code)
            
            if df.empty:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Stock not found"}).encode())
                return

            # 2. Calculate Indicators
            # MA
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA10'] = df['Close'].rolling(window=10).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA60'] = df['Close'].rolling(window=60).mean()

            # KD (9, 3, 3)
            k_period = 9
            df['low_9'] = df['Low'].rolling(window=k_period).min()
            df['high_9'] = df['High'].rolling(window=k_period).max()
            df['RSV'] = ((df['Close'] - df['low_9']) / (df['high_9'] - df['low_9'])) * 100
            df['RSV'] = df['RSV'].fillna(50)
            df['K'] = df['RSV'].ewm(span=3, adjust=False).mean()
            df['D'] = df['K'].ewm(span=3, adjust=False).mean()

            # 3. Calculate Livermore Specifics (Stop Loss, Consecutive Red)
            latest = df.iloc[-1]
            current_price = float(latest['Close'])
            
            # Consecutive Red Calculation
            consecutive_red = 0
            for i in range(len(df)-1, -1, -1):
                c = float(df['Close'].iloc[i])
                o = float(df['Open'].iloc[i])
                v = int(df['Volume'].iloc[i])
                
                # FinMind volume is in Lots (張)
                is_flat_low_vol = (c == o) and (v < 100)
                
                if c >= o and not is_flat_low_vol:
                    consecutive_red += 1
                else:
                    break
            
            # Stop Loss Calculation
            tech_stop = float(latest['Low'])
            money_stop = current_price * 0.90
            stop_loss = max(tech_stop, money_stop)

            # 4. Prepare OHLC Data (Recent 60 days)
            recent_df = df.tail(60)
            ohlc_data = []
            for idx, row in recent_df.iterrows():
                ohlc_data.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": round(float(row['Open']), 2),
                    "high": round(float(row['High']), 2),
                    "low": round(float(row['Low']), 2),
                    "close": round(float(row['Close']), 2),
                    "volume": int(row['Volume']),
                    "k": round(float(row['K']), 1) if not pd.isna(row['K']) else 50,
                    "d": round(float(row['D']), 1) if not pd.isna(row['D']) else 50,
                    "ma5": round(float(row['MA5']), 2) if not pd.isna(row['MA5']) else None,
                    "ma10": round(float(row['MA10']), 2) if not pd.isna(row['MA10']) else None,
                    "ma20": round(float(row['MA20']), 2) if not pd.isna(row['MA20']) else None,
                    "ma60": round(float(row['MA60']), 2) if not pd.isna(row['MA60']) else None
                })
            
            # Latest Values
            prev = df.iloc[-2]
            change_pct = ((current_price - float(prev['Close'])) / float(prev['Close'])) * 100
            
            # 5. Get Name
            name = get_stock_name(ticker_code)

            # 6. Response
            data = {
                "ticker": ticker_code,
                "name": name,
                "currentPrice": round(current_price, 2),
                "changePct": round(change_pct, 2),
                "k": round(float(latest['K']), 1),
                "d": round(float(latest['D']), 1),
                "ohlc": ohlc_data,
                "ma5": round(float(latest['MA5']), 2) if not pd.isna(latest['MA5']) else None,
                "ma10": round(float(latest['MA10']), 2) if not pd.isna(latest['MA10']) else None,
                "ma20": round(float(latest['MA20']), 2) if not pd.isna(latest['MA20']) else None,
                "ma60": round(float(latest['MA60']), 2) if not pd.isna(latest['MA60']) else None,
                "volume": int(latest['Volume']),
                "consecutiveRed": consecutive_red,
                "stopLoss": round(stop_loss, 2)
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            # Disable Caching
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
