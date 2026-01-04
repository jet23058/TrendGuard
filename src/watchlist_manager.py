"""
Watchlist Manager Module - 每日觀察清單管理
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
import streamlit as st

# Watchlist directory
WATCHLIST_DIR = Path("data/watchlists")


def ensure_watchlist_dir():
    """確保存檔目錄存在"""
    WATCHLIST_DIR.mkdir(parents=True, exist_ok=True)


def get_watchlist_path(date: str) -> Path:
    """取得指定日期的觀察清單檔案路徑"""
    return WATCHLIST_DIR / f"{date}_watchlist.json"


def load_watchlist(date: Optional[str] = None) -> dict:
    """
    載入指定日期觀察清單
    
    Args:
        date: 日期字串 (YYYY-MM-DD)，預設為今日
    
    Returns:
        Watchlist dict with stocks
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    file_path = get_watchlist_path(date)
    
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return {"date": date, "stocks": []}


def save_watchlist(stocks: List[str], date: Optional[str] = None):
    """
    儲存觀察清單
    
    Args:
        stocks: 股票代碼列表
        date: 日期字串，預設為今日
    """
    ensure_watchlist_dir()
    
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    watchlist = {
        "date": date,
        "stocks": stocks,
        "updated_at": datetime.now().isoformat()
    }
    
    file_path = get_watchlist_path(date)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(watchlist, f, ensure_ascii=False, indent=2)


def get_previous_trading_date() -> str:
    """取得前一個交易日日期"""
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    # Skip weekends
    while yesterday.weekday() >= 5:
        yesterday -= timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def detect_watchlist_changes(today_stocks: List[str], yesterday_stocks: List[str]) -> dict:
    """
    偵測觀察清單異動
    
    Args:
        today_stocks: 今日股票列表
        yesterday_stocks: 昨日股票列表
    
    Returns:
        dict with new_entries, exits
    """
    today_set = set(today_stocks)
    yesterday_set = set(yesterday_stocks)
    
    new_entries = list(today_set - yesterday_set)    # 新加入
    exits = list(yesterday_set - today_set)          # 被去除
    holdings = list(today_set & yesterday_set)       # 續留
    
    return {
        "new_entries": new_entries,
        "exits": exits,
        "holdings": holdings
    }


def add_to_watchlist(symbol: str) -> List[str]:
    """新增股票到今日觀察清單"""
    watchlist = load_watchlist()
    stocks = watchlist.get("stocks", [])
    
    if symbol not in stocks:
        stocks.append(symbol)
        save_watchlist(stocks)
    
    return stocks


def remove_from_watchlist(symbol: str) -> List[str]:
    """從今日觀察清單移除股票"""
    watchlist = load_watchlist()
    stocks = watchlist.get("stocks", [])
    
    if symbol in stocks:
        stocks.remove(symbol)
        save_watchlist(stocks)
    
    return stocks


def get_sample_stocks() -> List[str]:
    """取得預設範例股票（熱門台股）"""
    return [
        "2330",  # 台積電
        "2317",  # 鴻海
        "2454",  # 聯發科
        "2308",  # 台達電
        "2881",  # 富邦金
        "2882",  # 國泰金
        "2303",  # 聯電
        "3008",  # 大立光
        "2412",  # 中華電
        "1301",  # 台塑
    ]
