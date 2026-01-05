from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import numpy as np

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/stock', methods=['GET'])
def get_stock():
    ticker = request.args.get('ticker')
    print(f"Received request for ticker: {ticker}")
    
    if not ticker:
        return jsonify({"error": "Missing ticker"}), 400

    try:
        # Handle .TW suffix logic
        if not ticker.endswith('.TW') and not ticker.endswith('.TWO'):
            # Default to .TW
            ticker_tw = f"{ticker}.TW"
        else:
            ticker_tw = ticker

        stock = yf.Ticker(ticker_tw)
        df = stock.history(period="6mo")
        
        # If .TW empty, try .TWO
        if df.empty and not ticker.endswith('.TWO'):
            ticker_two = ticker.replace('.TW', '') + ".TWO"
            stock = yf.Ticker(ticker_two)
            df = stock.history(period="6mo")
            if not df.empty:
                ticker_tw = ticker_two
        
        if df.empty:
            return jsonify({"error": "Stock not found"}), 404

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
            "ticker": ticker.replace('.TW', '').replace('.TWO', ''),
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

        return jsonify(data)

    except Exception as e:
        print(f"Error fetching stock {ticker}: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run on port 5000
    app.run(debug=True, port=5000)
