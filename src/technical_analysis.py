"""
Technical Analysis Module - KD 指標計算與技術分析
"""
import pandas as pd
import numpy as np
import pandas_ta as ta


def calculate_kd(df: pd.DataFrame, k_period: int = 9, d_period: int = 3, smooth_k: int = 3) -> pd.DataFrame:
    """
    計算 KD 指標 (Stochastic Oscillator)
    
    Args:
        df: OHLCV DataFrame
        k_period: K 週期 (預設 9)
        d_period: D 週期 (預設 3)
        smooth_k: K 平滑週期 (預設 3)
    
    Returns:
        DataFrame with K and D columns added
    """
    if df.empty:
        return df
    
    # Calculate using pandas_ta
    stoch = ta.stoch(df['High'], df['Low'], df['Close'], 
                     k=k_period, d=d_period, smooth_k=smooth_k)
    
    if stoch is not None:
        df['K'] = stoch[f'STOCHk_{k_period}_{d_period}_{smooth_k}']
        df['D'] = stoch[f'STOCHd_{k_period}_{d_period}_{smooth_k}']
    else:
        # Manual calculation as fallback
        low_min = df['Low'].rolling(window=k_period).min()
        high_max = df['High'].rolling(window=k_period).max()
        
        rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
        df['K'] = rsv.ewm(span=smooth_k, adjust=False).mean()
        df['D'] = df['K'].ewm(span=d_period, adjust=False).mean()
    
    return df


def detect_kd_cross(df: pd.DataFrame) -> dict:
    """
    偵測 KD 金叉/死叉
    
    Args:
        df: DataFrame with K and D columns
    
    Returns:
        dict with cross type and details
    """
    if df.empty or 'K' not in df.columns or 'D' not in df.columns:
        return {"type": None, "date": None}
    
    # Get the last few rows
    recent = df.tail(5).copy()
    
    if len(recent) < 2:
        return {"type": None, "date": None}
    
    # Check for golden cross (K crosses above D)
    prev_k = recent['K'].iloc[-2]
    prev_d = recent['D'].iloc[-2]
    curr_k = recent['K'].iloc[-1]
    curr_d = recent['D'].iloc[-1]
    
    if prev_k < prev_d and curr_k > curr_d:
        return {
            "type": "golden",
            "date": recent.index[-1],
            "k_value": curr_k,
            "d_value": curr_d
        }
    elif prev_k > prev_d and curr_k < curr_d:
        return {
            "type": "death",
            "date": recent.index[-1],
            "k_value": curr_k,
            "d_value": curr_d
        }
    
    return {"type": None, "date": None, "k_value": curr_k, "d_value": curr_d}


def get_kd_status(k_value: float) -> dict:
    """
    取得 KD 狀態描述
    
    Args:
        k_value: K 值
    
    Returns:
        dict with status and color
    """
    if k_value >= 80:
        return {
            "status": "過熱區",
            "description": "K值 > 80，處於超買區，注意回檔風險",
            "color": "#FF6B6B",
            "level": "overbought"
        }
    elif k_value <= 20:
        return {
            "status": "超賣區",
            "description": "K值 < 20，處於超賣區，可能有反彈機會",
            "color": "#00D4AA",
            "level": "oversold"
        }
    elif k_value >= 50:
        return {
            "status": "多方區",
            "description": "K值位於 50 以上，多方佔優勢",
            "color": "#FFD93D",
            "level": "bullish"
        }
    else:
        return {
            "status": "空方區",
            "description": "K值位於 50 以下，空方佔優勢",
            "color": "#6C7A89",
            "level": "bearish"
        }


def get_volume_analysis(df: pd.DataFrame, window: int = 5) -> dict:
    """
    量能分析
    
    Args:
        df: OHLCV DataFrame
        window: 均量計算週期 (預設 5 日)
    
    Returns:
        dict with volume analysis
    """
    if df.empty or 'Volume' not in df.columns:
        return {"ratio": 0, "status": "無資料", "avg_volume": 0}
    
    df['MA_Volume'] = df['Volume'].rolling(window=window).mean()
    
    current_volume = df['Volume'].iloc[-1]
    avg_volume = df['MA_Volume'].iloc[-1]
    
    if avg_volume > 0:
        ratio = current_volume / avg_volume
    else:
        ratio = 0
    
    if ratio >= 2.0:
        status = "爆量"
        description = f"成交量為 {window} 日均量的 {ratio:.1f} 倍，量能明顯放大"
    elif ratio >= 1.5:
        status = "量增"
        description = f"成交量為 {window} 日均量的 {ratio:.1f} 倍，量能增加"
    elif ratio >= 0.8:
        status = "正常"
        description = f"成交量接近 {window} 日均量"
    elif ratio >= 0.5:
        status = "量縮"
        description = f"成交量為 {window} 日均量的 {ratio:.1f} 倍，量能萎縮"
    else:
        status = "極度量縮"
        description = f"成交量不足 {window} 日均量的一半，動能消失"
    
    return {
        "current_volume": current_volume,
        "avg_volume": avg_volume,
        "ratio": ratio,
        "status": status,
        "description": description
    }


def detect_breakout(df: pd.DataFrame, lookback: int = 20) -> dict:
    """
    偵測價格突破
    
    Args:
        df: OHLCV DataFrame
        lookback: 回看週期
    
    Returns:
        dict with breakout info
    """
    if df.empty or len(df) < lookback:
        return {"is_breakout": False, "type": None}
    
    current_close = df['Close'].iloc[-1]
    prev_high = df['High'].iloc[-lookback:-1].max()
    prev_low = df['Low'].iloc[-lookback:-1].min()
    
    if current_close > prev_high:
        return {
            "is_breakout": True,
            "type": "upward",
            "level": prev_high,
            "description": f"突破近 {lookback} 日高點 {prev_high:.2f}"
        }
    elif current_close < prev_low:
        return {
            "is_breakout": True,
            "type": "downward",
            "level": prev_low,
            "description": f"跌破近 {lookback} 日低點 {prev_low:.2f}"
        }
    
    return {"is_breakout": False, "type": None}
