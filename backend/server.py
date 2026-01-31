import os
import json
import base64
import re
import numpy as np
import cv2
import pytesseract
from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd

# Try to import twstock for Chinese names
try:
    import twstock
    HAS_TWSTOCK = True
except ImportError:
    HAS_TWSTOCK = False
    print("Warning: twstock not installed")

app = Flask(__name__)
CORS(app)

def parse_text_for_stocks(text):
    """
    Parses raw OCR text to find Taiwan stock patterns.
    Heuristic: Look for 4-digit codes and associated numbers.
    """
    results = []
    lines = text.split('\n')
    
    # Pattern for 4-digit stock code
    code_pattern = re.compile(r'\b([1-9]\d{3}|00\d{2,3})\b')
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        codes = code_pattern.findall(line)
        if not codes: continue
        
        for code in codes:
            name = ""
            cjk_match = re.search(r'[\u4e00-\u9fa5]{2,}', line)
            if cjk_match:
                name = cjk_match.group(0)
            
            numbers = re.findall(r'[\d,]+\.?\d*', line)
            numbers = [n.replace(',', '') for n in numbers if n.replace(',', '') != code]
            
            shares = 0
            cost = 0.0
            
            for n in numbers:
                try:
                    val = float(n)
                    if val >= 1000: 
                        shares = int(val)
                    elif 0 < val < 5000: # Stock price range
                        cost = val
                except: continue
            
            results.append({
                "ticker": code,
                "name": name,
                "shares": shares,
                "cost": cost
            })
    return results

# OCR Endpoint using local Tesseract
@app.route('/api/ocr', methods=['POST'])
def ocr_images():
    req_data = request.json
    if not req_data or 'images' not in req_data:
        return jsonify({"error": "No images provided"}), 400
        
    files = req_data['images']
    if not files:
        return jsonify({"error": "Empty image list"}), 400
        
    print(f"收到 {len(files)} 張圖片進行在地 OCR...")
    
    all_extracted_stocks = []
    
    for img_obj in files:
        try:
            img_bytes = base64.b64decode(img_obj['data'])
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None: continue
            
            # Preprocessing
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            gray = cv2.bilateralFilter(gray, 9, 75, 75)
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
            
            # OCR
            text = pytesseract.image_to_string(thresh, lang='chi_tra+eng', config='--oem 3 --psm 6')
            
            # Parsing
            stocks = parse_text_for_stocks(text)
            all_extracted_stocks.extend(stocks)
        except Exception as e:
            print(f"Processing error: {e}")
            continue

    # Deduplicate
    unique_stocks = {}
    for s in all_extracted_stocks:
        ticker = s['ticker']
        if ticker not in unique_stocks:
            unique_stocks[ticker] = s
        else:
            if not unique_stocks[ticker]['name'] and s['name']:
                unique_stocks[ticker]['name'] = s['name']
            if unique_stocks[ticker]['shares'] == 0 and s['shares'] > 0:
                unique_stocks[ticker]['shares'] = s['shares']
            if unique_stocks[ticker]['cost'] == 0 and s['cost'] > 0:
                unique_stocks[ticker]['cost'] = s['cost']
                
    result = list(unique_stocks.values())
    print(f"在地 OCR 成功，解析出 {len(result)} 筆資料")
    return jsonify(result)

def get_stock_name(ticker_code):
    """Get Chinese name using twstock if available"""
    if HAS_TWSTOCK and ticker_code in twstock.codes:
        return twstock.codes[ticker_code].name
    
    # Fallback to yfinance or just return ticker
    try:
        t = yf.Ticker(f"{ticker_code}.TW")
        info = t.info
        return info.get('longName', info.get('shortName', ticker_code))
    except:
        return ticker_code

def get_stock_history(ticker):
    """Helper to fetch stock history"""
    stock = yf.Ticker(ticker)
    return stock, stock.history(period="6mo")

@app.route('/api/stock', methods=['GET'])
def get_stock():
    ticker = request.args.get('ticker')
    print(f"Received request for ticker: {ticker}")
    
    if not ticker:
        return jsonify({"error": "Missing ticker"}), 400

    try:
        # 1. Determine Suffix (.TW or .TWO)
        ticker_code = ticker.replace('.TW', '').replace('.TWO', '')
        
        # Default logic
        ticker_tw = f"{ticker_code}.TW"
        stock, df = get_stock_history(ticker_tw)
        
        # If empty, try .TWO
        if df.empty:
            ticker_two = f"{ticker_code}.TWO"
            stock, df = get_stock_history(ticker_two)
            if not df.empty:
                ticker_tw = ticker_two # Confirm it's .TWO

        if df.empty:
            return jsonify({"error": "Stock not found"}), 404

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
            if c > o:
                consecutive_red += 1
            else:
                break
        
        # Stop Loss Calculation
        # Tech stop = Low of breakout day (assumed today for simplicity or recent low)
        # Money stop = 10%
        tech_stop = float(latest['Low'])
        money_stop = current_price * 0.90
        stop_loss = max(tech_stop, money_stop)

        # 4. Prepare OHLC Data (Recent 60 days)
        # User reported "interval too large", using 60 is standard but ensure no gaps if possible
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
            # New fields
            "consecutiveRed": consecutive_red,
            "stopLoss": round(stop_loss, 2)
        }

        return jsonify(data)

    except Exception as e:
        print(f"Error fetching stock {ticker}: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
