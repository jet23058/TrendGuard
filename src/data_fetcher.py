"""
Data Fetcher Module - 股票資料抓取
Uses yfinance to fetch Taiwan stock data
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_stock_data(symbol: str, period: str = "1mo") -> pd.DataFrame:
    """
    取得股票歷史 K 線資料
    
    Args:
        symbol: 股票代碼 (不含 .TW 後綴)
        period: 資料期間 (1d, 5d, 1mo, 3mo, 6mo, 1y)
    
    Returns:
        DataFrame with OHLCV data
    """
    ticker_symbol = f"{symbol}.TW"
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period=period)
        if df.empty:
            # Try .TWO for OTC stocks
            ticker_symbol = f"{symbol}.TWO"
            ticker = yf.Ticker(ticker_symbol)
            df = ticker.history(period=period)
        return df
    except Exception as e:
        st.error(f"無法取得 {symbol} 的資料: {e}")
        return pd.DataFrame()


def get_current_price(symbol: str) -> dict:
    """
    取得即時價格資訊
    
    Args:
        symbol: 股票代碼
    
    Returns:
        dict with current price, change, change_pct
    """
    ticker_symbol = f"{symbol}.TW"
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # Get from fast_info if available
        if hasattr(ticker, 'fast_info'):
            fast = ticker.fast_info
            current = fast.get('lastPrice', 0)
            prev_close = fast.get('previousClose', current)
        else:
            current = info.get('currentPrice', info.get('regularMarketPrice', 0))
            prev_close = info.get('previousClose', current)
        
        if current == 0:
            # Fallback to history
            hist = ticker.history(period="2d")
            if not hist.empty:
                current = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current
        
        change = current - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        
        return {
            "current": current,
            "prev_close": prev_close,
            "change": change,
            "change_pct": change_pct
        }
    except Exception as e:
        return {
            "current": 0,
            "prev_close": 0,
            "change": 0,
            "change_pct": 0,
            "error": str(e)
        }


def get_stock_info(symbol: str) -> dict:
    """
    取得股票基本資訊
    
    Args:
        symbol: 股票代碼
    
    Returns:
        dict with stock name and other info
    """
    ticker_symbol = f"{symbol}.TW"
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        name = info.get('longName', info.get('shortName', symbol))
        
        # Extract Chinese name if available
        if name and '(' in name:
            name = name.split('(')[0].strip()
        
        return {
            "name": name,
            "symbol": symbol,
            "market": info.get('market', 'TW'),
            "sector": info.get('sector', ''),
            "industry": info.get('industry', ''),
        }
    except Exception:
        return {
            "name": symbol,
            "symbol": symbol,
            "market": "TW",
            "sector": "",
            "industry": "",
        }


def get_multiple_stocks_data(symbols: list, period: str = "1mo") -> dict:
    """
    批次取得多檔股票資料
    
    Args:
        symbols: 股票代碼列表
        period: 資料期間
    
    Returns:
        dict with symbol as key and DataFrame as value
    """
    result = {}
    for symbol in symbols:
        result[symbol] = get_stock_data(symbol, period)
    return result
