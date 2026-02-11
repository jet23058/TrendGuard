#!/usr/bin/env python3
"""
Stock Data Facade Pattern Implementation

This facade provides a unified interface for fetching stock data from multiple sources:
1. TWSE (Taiwan Stock Exchange) - No API limit, but may have less features
2. FinMind - Feature-rich but has API rate limits

Environment Variable:
    STOCK_DATA_PROVIDER: Set to 'twse' or 'finmind' (default: 'twse')
    
Usage:
    from stock_data_facade import StockDataFacade
    
    facade = StockDataFacade()  # Uses STOCK_DATA_PROVIDER env or defaults to 'twse'
    data = facade.get_stock_price('2330', '2024-01-01', '2024-01-31')
"""

import os
import requests
import time
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class StockDataProvider(ABC):
    """Abstract base class for stock data providers"""
    
    @abstractmethod
    def fetch_stock_price(self, stock_id: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Fetch stock price data
        
        Args:
            stock_id: Stock ticker code (e.g., '2330')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            List of dictionaries with keys: date, open, high, low, close, volume
        """
        pass
    
    @abstractmethod
    def fetch_stock_info(self, stock_id: str) -> Dict:
        """
        Fetch stock information (name, etc.)
        
        Args:
            stock_id: Stock ticker code
            
        Returns:
            Dictionary with keys: stock_id, stock_name
        """
        pass


class TWSEProvider(StockDataProvider):
    """Taiwan Stock Exchange data provider"""
    
    def __init__(self):
        self.base_url = "https://www.twse.com.tw"
        
    def fetch_stock_price(self, stock_id: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Fetch stock price from TWSE API
        
        TWSE API provides monthly data, so we need to fetch multiple months
        if the date range spans across months.
        """
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            all_data = []
            
            # Generate list of year-month pairs to fetch
            current_dt = start_dt.replace(day=1)
            while current_dt <= end_dt:
                year = current_dt.year
                month = current_dt.month
                
                # Fetch data for this month
                monthly_data = self._fetch_monthly_data(stock_id, year, month)
                all_data.extend(monthly_data)
                
                # Move to next month
                if month == 12:
                    current_dt = current_dt.replace(year=year + 1, month=1)
                else:
                    current_dt = current_dt.replace(month=month + 1)
            
            # Filter data within date range
            filtered_data = [
                item for item in all_data
                if start_date <= item['date'] <= end_date
            ]
            
            return filtered_data
            
        except Exception as e:
            print(f"TWSE API Error: {e}")
            return []
    
    def _fetch_monthly_data(self, stock_id: str, year: int, month: int) -> List[Dict]:
        """Fetch stock data for a specific month from TWSE"""
        try:
            # Small delay to avoid rate limiting (TWSE recommends not too frequent)
            time.sleep(0.1)
            
            # TWSE API endpoint for daily stock data
            url = f"{self.base_url}/exchangeReport/STOCK_DAY"
            params = {
                'response': 'json',
                'date': f'{year}{month:02d}01',  # First day of the month
                'stockNo': stock_id
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            
            # Check if request was successful
            if data.get('stat') != 'OK':
                return []
            
            # Parse data
            results = []
            fields = data.get('fields', [])
            raw_data = data.get('data', [])
            
            # Find field indices
            # Expected fields: ['日期', '成交股數', '成交金額', '開盤價', '最高價', '最低價', '收盤價', '漲跌價差', '成交筆數']
            date_idx = fields.index('日期') if '日期' in fields else 0
            volume_idx = fields.index('成交股數') if '成交股數' in fields else 1
            open_idx = fields.index('開盤價') if '開盤價' in fields else 3
            high_idx = fields.index('最高價') if '最高價' in fields else 4
            low_idx = fields.index('最低價') if '最低價' in fields else 5
            close_idx = fields.index('收盤價') if '收盤價' in fields else 6
            
            for row in raw_data:
                try:
                    # Parse date from ROC format (e.g., "113/01/02" -> "2024-01-02")
                    date_str = row[date_idx].strip()
                    date_parts = date_str.split('/')
                    if len(date_parts) == 3:
                        roc_year = int(date_parts[0])
                        ad_year = roc_year + 1911
                        formatted_date = f"{ad_year}-{date_parts[1]}-{date_parts[2]}"
                    else:
                        continue
                    
                    # Parse price data (remove commas and convert)
                    open_price = float(row[open_idx].replace(',', ''))
                    high_price = float(row[high_idx].replace(',', ''))
                    low_price = float(row[low_idx].replace(',', ''))
                    close_price = float(row[close_idx].replace(',', ''))
                    
                    # Parse volume (remove commas, convert to lots/張)
                    volume_str = row[volume_idx].replace(',', '')
                    volume = int(volume_str) // 1000  # Convert shares to lots (張)
                    
                    results.append({
                        'date': formatted_date,
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'volume': volume
                    })
                    
                except (ValueError, IndexError) as e:
                    # Skip rows with invalid data
                    continue
            
            return results
            
        except Exception as e:
            print(f"Error fetching monthly data for {stock_id} ({year}-{month:02d}): {e}")
            return []
    
    def fetch_stock_info(self, stock_id: str) -> Dict:
        """
        Fetch stock information from TWSE
        
        Note: TWSE doesn't provide a simple stock info API,
        so we'll try to get it from the stock list or use a fallback.
        """
        try:
            # Try to get from stock list
            url = f"{self.base_url}/exchangeReport/MI_INDEX"
            params = {
                'response': 'json',
                'date': datetime.now().strftime('%Y%m%d'),
                'type': 'ALLBUT0999'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Search for stock in the data
                if 'data9' in data:
                    for item in data['data9']:
                        if item[0] == stock_id:
                            return {
                                'stock_id': stock_id,
                                'stock_name': item[1]
                            }
            
            # Fallback: return stock_id as name
            return {
                'stock_id': stock_id,
                'stock_name': stock_id
            }
            
        except Exception as e:
            print(f"Error fetching stock info for {stock_id}: {e}")
            return {
                'stock_id': stock_id,
                'stock_name': stock_id
            }


class FinMindProvider(StockDataProvider):
    """FinMind data provider"""
    
    def __init__(self):
        self.base_url = "https://api.finmindtrade.com/api/v4/data"
        self.token = os.getenv("FINMIND_API_TOKEN")
        
    def fetch_stock_price(self, stock_id: str, start_date: str, end_date: str) -> List[Dict]:
        """Fetch stock price from FinMind API"""
        try:
            params = {
                "dataset": "TaiwanStockPrice",
                "data_id": stock_id,
                "start_date": start_date,
                "end_date": end_date
            }
            
            if self.token:
                params["token"] = self.token
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            
            if data.get("msg") != "success":
                return []
            
            # Convert FinMind format to standard format
            results = []
            for item in data.get("data", []):
                results.append({
                    'date': item['date'],
                    'open': float(item['open']),
                    'high': float(item['max']),
                    'low': float(item['min']),
                    'close': float(item['close']),
                    'volume': int(item['Trading_Volume'])
                })
            
            return results
            
        except Exception as e:
            print(f"FinMind API Error: {e}")
            return []
    
    def fetch_stock_info(self, stock_id: str) -> Dict:
        """Fetch stock information from FinMind"""
        try:
            params = {
                "dataset": "TaiwanStockInfo",
                "data_id": stock_id
            }
            
            if self.token:
                params["token"] = self.token
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code != 200:
                return {'stock_id': stock_id, 'stock_name': stock_id}
            
            data = response.json()
            
            if data.get("msg") == "success" and len(data.get("data", [])) > 0:
                info = data["data"][0]
                return {
                    'stock_id': stock_id,
                    'stock_name': info.get('stock_name', stock_id)
                }
            
            return {'stock_id': stock_id, 'stock_name': stock_id}
            
        except Exception as e:
            print(f"Error fetching stock info: {e}")
            return {'stock_id': stock_id, 'stock_name': stock_id}


class StockDataFacade:
    """
    Facade for accessing stock data from multiple providers
    
    This class provides a unified interface for fetching stock data,
    abstracting away the complexity of different data sources.
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize the facade with a specific provider
        
        Args:
            provider: 'twse' or 'finmind'. If None, uses STOCK_DATA_PROVIDER env var,
                     defaulting to 'twse'
        """
        if provider is None:
            provider = os.getenv('STOCK_DATA_PROVIDER', 'twse').lower()
        
        self.provider = provider
        self._provider_instance = self._create_provider(provider)
    
    def _create_provider(self, provider: str) -> StockDataProvider:
        """Factory method to create provider instances"""
        if provider == 'twse':
            return TWSEProvider()
        elif provider == 'finmind':
            return FinMindProvider()
        else:
            raise ValueError(f"Unknown provider: {provider}. Must be 'twse' or 'finmind'")
    
    def set_provider(self, provider: str):
        """
        Switch to a different provider
        
        Args:
            provider: 'twse' or 'finmind'
        """
        self.provider = provider
        self._provider_instance = self._create_provider(provider)
    
    def get_stock_price(self, stock_id: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Get stock price data
        
        Args:
            stock_id: Stock ticker code
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            List of price data dictionaries
        """
        return self._provider_instance.fetch_stock_price(stock_id, start_date, end_date)
    
    def get_stock_info(self, stock_id: str) -> Dict:
        """
        Get stock information
        
        Args:
            stock_id: Stock ticker code
            
        Returns:
            Dictionary with stock information
        """
        return self._provider_instance.fetch_stock_info(stock_id)
    
    def get_provider_name(self) -> str:
        """Get current provider name"""
        return self.provider


# Convenience function for backward compatibility
def get_stock_data_facade(provider: Optional[str] = None) -> StockDataFacade:
    """
    Factory function to create a StockDataFacade instance
    
    Args:
        provider: Optional provider name ('twse' or 'finmind')
        
    Returns:
        StockDataFacade instance
    """
    return StockDataFacade(provider=provider)
