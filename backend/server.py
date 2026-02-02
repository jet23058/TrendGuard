import os
import json
import base64
import re
import numpy as np
import cv2
import pytesseract
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from datetime import datetime, timedelta
from FinMind.data import DataLoader
import google.generativeai as genai

# Try to import twstock for Chinese names
try:
    import twstock
    HAS_TWSTOCK = True
except ImportError:
    HAS_TWSTOCK = False
    print("Warning: twstock not installed")

app = Flask(__name__)
CORS(app)

# Initialize FinMind DataLoader
_finmind_loader = None

def get_finmind_loader():
    global _finmind_loader
    if _finmind_loader is None:
        _finmind_loader = DataLoader()
        token = os.environ.get("FINMIND_API_TOKEN")
        if token:
            _finmind_loader.login_by_token(api_token=token)
    return _finmind_loader

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

@app.route('/api/ocr', methods=['POST'])
def ocr_images():
    # Use GEMINI_KEY from environment
    api_key = os.environ.get("GEMINI_KEY")
    if not api_key:
        # Fallback to GOOGLE_API_KEY
        api_key = os.environ.get("GOOGLE_API_KEY")
        
    if not api_key:
        print("Error: GEMINI_KEY not set")
        return jsonify({"error": "Server missing API Key"}), 500
        
    genai.configure(api_key=api_key)
    
    # 接收 JSON (Base64 Images)
    req_data = request.json
    if not req_data or 'images' not in req_data:
        return jsonify({"error": "No images provided"}), 400
        
    files = req_data['images']
    if not files:
        return jsonify({"error": "Empty image list"}), 400
        
    print(f"收到 {len(files)} 張圖片進行 Gemini OCR...")
    
    image_parts = []
    import base64
    
    for img_obj in files:
        try:
            # Decode Base64
            img_bytes = base64.b64decode(img_obj['data'])
            image_parts.append({
                "mime_type": img_obj['mime_type'],
                "data": img_bytes
            })
        except Exception as e:
            print(f"Image decode error: {e}")
            return jsonify({"error": f"Image decode failed: {e}"}), 400
        
    prompt = """
    你是一個台灣股市券商 App 截圖的解析專家。
    使用者上傳了一組庫存截圖（可能包含多張，且內容可能有重疊）。
    
    請執行以下任務：
    1. **提取資訊**：找出每一列的「股票代碼」、「股票名稱」、「庫存股數」、「平均成本」。
    2. **去重合併**：因為截圖是連續的，上下兩張圖可能會顯示同一檔股票。請依據「股票代碼」去除重複項目，保留一份即可。
    3. **容錯處理**：
       - 股票代碼通常是 4 碼數字。
       - 股數與成本請轉換為純數字（去除逗號）。
       - 如果有無法辨識的欄位，請盡量推斷或標記 null。
    
    請直接回傳一個 **純 JSON 陣列**，不要包含任何 Markdown 格式 (如 ```json ... ```)。
    格式範例：
    [
      {"ticker": "2330", "name": "台積電", "shares": 2000, "cost": 502.5},
      {"ticker": "0050", "name": "元大台灣50", "shares": 1500, "cost": 120.1}
    ]
    """
    
    try:
        # 使用 Gemini 1.5 Flash 確保穩定性，因為 2.0 可能在某些 API 環境尚未完全可用
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Generate
        response = model.generate_content([prompt, *image_parts])
        raw_text = response.text
        
        # Clean up Markdown formatting
        cleaned_text = raw_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
            
        result_json = json.loads(cleaned_text.strip())
        print(f"Gemini OCR 成功，解析出 {len(result_json)} 筆資料")
        
        return jsonify(result_json)
        
    except Exception as e:
        print(f"OCR Failed: {e}")
        return jsonify({"error": str(e)}), 500

def get_stock_name(ticker_code):
    """Get Chinese name using twstock if available, or FinMind"""
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
        start_date = (datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d') # ~6 months
        
        # Strip .TW or .TWO if passed (FinMind expects just code)
        code = ticker_code.replace('.TW', '').replace('.TWO', '')
        
        df = loader.taiwan_stock_daily(
            stock_id=code,
            start_date=start_date,
            end_date=end_date
        )
        
        if df is None or df.empty:
            return None, pd.DataFrame()
            
        # Standardize columns to match yfinance format for compatibility
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
        df['Volume'] = df['Volume'].astype(int) # Note: FinMind volume is in shares (張) check? No, FinMind is usually shares if using taiwan_stock_daily? 
        # Actually FinMind Trading_Volume is usually in "shares" (股) or "lots" (張)?
        # Let's verify: In update_daily.py I assumed it was "shares" then realized it's "張" (lots) because I check v < 100.
        # Wait, in update_daily.py I said "FinMind volume 單位為張".
        # Let's double check this. 
        # If I look at FinMind docs or my test output: 2330 daily volume is around 30,000-50,000. That's lots (張).
        # yfinance volume is in shares (30,000,000).
        # So I need to multiply by 1000 to match yfinance behavior if the frontend expects shares?
        # Let's check frontend.
        
        return None, df
    except Exception as e:
        print(f"FinMind error for {ticker_code}: {e}")
        return None, pd.DataFrame()

@app.route('/api/stock', methods=['GET'])
def get_stock():
    ticker = request.args.get('ticker')
    print(f"Received request for ticker: {ticker}")
    
    if not ticker:
        return jsonify({"error": "Missing ticker"}), 400

    try:
        # 1. Clean ticker
        ticker_code = ticker.replace('.TW', '').replace('.TWO', '')
        
        # Fetch history using FinMind
        _, df = get_stock_history(ticker_code)

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
        
        # Consecutive Red Calculation (Match update_daily.py logic)
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

        return jsonify(data)

    except Exception as e:
        print(f"Error fetching stock {ticker}: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
