import requests
from lxml import etree
import json
import os
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("frontend/public/data")

def fetch_taifex_market_cap_rank():
    """
    Fetches market cap ranking from TAIFEX.
    Returns a dictionary: { stock_code: rank_int }
    """
    url = "https://www.taifex.com.tw/cht/9/futuresQADetail"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print(f"Fetching Market Cap Rank from {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse HTML
        parser = etree.HTMLParser()
        tree = etree.fromstring(response.content, parser)
        
        # Select all rows in the table
        rows = tree.xpath('//table[@class="table_c"]//tr')
        
        rank_map = {}
        
        for row in rows:
            # Skip header row (thead usually, or check content)
            cols = row.xpath('./td')
            if not cols:
                continue
                
            # Extract Column A (Left side)
            if len(cols) >= 4:
                try:
                    rank_a = cols[0].text.strip()
                    code_a = cols[1].text.strip()
                    if rank_a.isdigit() and code_a:
                        rank_map[code_a] = int(rank_a)
                except:
                    pass

            # Extract Column B (Right side)
            if len(cols) >= 8:
                try:
                    rank_b = cols[4].text.strip()
                    code_b = cols[5].text.strip()
                    if rank_b.isdigit() and code_b:
                        rank_map[code_b] = int(rank_b)
                except:
                    pass
                    
        print(f"✅ Successfully fetched {len(rank_map)} stocks ranking.")
        return rank_map

    except Exception as e:
        print(f"❌ Failed to fetch market cap rank: {e}")
        return {}

def save_rank_to_json(rank_map):
    """Saves the rank map to a JSON file"""
    if not rank_map:
        print("⚠️ Empty rank map, skipping save.")
        return False
        
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "market_cap_rank.json"
    
    data = {
        "updatedAt": datetime.now().isoformat(),
        "source": "TAIFEX",
        "ranks": rank_map
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved ranking to {output_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to save ranking JSON: {e}")
        return False

if __name__ == "__main__":
    ranks = fetch_taifex_market_cap_rank()
    if ranks:
        save_rank_to_json(ranks)
        
        # Verify Top 10
        sorted_ranks = sorted(ranks.items(), key=lambda x: x[1])
        print("\nTop 10 Market Cap Stocks:")
        for code, rank in sorted_ranks[:10]:
            print(f"#{rank}: {code}")

