import sys
from unittest.mock import MagicMock

# Mock external dependencies to allow import without installation
sys.modules['yfinance'] = MagicMock()
sys.modules['twstock'] = MagicMock()
sys.modules['pandas'] = MagicMock()

import unittest
import json
from pathlib import Path
from scripts import update_daily

class TestDailyDiff(unittest.TestCase):
    def setUp(self):
        # Sample stock data structure
        self.stock_a = {'ticker': '1111', 'name': 'Stock A', 'sector': 'Sector A'}
        self.stock_b = {'ticker': '2222', 'name': 'Stock B', 'sector': 'Sector B'}
        self.stock_c = {'ticker': '3333', 'name': 'Stock C', 'sector': 'Sector C'}

    def test_calculate_diff(self):
        """Test the logic for New, Continued, and Removed stocks"""
        # Previous day had: A and B
        previous_data = {
            'stocks': [self.stock_a, self.stock_b]
        }
        
        # Current day has: B and C
        current_stocks = [
            self.stock_b, # Continued
            self.stock_c  # New
        ]
        
        # Expected:
        # New: C
        # Continued: B
        # Removed: A
        
        changes = update_daily.calculate_changes(previous_data, current_stocks)
        
        self.assertEqual(len(changes['new']), 1)
        self.assertEqual(changes['new'][0]['ticker'], '3333')
        
        self.assertEqual(len(changes['continued']), 1)
        self.assertEqual(changes['continued'][0]['ticker'], '2222')
        
        self.assertEqual(len(changes['removed']), 1)
        self.assertEqual(changes['removed'][0]['ticker'], '1111')

    def test_no_previous_data(self):
        """Test when there is no previous data"""
        previous_data = None
        current_stocks = [self.stock_a]
        
        changes = update_daily.calculate_changes(previous_data, current_stocks)
        
        # All current should be 'new' (or maybe handled differently, but logically new)
        # If no previous data, we assume everything is new
        self.assertEqual(len(changes['new']), 1)
        self.assertEqual(len(changes['continued']), 0)
        self.assertEqual(len(changes['removed']), 0)

if __name__ == '__main__':
    unittest.main()
