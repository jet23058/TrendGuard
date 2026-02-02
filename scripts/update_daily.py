#!/usr/bin/env python3
"""
利弗摩爾強勢突破掃描器
每日 14:30 執行，篩選符合條件的強勢股

篩選條件：
1. 股價站上所有均線 (MA5, MA10, MA20, MA60)
2. 連續兩日紅 K (收盤 > 開盤)
3. 收盤價突破近 N 日新高
4. (修正) 警示/處置股也必須符合上述技術條件才能入選
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# FinMind API for Taiwan stock data (more reliable than yfinance)
from FinMind.data import DataLoader

# Initialize FinMind DataLoader (singleton)
_finmind_loader = None

def get_finmind_loader():
    """Get or create FinMind DataLoader singleton"""
    global _finmind_loader
    if _finmind_loader is None:
        _finmind_loader = DataLoader()
        token = os.environ.get("FINMIND_API_TOKEN")
        if token:
            _finmind_loader.login_by_token(api_token=token)
            print("✅ FinMind logged in with token")
    return _finmind_loader

try:
    import twstock
    # 強制更新股票代碼表，確保擁有最新上市櫃清單
    # twstock.__update_codes() # 注意: 這可能需要下載，若 CI 環境受限可能失敗，視情況啟用
    HAS_TWSTOCK = True
except ImportError:
    HAS_TWSTOCK = False
    print("Warning: twstock not installed, using FinMind for stock names")

import re
import requests
from datetime import timedelta

def roc_to_date(roc_str):
    """Convert ROC date string (e.g., '114/01/05') to datetime object"""
    try:
        parts = roc_str.split('/')
        year = int(parts[0]) + 1911
        return datetime(year, int(parts[1]), int(parts[2]))
    except:
        return None

def fetch_market_alerts():
    """Fetch TWSE/TPEx Warning and Disposition data with Risk Analysis"""
    alerts = {}
    history_db = {} # {code: [dates]}
    
    today = datetime.now()
    today_str = today.strftime('%Y%m%d')
    # Look back 40 days to ensure we have enough trading days for the 30-day rule
    start_str = (today - timedelta(days=40)).strftime('%Y%m%d') 
    
    # 1. Fetch TWSE Warning History (Notice)
    try:
        url = "https://www.twse.com.tw/rwd/zh/announcement/notice"
        params = {'response': 'json', 'startDate': start_str, 'endDate': today_str}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        
        if 'data' in data:
            for item in data['data']:
                code = item[1]
                date_roc = item[5] # e.g. "114/01/30"
                reason = item[4]
                
                if code not in history_db:
                    history_db[code] = []
                history_db[code].append(date_roc)
                
                # If it's today's alert, initialize the alert object
                alert_dt = roc_to_date(date_roc)
                if alert_dt and (today - alert_dt).days <= 1:
                    alerts[code] = {
                        "type": "warning",
                        "badge": "警示",
                        "color": "yellow",
                        "info": "注意股",
                        "detail": reason,
                        "history": []
                    }
    except Exception as e:
        print(f"Error fetching TWSE notice: {e}")

    # 2. Fetch TWSE Disposition (Punish)
    try:
        url = "https://www.twse.com.tw/rwd/zh/announcement/punish"
        params = {'response': 'json', 'startDate': start_str, 'endDate': today_str}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        
        if 'data' in data:
            for item in data['data']:
                code = item[2]
                period_str = item[6] 
                content = item[8]
                
                if '～' in period_str:
                    start_roc, end_roc = period_str.split('～')
                    start_dt = roc_to_date(start_roc)
                    end_dt = roc_to_date(end_roc)
                    
                    if start_dt and end_dt and start_dt <= today + timedelta(days=1) and today <= end_dt + timedelta(days=1): 
                        freq = "處置"
                        match = re.search(r'每(\S+)分鐘', content)
                        if match:
                            freq = f"{match.group(1)}分盤"
                        elif "人工管制" in content:
                            freq = "人工管制"
                            
                        alerts[code] = {
                            "type": "disposition",
                            "badge": "處置",
                            "color": "red",
                            "info": f"{freq} (至 {end_roc})",
                            "detail": f"期間: {period_str}\n措施: {item[7]}",
                            "is_disposed": True
                        }
    except Exception as e:
        print(f"Error fetching TWSE punish: {e}")

    # 3. Fetch TPEX (OTC) Alerts
    try:
        base_url = "https://www.tpex.org.tw/openapi/v1"
        
        # 3.1 TPEX Warning History
        r = requests.get(f"{base_url}/tpex_trading_warning_information", timeout=10)
        if r.status_code == 200:
            for item in r.json():
                code = item.get('SecuritiesCompanyCode')
                date_roc = item.get('Date') # Compact "1140130"
                reason = item.get('TradingInformation', '')
                
                # Convert to slash format for consistency
                if len(date_roc) == 7:
                    fmt_date = f"{date_roc[:3]}/{date_roc[3:5]}/{date_roc[5:]}"
                else:
                    fmt_date = date_roc
                    
                if code not in history_db:
                    history_db[code] = []
                history_db[code].append(fmt_date)
                
                # Check if recent
                alert_dt = None
                if len(date_roc) == 7:
                    alert_dt = datetime(int(date_roc[:3]) + 1911, int(date_roc[3:5]), int(date_roc[5:]))
                
                if alert_dt and (today - alert_dt).days <= 1:
                    if code not in alerts:
                        alerts[code] = {
                            "type": "warning",
                            "badge": "警示",
                            "color": "yellow",
                            "info": "注意股",
                            "detail": reason,
                            "history": []
                        }

        # 3.2 TPEX Disposition
        r = requests.get(f"{base_url}/tpex_disposal_information", timeout=10)
        if r.status_code == 200:
            for item in r.json():
                code = item.get('SecuritiesCompanyCode')
                period_str = item.get('DispositionPeriod', '')
                content = item.get('DisposalCondition', '')
                
                if '~' in period_str:
                    try:
                        start_roc, end_roc = period_str.split('~')
                        def parse_roc_compact(d_str):
                            if len(d_str) == 7:
                                return datetime(int(d_str[:3]) + 1911, int(d_str[3:5]), int(d_str[5:]))
                            return roc_to_date(d_str)
                            
                        start_dt = parse_roc_compact(start_roc)
                        end_dt = parse_roc_compact(end_roc)
                        
                        if start_dt and end_dt and start_dt <= today + timedelta(days=1) and today <= end_dt + timedelta(days=1):
                            freq = "處置"
                            match = re.search(r'每(\S+)分鐘', content)
                            if match:
                                freq = f"{match.group(1)}分盤"
                            elif "人工管制" in content:
                                freq = "人工管制"
                                
                            alerts[code] = {
                                "type": "disposition",
                                "badge": "處置",
                                "color": "red",
                                "info": f"{freq} (至 {end_roc})",
                                "detail": f"期間: {period_str}\n措施: {content}",
                                "is_disposed": True
                            }
                    except: pass
    except Exception as e:
        print(f"Error fetching TPEX alerts: {e}")

    # 4. Risk Analysis (Calculating Disposition Proximity)
    for code, alert_obj in alerts.items():
        if alert_obj.get('type') == 'disposition':
            continue # Already disposed
            
        hist = sorted(list(set(history_db.get(code, []))), reverse=True)
        alert_obj['history'] = hist
        
        # Calculate Risk Metrics
        # Rule 1: 3 consecutive days
        consecutive = 0
        # This is tricky because we need trading days. 
        # For simplicity, we count consecutive entries in the sorted history.
        consecutive = 1
        # Check if previous days were also in history
        # (Need a calendar or just check if dates are close)
        # For now, let's just use the count in recent window.
        
        count_30 = len(hist)
        count_6 = 0
        # Approx count in last 6 trading days (approx 10 calendar days)
        cutoff_6 = today - timedelta(days=10)
        for d_str in hist:
            d_dt = roc_to_date(d_str)
            if d_dt and d_dt >= cutoff_6:
                count_6 += 1
        
        # Determine Risk Level
        risk_level = "low"
        risk_msg = ""
        
        if count_6 >= 3:
            risk_level = "high"
            risk_msg = f"觸發 4/6 處置風險 (目前 {count_6}/6)"
        elif count_6 >= 2:
            risk_level = "medium"
            risk_msg = f"近期注意次數增加 ({count_6}/6)"
            
        if count_30 >= 10:
            risk_level = "high"
            risk_msg = f"觸發 12/30 處置風險 (目前 {count_30}/30)"
            
        alert_obj['risk'] = {
            "level": risk_level,
            "message": risk_msg,
            "count_6": count_6,
            "count_30": count_30
        }

    return alerts

def fetch_allowed_day_trade_targets():
    """取得所有可現股當沖的股票代碼 (上市+上櫃)"""
    allowed = set()
    
    # 1. TWSE (上市)
    try:
        # TWTB4U: 當日沖銷交易標的及成交量值
        # 若不帶日期，預設回傳最近交易日
        url = "https://www.twse.com.tw/exchangeReport/TWTB4U?response=json"
        r = requests.get(url, timeout=10)
        data = r.json()
        if 'tables' in data:
            for t in data['tables']:
                # 尋找包含標的清單的表格 (通常是第二個，欄位含'證券代號')
                if 'fields' in t and '證券代號' in t['fields']:
                    if len(t.get('data', [])) > 100: # 簡單檢核資料量
                        for row in t['data']:
                            allowed.add(row[0]) # 代號
                        print(f"已取得上市當沖標的: {len(t['data'])} 檔")
    except Exception as e:
        print(f"Error fetching TWSE day trade list: {e}")

    # 2. TPEX (上櫃)
    try:
        # TPEX 需要指定日期，嘗試回推最近 5 天直到抓到資料
        found = False
        base_date = datetime.now()
        
        for i in range(5):
            d = base_date - timedelta(days=i)
            roc_year = d.year - 1911
            date_str = f"{roc_year}/{d.month:02d}/{d.day:02d}"
            
            url = f"https://www.tpex.org.tw/web/stock/trading/intraday_stat/intraday_trading_stat_result.php?l=zh-tw&o=json&d={date_str}"
            try:
                r = requests.get(url, timeout=5)
                data = r.json()
                if 'tables' in data:
                    for t in data['tables']:
                         if 'fields' in t and '證券代號' in t['fields']:
                            count = len(t.get('data', []))
                            if count > 50: # 簡單檢核
                                for row in t['data']:
                                    allowed.add(row[0])
                                print(f"已取得上櫃當沖標的 ({date_str}): {count} 檔")
                                found = True
                                break
                    if found: break
            except:
                continue
                
    except Exception as e:
        print(f"Error fetching TPEX day trade list: {e}")
        
    print(f"總計可當沖標的: {len(allowed)} 檔")
    return allowed

import concurrent.futures
import time
import threading

# --- 設定 ---
LOOKBACK_DAYS = 20  # 突破幾日新高
TEST_MODE = os.environ.get('TEST_MODE', 'true').lower() == 'true'  # GitHub Actions 設為 false
OUTPUT_DIR = Path("frontend/public/data")
MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 5)) # Parallel workers

# ... (TEST_STOCKS list remains same) ...

# ... (Helper functions remain same) ...

def process_single_stock(code, market_alerts, allowed_day_trade_targets):
    """Worker function for parallel processing"""
    try:
        # Small delay to prevent burst rate limit
        time.sleep(0.1) 
        data, change_pct = check_livermore_criteria(code, market_alerts, allowed_day_trade_targets)
        return code, data, change_pct
    except Exception as e:
        print(f"Error processing {code}: {e}")
        return code, None, None

def main():
    """主程式"""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--update-alerts', action='store_true', help='Update existing alerts only')
    parser.add_argument('--generate-article-only', action='store_true', help='Generate article from existing data only')
    args = parser.parse_args()

    # ... (Alerts update logic remains same) ...
    if args.update_alerts:
        data = update_existing_alerts()
        try:
            print("正在更新盤勢分析文章 (含警示資訊)...")
            article = generate_daily_article(data)
            save_to_json(article)
            print("✅ 已更新每日分析文章並儲存")
        except Exception as e:
            print(f"⚠️ 文章更新失敗: {e}")
        return

    # ... (Generate article logic remains same) ...
    if args.generate_article_only:
        # ... (implementation same as before) ...
        print("🚀 Manual Trigger: Generating Article Only")
        output_file = OUTPUT_DIR / "daily_scan_results.json"
        if not output_file.exists():
            print(f"❌ Error: {output_file} not found. Cannot generate article.")
            sys.exit(1)
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            article = generate_daily_article(data)
            if save_to_json(article):
                print("✅ Manual article generation and save completed successfully.")
            else:
                print("⚠️ Article generated but NOT saved (check errors above).")
                sys.exit(1)
            return
        except Exception as e:
            print(f"❌ Failed to generate article: {e}")
            sys.exit(1)

    print(f"\n=== 利弗摩爾強勢突破掃描 ===")
    print(f"掃描時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"突破天數: {LOOKBACK_DAYS} 日\n")
    
    # 確保目錄存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "daily_scan_results.json"
    
    # 讀取舊資料 (用於計算差異)
    previous_data = None
    if output_file.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                previous_data = json.load(f)
        except Exception as e:
            print(f"無法讀取舊資料: {e}")

    # 取得股票清單
    target_list = get_all_tw_targets()
    total = len(target_list)
    
    # 警告：無 Token 時掃描大量股票風險
    token = os.environ.get("FINMIND_API_TOKEN")
    if not token and total > 600:
        print(f"⚠️ 警告: 未設定 FINMIND_API_TOKEN，掃描 {total} 檔股票可能會觸發 API 限制 (600次/hr)。")
        print("   建議設定 Token 以獲得 3000次/hr 額度，或僅使用測試模式。")
    
    # 取得市場警示 (處置/注意)
    market_alerts = fetch_market_alerts()
    print(f"取得市場警示資料: {len(market_alerts)} 筆")
    
    # 取得可當沖標的清單
    allowed_day_trade_targets = fetch_allowed_day_trade_targets()
    
    results = []
    
    # 市場寬度統計 (Market Breadth)
    market_stats = {
        "up": 0,
        "down": 0,
        "flat": 0,
        "total_scanned": 0
    }
    
    print(f"🚀 開始平行掃描 (Workers: {MAX_WORKERS})...")
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit tasks
        futures = {executor.submit(process_single_stock, code, market_alerts, allowed_day_trade_targets): code for code in target_list}
        
        completed_count = 0
        for future in concurrent.futures.as_completed(futures):
            code = futures[future]
            try:
                _, data, change_pct = future.result()
                
                completed_count += 1
                if completed_count % 10 == 0:
                    print(f"\r進度: {completed_count}/{total} ({(completed_count/total)*100:.1f}%)", end="", flush=True)
                
                # 統計市場漲跌
                if change_pct is not None:
                    market_stats["total_scanned"] += 1
                    if change_pct > 0:
                        market_stats["up"] += 1
                    elif change_pct < 0:
                        market_stats["down"] += 1
                    else:
                        market_stats["flat"] += 1
                        
                if data:
                    results.append(data)
                    
            except Exception as exc:
                print(f"\nError processing {code}: {exc}")

    elapsed = time.time() - start_time
    print(f"\n\n掃描完成！耗時: {elapsed:.2f} 秒")
    print(f"市場統計: 上漲 {market_stats['up']} / 下跌 {market_stats['down']} / 平盤 {market_stats['flat']}")
    print(f"符合條件: {len(results)} 檔\n")
    
    # 按連紅天數排序 (越多越強)
    results.sort(key=lambda x: x['signal']['priority'], reverse=True)
    
    # 計算差異
    changes = calculate_changes(previous_data, results)

    # 輸出結果
    if results:
        print("=" * 60)
        print(f"{'代號':<8} {'名稱':<10} {'現價':>8} {'連紅':>4} {'狀態':<6}")
        print("=" * 60)
        
        # 建立快速查找 map
        new_tickers = {s['ticker'] for s in changes['new']}
        
        for r in results:
            status = "✨新進" if r['ticker'] in new_tickers else "⟳續漲"
            print(f"{r['ticker']:<8} {r['name']:<10} {r['currentPrice']:>8.2f} {r['consecutiveRed']:>4} {status:<6}")

    current_iso = datetime.now().isoformat()
    
    # 準備 JSON 輸出
    output = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "updatedAt": current_iso,
        "quoteTime": current_iso, 
        "alertUpdateTime": current_iso,
        "scanType": "livermore_breakout",
        "criteria": {
            "lookbackDays": LOOKBACK_DAYS,
            "description": f"突破 {LOOKBACK_DAYS} 日新高 + 站上所有均線 + 連續2日紅K"
        },
        "stocks": results,
        "marketStats": market_stats, # 新增市場統計欄位
        "summary": {
            "total": len(results),
            "buySignals": len(results),
            "counts": {
                "new": len(changes['new']),
                "continued": len(changes['continued']),
                "removed": len(changes['removed'])
            }
        },
        "changes": changes
    }
    
    # 寫入 JSON
    output_file = OUTPUT_DIR / "daily_scan_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # [NEW] Save History JSON for Article Page
    history_dir = OUTPUT_DIR / "history"
    history_dir.mkdir(exist_ok=True)
    history_file = history_dir / f"{output['date']}.json"
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"✅ History saved to {history_file}")
    
    print(f"\n✅ 已輸出至 {output_file}")

    # -----------------------------------------------
    # Auto Generate Article
    # -----------------------------------------------
    try:
        print("正在產生盤勢分析文章...")
        article = generate_daily_article(output)
        save_to_json(article)
        print("✅ 已產生每日分析文章並儲存")
    except Exception as e:
        print(f"⚠️ 文章產生失敗 (不影響主流程): {e}")
    
    return output



def generate_articles_index():
    """Appends new articles to the existing index JSON file."""
    articles_dir = OUTPUT_DIR / "articles"
    index_file = OUTPUT_DIR / "articles_index.json"
    
    if not articles_dir.exists():
        print("⚠️ No articles directory found.")
        return

    # 1. Try to load existing index from data branch (GitHub)
    existing_index = []
    try:
        import urllib.request
        url = "https://raw.githubusercontent.com/jet23058/TrendGuard/data/articles_index.json"
        with urllib.request.urlopen(url, timeout=10) as response:
            existing_index = json.loads(response.read().decode('utf-8'))
            print(f"📥 Loaded existing index with {len(existing_index)} articles")
    except Exception as e:
        print(f"⚠️ Could not fetch existing index (will create new): {e}")
    
    # 2. Build a set of existing dates for deduplication
    existing_dates = {item['date'] for item in existing_index}
    
    # 3. Scan local articles directory for new articles
    new_articles = []
    for file_path in sorted(articles_dir.glob("*.json"), reverse=True):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                article_date = data.get("date", file_path.stem)
                
                # Skip if already in index
                if article_date in existing_dates:
                    continue
                    
                summary_data = {
                    "date": article_date,
                    "title": data.get("title", "無標題"),
                    "isAiGenerated": data.get("isAiGenerated", False),
                    "preview": data.get("content", "")[:100].replace('#', '').strip() + "..." 
                }
                new_articles.append(summary_data)
                print(f"➕ Adding new article: {article_date}")
        except Exception as e:
            print(f"⚠️ Failed to read article {file_path.name}: {e}")

    # 4. Merge and sort (newest first)
    merged_index = new_articles + existing_index
    merged_index.sort(key=lambda x: x['date'], reverse=True)
    
    # 5. Write updated index file
    try:
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(merged_index, f, ensure_ascii=False, indent=2)
        print(f"✅ Articles index updated: {index_file} ({len(merged_index)} total articles)")
    except Exception as e:
        print(f"❌ Failed to write articles index: {e}")


if __name__ == "__main__":
    main()
    # Always regenerate index after main process
    generate_articles_index()

