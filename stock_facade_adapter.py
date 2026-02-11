#!/usr/bin/env python3
"""
Helper module to integrate StockDataFacade with existing FinMind-based code

This module provides adapter functions to make the transition from FinMind
to the Facade pattern seamless for existing code.
"""

import os
import pandas as pd
from datetime import datetime
from stock_data_facade import StockDataFacade


# Singleton instance
_facade = None


def get_stock_facade():
    """Get or create StockDataFacade singleton"""
    global _facade
    if _facade is None:
        _facade = StockDataFacade()
        provider = _facade.get_provider_name()
        print(f"✅ Stock Data Provider initialized: {provider.upper()}")
    return _facade


def get_stock_price_as_dataframe(stock_id, start_date, end_date):
    """
    Fetch stock price data and return as pandas DataFrame
    
    This function mimics the FinMind DataLoader.taiwan_stock_daily() behavior
    to ensure backward compatibility with existing code.
    
    Args:
        stock_id: Stock ticker code
        start_date: Start date string 'YYYY-MM-DD'
        end_date: End date string 'YYYY-MM-DD'
        
    Returns:
        pandas DataFrame with columns: date, stock_id, open, max, min, close, Trading_Volume
    """
    facade = get_stock_facade()
    
    try:
        data = facade.get_stock_price(stock_id, start_date, end_date)
        
        if not data:
            return None
        
        # Convert to DataFrame with FinMind-compatible column names
        df = pd.DataFrame(data)
        
        # Rename columns to match FinMind format
        df = df.rename(columns={
            'high': 'max',
            'low': 'min',
            'volume': 'Trading_Volume'
        })
        
        # Add stock_id column
        df['stock_id'] = stock_id
        
        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Reorder columns to match FinMind format
        df = df[['date', 'stock_id', 'Trading_Volume', 'open', 'max', 'min', 'close']]
        
        return df
        
    except Exception as e:
        print(f"Error fetching stock price for {stock_id}: {e}")
        return None


def get_stock_info(stock_id):
    """
    Get stock information
    
    Args:
        stock_id: Stock ticker code
        
    Returns:
        Dictionary with stock_id and stock_name
    """
    facade = get_stock_facade()
    
    try:
        return facade.get_stock_info(stock_id)
    except Exception as e:
        print(f"Error fetching stock info for {stock_id}: {e}")
        return {'stock_id': stock_id, 'stock_name': stock_id}


# Mock DataLoader class for backward compatibility
class FacadeDataLoader:
    """
    Mock DataLoader class that uses StockDataFacade internally
    
    This class provides the same interface as FinMind's DataLoader
    but uses the facade pattern to support multiple data providers.
    """
    
    def __init__(self):
        self.facade = get_stock_facade()
    
    def login_by_token(self, api_token=None):
        """
        Mock login method for compatibility
        
        Note: This only affects FinMind provider if STOCK_DATA_PROVIDER=finmind
        """
        if self.facade.get_provider_name() == 'finmind':
            print("FinMind provider is active - token will be used from environment")
        else:
            print(f"Current provider: {self.facade.get_provider_name()} - no token needed")
    
    def taiwan_stock_daily(self, stock_id, start_date, end_date):
        """
        Fetch Taiwan stock daily data
        
        Returns pandas DataFrame compatible with FinMind format
        """
        return get_stock_price_as_dataframe(stock_id, start_date, end_date)
    
    def TaiwanStockInfo(self):
        """
        Mock method for getting Taiwan stock info
        
        Note: This method is not fully implemented as it requires fetching
        all stock info, which is not efficient. Use get_stock_info() instead
        for individual stocks.
        """
        print("Warning: TaiwanStockInfo() is not fully implemented in facade mode")
        print("Use get_stock_info(stock_id) for individual stock information")
        return pd.DataFrame()
