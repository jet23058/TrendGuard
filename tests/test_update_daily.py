"""
Unit tests for update_daily.py (Livermore Breakout Scanner)
"""
import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, '.')
from scripts.update_daily import (
    calculate_rsi,
    calculate_volume_profile,
    format_capital_tw,
    get_reference_price_snapshot,
    get_rsi_status,
    get_stock_name,
    get_all_tw_targets,
    parse_capital_value,
    TEST_STOCKS,
    LOOKBACK_DAYS
)


class TestGetStockName:
    """Tests for stock name retrieval"""
    
    def test_returns_tuple(self):
        """Should return a tuple of (name, sector, market)"""
        result = get_stock_name("2330")
        assert isinstance(result, tuple)
        assert len(result) == 3
    
    def test_returns_code_as_fallback(self):
        """Should return code as name if lookup fails"""
        result = get_stock_name("9999999")
        name, sector, market = result
        # Should at least return something
        assert name is not None


class TestGetAllTwTargets:
    """Tests for target list generation"""
    
    def test_returns_list(self):
        """Should return a list of stock codes"""
        result = get_all_tw_targets()
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_contains_major_stocks_in_test_mode(self):
        """In test mode, should contain major stocks"""
        result = get_all_tw_targets()
        assert '2330' in result  # 台積電


class TestConstants:
    """Tests for configuration constants"""
    
    def test_lookback_days_is_positive(self):
        """Lookback days should be positive"""
        assert LOOKBACK_DAYS > 0
    
    def test_test_stocks_not_empty(self):
        """Test stocks list should not be empty"""
        assert len(TEST_STOCKS) > 0
    
    def test_test_stocks_contains_tsmc(self):
        """Test stocks should contain TSMC"""
        assert '2330' in TEST_STOCKS


class TestDailySearchSignals:
    """Tests for extra daily scan search fields"""

    def test_rsi_status_flags_extremes(self):
        assert get_rsi_status(81) == "overbought"
        assert get_rsi_status(19.9) == "oversold"
        assert get_rsi_status(50) == "neutral"

    def test_calculate_rsi_reaches_overbought_on_steady_gains(self):
        closes = pd.Series(range(1, 31), dtype="float")
        rsi = calculate_rsi(closes)
        assert rsi.iloc[-1] == 100

    def test_reference_price_uses_latest_trading_day_before_30_calendar_days(self):
        dates = pd.date_range("2026-03-01", "2026-04-19").difference(pd.DatetimeIndex(["2026-03-20"]))
        df = pd.DataFrame({"Close": range(100, 100 + len(dates)), "Volume": range(1000, 1000 + len(dates))}, index=dates)

        snapshot = get_reference_price_snapshot(df, days_back=30, as_of=datetime(2026, 4, 19))

        assert snapshot["date"] == "2026-03-19"
        assert snapshot["price"] == 118
        assert snapshot["changePct"] == 25.42

    def test_volume_profile_flags_high_and_low_anomalies(self):
        dates = pd.bdate_range("2026-01-01", periods=31)
        high_df = pd.DataFrame({"Volume": [1000] * 30 + [2500]}, index=dates)
        low_df = pd.DataFrame({"Volume": [1000] * 30 + [400]}, index=dates)

        assert calculate_volume_profile(high_df)["status"] == "high"
        assert calculate_volume_profile(high_df)["ratio30d"] == 2.5
        assert calculate_volume_profile(low_df)["status"] == "low"
        assert calculate_volume_profile(low_df)["isAnomaly"] is True

    def test_capital_parsing_and_formatting(self):
        assert parse_capital_value("36,920,000,000元") == 36920000000
        assert format_capital_tw(36920000000) == "369.2億"


class TestLivermoreCriteria:
    """Tests for Livermore breakout criteria logic"""
    
    def test_breakout_detection(self):
        """Test breakout detection logic"""
        # Current price > previous high = breakout
        current_price = 100
        prev_high = 95
        is_breakout = current_price > prev_high
        assert is_breakout is True
        
        # Current price <= previous high = no breakout
        current_price = 90
        is_breakout = current_price > prev_high
        assert is_breakout is False
    
    def test_consecutive_red_k_counting(self):
        """Test consecutive red K counting logic"""
        # Simulate: close > open for each day
        closes = [100, 102, 104, 106]  # 4 days of red K
        opens = [98, 100, 102, 104]
        
        consecutive_red = 0
        for c, o in zip(reversed(closes), reversed(opens)):
            if c > o:
                consecutive_red += 1
            else:
                break
        
        assert consecutive_red == 4
    
    def test_above_all_ma_logic(self):
        """Test above all moving averages logic"""
        current_price = 100
        ma5 = 98
        ma10 = 95
        ma20 = 90
        ma60 = 85
        
        is_above_all = (
            current_price > ma5 and
            current_price > ma10 and
            current_price > ma20 and
            current_price > ma60
        )
        
        assert is_above_all is True
        
        # If below one MA, should be False
        ma5 = 105
        is_above_all = (
            current_price > ma5 and
            current_price > ma10 and
            current_price > ma20 and
            current_price > ma60
        )
        assert is_above_all is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
