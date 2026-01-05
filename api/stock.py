from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import yfinance as yf
import pandas as pd
import numpy as np

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
            # Handle .TW suffix
            if not ticker.endswith('.TW') and not ticker.endswith('.TWO'):
                # Try finding listing (TW vs TWO) - yfinance usually needs exact suffix
                # We assume .TW for simplicity if not provided, or search?
                # For safety, frontend should pass full ticker, or we default to .TW
                ticker = f"{ticker}.TW"

            stock = yf.Ticker(ticker)
            df = stock.history(period="6mo")
            
            if df.empty:
                # Try .TWO
                ticker = ticker.replace('.TW', '.TWO')
                stock = yf.Ticker(ticker)
                df = stock.history(period="6mo")

            if df.empty:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Stock not found"}).encode())
                return

            # Calculate Indicators
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

            # Prepare OHLC Data for Frontend
            recent_df = df.tail(60) # Last 60 days
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
                    "ma20": round(float(row['MA20']), 2) if not pd.isna(row['MA20']) else None
                })
            
            # Latest Values
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            current_price = float(latest['Close'])
            change_pct = ((current_price - float(prev['Close'])) / float(prev['Close'])) * 100
            
            # Basic Info
            try:
                info = stock.info
                name = info.get('longName', info.get('shortName', ticker))
            except:
                name = ticker

            # Response
            data = {
                "ticker": ticker.replace('.TW', '').replace('.TWO', ''), # Strip suffix for display
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
                "volume": int(latest['Volume'])
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
