#!/usr/bin/env python3
"""
Stock Data Facade 使用範例

這個範例展示如何使用 Facade Pattern 來取得股價資料
"""

import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stock_data_facade import StockDataFacade


def example_basic_usage():
    """範例 1: 基本使用"""
    print("=" * 60)
    print("範例 1: 基本使用 (預設 TWSE Provider)")
    print("=" * 60)
    
    # 建立 Facade (預設使用 TWSE)
    facade = StockDataFacade()
    
    # 設定日期範圍
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # 取得台積電股價
    print(f"\n📊 取得台積電 (2330) 近 30 日股價...")
    data = facade.get_stock_price('2330', start_date, end_date)
    
    if data:
        print(f"✅ 成功取得 {len(data)} 筆資料")
        print(f"\n最新資料 ({data[-1]['date']}):")
        print(f"  開盤: {data[-1]['open']}")
        print(f"  最高: {data[-1]['high']}")
        print(f"  最低: {data[-1]['low']}")
        print(f"  收盤: {data[-1]['close']}")
        print(f"  成交量: {data[-1]['volume']:,} 張")
    else:
        print("❌ 無法取得資料")
    
    # 取得股票資訊
    print(f"\n📋 取得股票資訊...")
    info = facade.get_stock_info('2330')
    print(f"  代號: {info['stock_id']}")
    print(f"  名稱: {info['stock_name']}")


def example_switch_provider():
    """範例 2: 切換資料源"""
    print("\n" + "=" * 60)
    print("範例 2: 動態切換資料源")
    print("=" * 60)
    
    facade = StockDataFacade()
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # 使用 TWSE
    print(f"\n🔵 使用 {facade.get_provider_name().upper()} Provider...")
    data_twse = facade.get_stock_price('2330', start_date, end_date)
    print(f"取得 {len(data_twse)} 筆資料")
    
    # 切換到 FinMind
    print(f"\n🟢 切換到 FinMind Provider...")
    facade.set_provider('finmind')
    data_finmind = facade.get_stock_price('2330', start_date, end_date)
    print(f"取得 {len(data_finmind)} 筆資料")
    
    # 比較資料
    if len(data_twse) > 0 and len(data_finmind) > 0:
        print(f"\n📊 資料比較 (最新日期):")
        print(f"  TWSE:    收盤 {data_twse[-1]['close']}, 成交量 {data_twse[-1]['volume']:,} 張")
        print(f"  FinMind: 收盤 {data_finmind[-1]['close']}, 成交量 {data_finmind[-1]['volume']:,} 張")


def example_env_config():
    """範例 3: 使用環境變數配置"""
    print("\n" + "=" * 60)
    print("範例 3: 使用環境變數配置")
    print("=" * 60)
    
    # 模擬設定環境變數
    original_provider = os.environ.get('STOCK_DATA_PROVIDER')
    
    # 測試 TWSE
    os.environ['STOCK_DATA_PROVIDER'] = 'twse'
    facade1 = StockDataFacade()
    print(f"\n環境變數 STOCK_DATA_PROVIDER=twse")
    print(f"實際使用: {facade1.get_provider_name()}")
    
    # 測試 FinMind
    os.environ['STOCK_DATA_PROVIDER'] = 'finmind'
    facade2 = StockDataFacade()
    print(f"\n環境變數 STOCK_DATA_PROVIDER=finmind")
    print(f"實際使用: {facade2.get_provider_name()}")
    
    # 恢復原始設定
    if original_provider:
        os.environ['STOCK_DATA_PROVIDER'] = original_provider
    else:
        os.environ.pop('STOCK_DATA_PROVIDER', None)


def example_error_handling():
    """範例 4: 錯誤處理"""
    print("\n" + "=" * 60)
    print("範例 4: 錯誤處理")
    print("=" * 60)
    
    facade = StockDataFacade()
    
    # 測試無效股票代碼
    print(f"\n⚠️  測試無效股票代碼...")
    data = facade.get_stock_price('INVALID', '2024-01-01', '2024-01-31')
    print(f"結果: 返回 {len(data)} 筆資料 (正確處理錯誤)")
    
    # 測試無效 Provider
    print(f"\n⚠️  測試無效 Provider...")
    try:
        invalid_facade = StockDataFacade(provider='invalid')
        print("❌ 未正確拋出錯誤")
    except ValueError as e:
        print(f"✅ 正確拋出 ValueError: {e}")


def example_multiple_stocks():
    """範例 5: 批次查詢多檔股票"""
    print("\n" + "=" * 60)
    print("範例 5: 批次查詢多檔股票")
    print("=" * 60)
    
    facade = StockDataFacade()
    
    stocks = ['2330', '2317', '2454']  # 台積電、鴻海、聯發科
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    print(f"\n📊 查詢多檔股票近 7 日收盤價...")
    
    for stock_id in stocks:
        info = facade.get_stock_info(stock_id)
        data = facade.get_stock_price(stock_id, start_date, end_date)
        
        if data:
            latest = data[-1]
            prev = data[-2] if len(data) > 1 else data[-1]
            change = ((latest['close'] - prev['close']) / prev['close']) * 100
            
            print(f"\n{stock_id} {info['stock_name']:8s}")
            print(f"  收盤: {latest['close']:8.2f}  漲跌: {change:+6.2f}%")
        else:
            print(f"\n{stock_id} - 無法取得資料")


def main():
    """執行所有範例"""
    print("\n" + "🚀" * 30)
    print("Stock Data Facade 使用範例集")
    print("🚀" * 30)
    
    try:
        example_basic_usage()
        example_switch_provider()
        example_env_config()
        example_error_handling()
        example_multiple_stocks()
        
        print("\n" + "=" * 60)
        print("✅ 所有範例執行完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
