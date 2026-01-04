"""
Portfolio Manager Module - 持股管理與異動偵測
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import streamlit as st

# Portfolio directory
PORTFOLIO_DIR = Path("data/portfolios")


def ensure_portfolio_dir():
    """確保存檔目錄存在"""
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)


def get_portfolio_path(date: str) -> Path:
    """取得指定日期的持股檔案路徑"""
    return PORTFOLIO_DIR / f"{date}_portfolio.json"


def load_portfolio(date: Optional[str] = None) -> dict:
    """
    載入指定日期持股
    
    Args:
        date: 日期字串 (YYYY-MM-DD)，預設為今日
    
    Returns:
        Portfolio dict with stocks and metadata
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    file_path = get_portfolio_path(date)
    
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return {"date": date, "stocks": {}, "total_value": 0, "total_cost": 0}


def save_portfolio(portfolio: dict, date: Optional[str] = None):
    """
    儲存持股資料
    
    Args:
        portfolio: 持股資料
        date: 日期字串，預設為今日
    """
    ensure_portfolio_dir()
    
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    portfolio["date"] = date
    portfolio["updated_at"] = datetime.now().isoformat()
    
    file_path = get_portfolio_path(date)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)


def get_yesterday_date() -> str:
    """取得前一個交易日日期（簡化處理，實際應考慮假日）"""
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    # Skip weekends
    while yesterday.weekday() >= 5:
        yesterday -= timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def detect_changes(today_portfolio: dict, yesterday_portfolio: dict) -> dict:
    """
    偵測持股異動
    
    Args:
        today_portfolio: 今日持股
        yesterday_portfolio: 昨日持股
    
    Returns:
        dict with new_entries, exits, and holdings
    """
    today_stocks = set(today_portfolio.get("stocks", {}).keys())
    yesterday_stocks = set(yesterday_portfolio.get("stocks", {}).keys())
    
    new_entries = today_stocks - yesterday_stocks  # 新進場
    exits = yesterday_stocks - today_stocks         # 已離場
    holdings = today_stocks & yesterday_stocks      # 續抱
    
    result = {
        "new_entries": [],
        "exits": [],
        "holdings": []
    }
    
    # 新進場詳情
    for symbol in new_entries:
        stock_data = today_portfolio["stocks"][symbol]
        result["new_entries"].append({
            "symbol": symbol,
            "name": stock_data.get("name", symbol),
            "cost": stock_data.get("cost", 0),
            "shares": stock_data.get("shares", 0),
        })
    
    # 已離場詳情
    for symbol in exits:
        stock_data = yesterday_portfolio["stocks"][symbol]
        result["exits"].append({
            "symbol": symbol,
            "name": stock_data.get("name", symbol),
            "cost": stock_data.get("cost", 0),
            "shares": stock_data.get("shares", 0),
            "exit_note": stock_data.get("exit_note", ""),
        })
    
    # 續抱詳情
    for symbol in holdings:
        stock_data = today_portfolio["stocks"][symbol]
        result["holdings"].append({
            "symbol": symbol,
            "name": stock_data.get("name", symbol),
            "cost": stock_data.get("cost", 0),
            "shares": stock_data.get("shares", 0),
        })
    
    return result


def add_stock_to_portfolio(symbol: str, name: str, cost: float, shares: int) -> dict:
    """
    新增股票到今日持股
    
    Args:
        symbol: 股票代碼
        name: 股票名稱
        cost: 成本價
        shares: 股數（張數 * 1000）
    
    Returns:
        Updated portfolio
    """
    portfolio = load_portfolio()
    
    portfolio["stocks"][symbol] = {
        "name": name,
        "cost": cost,
        "shares": shares,
        "added_at": datetime.now().isoformat()
    }
    
    save_portfolio(portfolio)
    return portfolio


def remove_stock_from_portfolio(symbol: str, exit_price: Optional[float] = None) -> dict:
    """
    從今日持股移除股票
    
    Args:
        symbol: 股票代碼
        exit_price: 賣出價格
    
    Returns:
        Updated portfolio
    """
    portfolio = load_portfolio()
    
    if symbol in portfolio["stocks"]:
        del portfolio["stocks"][symbol]
    
    save_portfolio(portfolio)
    return portfolio


def calculate_portfolio_value(portfolio: dict, prices: dict) -> dict:
    """
    計算投資組合市值與損益
    
    Args:
        portfolio: 持股資料
        prices: 各股票現價 {symbol: price}
    
    Returns:
        dict with total_value, total_cost, total_pnl, total_pnl_pct
    """
    total_value = 0
    total_cost = 0
    
    stocks = portfolio.get("stocks", {})
    
    for symbol, stock in stocks.items():
        shares = stock.get("shares", 0)
        cost = stock.get("cost", 0)
        current_price = prices.get(symbol, cost)
        
        stock_value = current_price * shares
        stock_cost = cost * shares
        
        total_value += stock_value
        total_cost += stock_cost
    
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    
    return {
        "total_value": total_value,
        "total_cost": total_cost,
        "total_pnl": total_pnl,
        "total_pnl_pct": total_pnl_pct,
        "stock_count": len(stocks)
    }
