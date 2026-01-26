import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, '.')
from scripts.update_daily import check_livermore_criteria, LOOKBACK_DAYS

def create_mock_df(last_days_data, total_days=70):
    """
    Create a DataFrame with sufficient history (Must be > 60 for MA60).
    Fill history with 'base_price' to ensure MAs are stable.
    Append 'last_days_data' at the end.
    """
    base_price = 10.0
    history_len = total_days - len(last_days_data)
    
    data = {
        'Open': [base_price] * history_len,
        'High': [base_price] * history_len,
        'Low': [base_price] * history_len,
        'Close': [base_price] * history_len,
        'Volume': [200000] * history_len # High volume to prevent history being filtered out
    }
    
    df_hist = pd.DataFrame(data)
    df_new = pd.DataFrame(last_days_data)
    
    df = pd.concat([df_hist, df_new], ignore_index=True)
    
    # Generate dates
    dates = pd.date_range(end=pd.Timestamp.now(), periods=len(df))
    df.index = dates
    return df

@patch('scripts.update_daily.get_stock_name')
@patch('scripts.update_daily.yf.download')
def test_flat_line_low_volume_exclusion(mock_download, mock_get_name):
    """
    Case 1: 昨日是一字線且量縮 (<100張)，今日大漲。
    預期結果: 連紅天數為 1 (昨日被視為斷點)，因不滿 2 天連紅而被剔除 (Result None)。
    """
    mock_get_name.return_value = ("Test Stock", "Test Sector")
    
    # 最後兩天資料
    # Day -2 (Yesterday): 10.0, Vol 500 (Low Vol) -> Flat Line
    # Day -1 (Today): 13.0, Vol 200000 -> Red K
    last_days = {
        'Open':   [10.0, 13.0],
        'High':   [10.0, 13.5],
        'Low':    [10.0, 12.5],
        'Close':  [10.0, 13.0], # Day -1 Close > Open? No, 13=13 is Flat? 
                                # Wait, I want today to be Red K.
                                # Let's make today strong: Open 12, Close 13
        'Volume': [500, 200000]
    }
    
    # Correcting Today's data to be a clear Red K
    last_days['Open'][1] = 12.0
    
    df = create_mock_df(last_days, total_days=80)
    mock_download.return_value = df
    
    # Run
    # 假裝在當沖白名單內
    result, pct = check_livermore_criteria('2330', {}, {'2330'})
    
    # 驗證
    # 昨日 (idx -2) 是 10.0/10.0/500 -> Flat Low Vol -> Not Red
    # 今日 (idx -1) 是 12.0/13.0 -> Red
    # Consecutive Red = 1
    # 條件 is_two_red_k = False
    # Result should be None
    assert result is None
    # Change pct should still be calculated
    assert pct is not None

@patch('scripts.update_daily.get_stock_name')
@patch('scripts.update_daily.yf.download')
def test_flat_line_high_volume_inclusion(mock_download, mock_get_name):
    """
    Case 2: 昨日是一字線但量大 (>100張)，今日大漲。
    預期結果: 連紅天數為 2 (昨日視為強勢紅K)，符合條件。
    """
    mock_get_name.return_value = ("Test Stock", "Test Sector")
    
    # Day -2 (Yesterday): 10.0, Vol 150000 (High Vol) -> Flat Line but Valid
    # Day -1 (Today): 12.0 -> 13.0 -> Red K
    last_days = {
        'Open':   [10.0, 12.0],
        'High':   [10.0, 13.5],
        'Low':    [10.0, 12.0],
        'Close':  [10.0, 13.0],
        'Volume': [150000, 200000] # 150,000 > 100,000
    }
    
    df = create_mock_df(last_days, total_days=80)
    mock_download.return_value = df
    
    # Run
    result, pct = check_livermore_criteria('2330', {}, {'2330'})
    
    # 驗證
    # Consecutive Red = 2 (or more, since history is valid)
    # Result should be valid data dict
    assert result is not None
    assert result['consecutiveRed'] >= 2
    assert result['ticker'] == '2330'

@patch('scripts.update_daily.get_stock_name')
@patch('scripts.update_daily.yf.download')
def test_flat_line_boundary_condition(mock_download, mock_get_name):
    """
    Case 3: 邊界測試，剛好 99,999 vs 100,000
    """
    mock_get_name.return_value = ("Test Stock", "Test Sector")
    
    # Day -3: Normal Red
    # Day -2: Flat, Vol 99,999 -> Invalid
    # Day -1: Red
    last_days = {
        'Open':   [10.0, 10.0, 12.0],
        'High':   [10.5, 10.0, 13.5],
        'Low':    [9.5,  10.0, 12.0],
        'Close':  [10.5, 10.0, 13.0],
        'Volume': [200000, 99999, 200000]
    }
    
    df = create_mock_df(last_days, total_days=80)
    mock_download.return_value = df
    
    result, _ = check_livermore_criteria('2330', {}, {'2330'})
    assert result is None # Broken by 99999
    
    # Now try 100,000
    last_days['Volume'][1] = 100000
    df2 = create_mock_df(last_days, total_days=80)
    mock_download.return_value = df2
    
    result2, _ = check_livermore_criteria('2330', {}, {'2330'})
    assert result2 is not None
    assert result2['consecutiveRed'] >= 2 # 應該是 2 或 3 (取決於之前的假資料是否紅K)
    # My mock history creates flat lines (base_price).
    # Base: Open=10, Close=10, Vol=50000. This is Flat Low Vol.
    # So history is NOT Red.
    # So consecutiveRed should be exactly 3 (Day -3, -2, -1)
    # Wait, Day -3 is 10.0->10.5 (Red).
    # Day -2 is 10.0->10.0 (Flat High Vol).
    # Day -1 is 12.0->13.0 (Red).
    # So at least 3 days.
    assert result2['consecutiveRed'] >= 3
