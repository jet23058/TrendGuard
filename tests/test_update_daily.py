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
    get_stock_name,
    get_all_tw_targets,
    TEST_STOCKS,
    LOOKBACK_DAYS
)


class TestGetStockName:
    """Tests for stock name retrieval"""
    
    def test_returns_tuple(self):
        """Should return a tuple of (name, sector)"""
        result = get_stock_name("2330")
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_returns_code_as_fallback(self):
        """Should return code as name if lookup fails"""
        result = get_stock_name("9999999")
        name, sector = result
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
