#!/usr/bin/env python3
"""
Test suite for StockDataFacade

According to TDD principles:
1. Write failing tests first (Red)
2. Implement minimum code to pass (Green)
3. Refactor if needed
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import os


class TestStockDataFacade(unittest.TestCase):
    """Test cases for Stock Data Facade Pattern"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Import here to allow the module to be created first
        from stock_data_facade import StockDataFacade
        self.facade = StockDataFacade()
        
    def test_facade_initialization_default_twse(self):
        """Test that facade defaults to TWSE provider when not specified"""
        from stock_data_facade import StockDataFacade
        
        # Default should be TWSE
        facade = StockDataFacade()
        self.assertEqual(facade.provider, 'twse')
        
    def test_facade_initialization_with_env(self):
        """Test that facade respects STOCK_DATA_PROVIDER environment variable"""
        from stock_data_facade import StockDataFacade
        
        with patch.dict(os.environ, {'STOCK_DATA_PROVIDER': 'finmind'}):
            facade = StockDataFacade()
            self.assertEqual(facade.provider, 'finmind')
            
    def test_get_stock_price_returns_data(self):
        """Test that get_stock_price returns data in expected format"""
        # Test data structure
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        data = self.facade.get_stock_price('2330', start_date, end_date)
        
        # Should return a list
        self.assertIsInstance(data, list)
        
        # If data exists, check structure
        if len(data) > 0:
            first_item = data[0]
            # Required fields
            self.assertIn('date', first_item)
            self.assertIn('open', first_item)
            self.assertIn('high', first_item)
            self.assertIn('low', first_item)
            self.assertIn('close', first_item)
            self.assertIn('volume', first_item)
            
    def test_get_stock_info_returns_name(self):
        """Test that get_stock_info returns stock name"""
        info = self.facade.get_stock_info('2330')
        
        self.assertIsInstance(info, dict)
        self.assertIn('stock_name', info)
        self.assertIn('stock_id', info)
        
    def test_twse_provider_fetch_stock_price(self):
        """Test TWSE provider can fetch stock price data"""
        from stock_data_facade import TWSEProvider
        
        provider = TWSEProvider()
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        data = provider.fetch_stock_price('2330', start_date, end_date)
        
        # Should return list (may be empty if no data)
        self.assertIsInstance(data, list)
        
    def test_finmind_provider_fetch_stock_price(self):
        """Test FinMind provider can fetch stock price data"""
        from stock_data_facade import FinMindProvider
        
        provider = FinMindProvider()
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        data = provider.fetch_stock_price('2330', start_date, end_date)
        
        # Should return list (may be empty if no data)
        self.assertIsInstance(data, list)
        
    def test_provider_switch(self):
        """Test that facade can switch between providers"""
        from stock_data_facade import StockDataFacade
        
        facade = StockDataFacade(provider='twse')
        self.assertEqual(facade.provider, 'twse')
        
        facade.set_provider('finmind')
        self.assertEqual(facade.provider, 'finmind')
        
    def test_invalid_provider_raises_error(self):
        """Test that invalid provider raises ValueError"""
        from stock_data_facade import StockDataFacade
        
        with self.assertRaises(ValueError):
            StockDataFacade(provider='invalid_provider')
            
    def test_twse_provider_handles_api_errors(self):
        """Test that TWSE provider gracefully handles API errors"""
        from stock_data_facade import TWSEProvider
        
        provider = TWSEProvider()
        
        # Invalid stock ID should return empty list or handle gracefully
        data = provider.fetch_stock_price('INVALID', '2024-01-01', '2024-01-31')
        self.assertIsInstance(data, list)
        
    def test_data_format_consistency(self):
        """Test that both providers return data in the same format"""
        from stock_data_facade import StockDataFacade
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        
        # Test TWSE
        facade_twse = StockDataFacade(provider='twse')
        data_twse = facade_twse.get_stock_price('2330', start_date, end_date)
        
        # Test FinMind
        facade_finmind = StockDataFacade(provider='finmind')
        data_finmind = facade_finmind.get_stock_price('2330', start_date, end_date)
        
        # Both should have same structure (if data exists)
        if len(data_twse) > 0 and len(data_finmind) > 0:
            twse_keys = set(data_twse[0].keys())
            finmind_keys = set(data_finmind[0].keys())
            
            # Check for required fields
            required_fields = {'date', 'open', 'high', 'low', 'close', 'volume'}
            self.assertTrue(required_fields.issubset(twse_keys))
            self.assertTrue(required_fields.issubset(finmind_keys))


if __name__ == '__main__':
    unittest.main()
