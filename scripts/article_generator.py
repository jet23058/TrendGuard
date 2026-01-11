import os
import json
import argparse
from datetime import datetime
from pathlib import Path

# Setup Output Directory (for reading results)
OUTPUT_DIR = Path("frontend/public/data")



def get_market_summary(scan_results: dict) -> str:
    """產生大盤概要資訊 (Hash summary)"""
    date_str = scan_results.get('date', datetime.now().strftime('%Y-%m-%d'))
    summary = scan_results.get('summary', {})
    total = summary.get('total', 0)
    counts = summary.get('counts', {})
    new_count = counts.get('new', 0)
    continued_count = counts.get('continued', 0)
    removed_count = counts.get('removed', 0)
    
    lookback = scan_results.get('criteria', {}).get('lookbackDays', 20)
    
    text = f"## 📊 大盤與選股概要 ({date_str})\n\n"
    text += f"今日系統透過「利弗摩爾動能策略」掃描全台股，在 {lookback} 日新高突破的條件下，"
    text += f"共篩選出 **{total}** 檔強勢股。\n\n"
    text += f"- ✨ **新進榜**：{new_count} 檔 (今日首度突破)\n"
    text += f"- 📈 **續強榜**：{continued_count} 檔 (持續創高)\n"
    text += f"- 📉 **剔除**：{removed_count} 檔 (轉弱或未達標)\n"
    
    return text

def get_sector_rotation(stocks: list) -> tuple:
    """產生類股輪動分析 (Text + Metadata)"""
    sector_counts = {}
    for s in stocks:
        sec = s.get('sector', '其他')
        sector_counts[sec] = sector_counts.get(sec, 0) + 1
        
    # Sort by count desc
    sorted_sectors = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)
    top_sectors = [s[0] for s in sorted_sectors[:3]]
    
    text = "## 🔄 類股輪動觀察\n\n"
    text += "資金流向顯示，今日動能主要集中在以下族群：\n\n"
    
    for sec, count in sorted_sectors[:5]:
        pct = (count / len(stocks)) * 100
        text += f"- **{sec}**：{count} 檔 ({pct:.1f}%)\n"
        
    if len(sorted_sectors) > 5:
        text += f"- 其他：{sum(s[1] for s in sorted_sectors[5:])} 檔\n"
        
    return text, top_sectors

def get_stock_analysis(scan_results: dict) -> tuple:
    """針對焦點股票產生簡析"""
    stocks = scan_results.get('stocks', [])
    # 優先選擇 Priority 高 (連紅多) 且是新進或前幾名的股票
    # 簡單策略：取前 3 名（通常是連紅天數多） + 2 檔新進（若有）
    
    changes = scan_results.get('changes', {})
    new_tickers = {s['ticker'] for s in changes.get('new', [])}
    
    highlights = []
    
    # helper
    def analyze_stock(stock):
        name = stock.get('name')
        code = stock.get('ticker')
        price = stock.get('currentPrice')
        cons_red = stock.get('consecutiveRed')
        pct = stock.get('changePct')
        val_str = "漲" if pct > 0 else "跌"
        
        # 中性用語
        desc = f"{name} ({code}) 收盤價 {price} 元，單日{val_str}幅 {abs(pct)}%。"
        desc += f"目前已連續 {cons_red} 日收紅K，顯示短期多方動能強勁。"
        
        # 均線狀態
        desc += " 股價位於所有均線之上，呈多頭排列。"
        
        return {
            "ticker": code,
            "name": name,
            "analysis": desc
        }

    # 1. Top 3 by priority (already sorted in update_daily.py usually, but let's trust list order)
    for s in stocks[:3]:
        highlights.append(analyze_stock(s))
        
    # 2. Pick up to 2 new stocks that aren't in top 3
    added_new = 0
    existing_tickers = {h['ticker'] for h in highlights}
    
    for s in stocks:
        if s['ticker'] in new_tickers and s['ticker'] not in existing_tickers:
            highlights.append(analyze_stock(s))
            added_new += 1
            if added_new >= 2:
                break
    
    # Form text
    text = "## 🎯 焦點個股運算結果\n\n"
    for h in highlights:
        text += f"### {h['name']} ({h['ticker']})\n"
        text += f"{h['analysis']}\n\n"
        
    return text, highlights


# Try importing Gemini, handle import error gracefully
try:
    from google import genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

def ask_gemini(prompt: str, model_name=None) -> str:
    """Invokes Gemini API to generate text using new google.genai SDK."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not model_name:
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    if not api_key or not HAS_GEMINI:
        return None
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"⚠️ Gemini API Error: {e}")
        return None

def generate_daily_article(scan_results: dict) -> dict:
    """Generate article data structure, optionally using Gemini."""
    
    # 1. Base Data Preparation
    date_str = scan_results.get('date')
    summary = scan_results.get('summary', {})
    total = summary.get('total', 0)
    
    # Extract top stocks for detailed prompt
    stocks = scan_results.get('stocks', [])
    top_stocks_info = []
    for s in stocks[:5]: # Top 5
        top_stocks_info.append(f"{s['name']}({s['ticker']}): Price {s['currentPrice']}, Chg {s['changePct']}%, ConsRed {s['consecutiveRed']}")
    top_stocks_str = "\n".join(top_stocks_info)
    
    sector_info, top_sectors = get_sector_rotation(stocks)
    
    # 2. Construct Prompt for Gemini
    prompt = f"""
    You are a professional stock market analyst for the Taiwan stock market (台股).
    Write a daily market analysis article based on the following data.
    
    **Data:**
    - Date: {date_str}
    - Total Momentum Stocks Found: {total}
    - Top Sectors: {', '.join(top_sectors)}
    - Top Stocks (Momentum Leaders):
    {top_stocks_str}
    
    **Requirements:**
    1. **Title**: Catchy, "clickbait" style title. Example: "多頭點火！台股今日 X 檔個股突破...".
    2. **Content**: 
       - Start with a "Market Pulse" section summarizing the general sentiment.
       - "Sector Focus": Discuss the active sectors.
       - "Spotlight": Pick the best 1-2 stocks from the list and analyze them briefly (pretend to analyze technicals based on the data).
       - Tone: Professional yet exciting, encouraging but notifying risks.
    3. **Format**: Return the result in pure Markdown. Use bolding and lists.
    4. **Language**: Traditional Chinese (繁體中文).
    """

    # 3. Call Gemini (or Fallback)
    print("🤖 Asking Gemini to write the article...")
    ai_content = ask_gemini(prompt)
    
    if ai_content:
        # Parse Title and Content from AI response
        # Assume first line is title if it starts with #
        lines = ai_content.strip().split('\n')
        title = f"{date_str} 盤勢分析 (AI EXCLUSIVE)"
        content = ai_content
        
        # Simple heuristic to extract title if provided
        if lines[0].startswith('# '):
            title = lines[0].replace('# ', '').strip()
            content = '\n'.join(lines[1:]).strip()
            
        print("✅ Gemini generated content successfully.")
    else:
        print("⚠️ Gemini not available or failed. Using template fallback.")
        # Fallback to original template logic
        market_md = get_market_summary(scan_results)
        stock_md, stock_highlights = get_stock_analysis(scan_results) # Use old helper
        
        title = f"{date_str} 盤勢分析運算結果"
        content = f"{market_md}\n---\n{sector_info}\n---\n{stock_md}"

    
    disclaimer = (
        "\n\n## ⚠️ 免責聲明\n"
        "本系統僅提供數據運算與客觀條件篩選功能，不提供任何投資建議。\n"
        "使用者應自行判斷風險，過往數據不代表未來績效。\n"
        "本報告內容僅供參考，不構成任何買賣邀約。"
    )
    
    full_content = content + disclaimer
    
    article = {
        "date": date_str,
        "generatedAt": datetime.now().isoformat(),
        "title": title,
        "content": full_content, 
        "isAiGenerated": bool(ai_content),
        "metadata": {
            "totalStocks": len(stocks),
            "topSectors": top_sectors,
        }
    }
    
    return article

def save_to_json(article_data: dict, output_dir: Path = OUTPUT_DIR) -> bool:
    """Save article to JSON file"""
    try:
        # Create articles directory
        articles_dir = output_dir / "articles"
        articles_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as YYYY-MM-DD.json
        doc_id = article_data['date']
        file_path = articles_dir / f"{doc_id}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Article saved to file: {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving to file: {e}")
        return False



def main(manual_trigger=False):
    """Main execution entry point"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--trigger-only', action='store_true')
    args = parser.parse_args()

    # Determine input path
    input_file = OUTPUT_DIR / "daily_scan_results.json"
    if not input_file.exists():
        print(f"Error: {input_file} not found. Cannot generate article.")
        return

    print(f"Reading scan results from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("Generating article...")
    article = generate_daily_article(data)
    
    print("Saving to JSON...")
    if not save_to_json(article):
        print("Save failed.")
        if manual_trigger:
            sys.exit(1)
    else:
        # Regenerate the articles index after saving
        print("Regenerating articles index...")
        try:
            from update_daily import generate_articles_index
        except ModuleNotFoundError:
            from scripts.update_daily import generate_articles_index
        generate_articles_index()

if __name__ == "__main__":
    main(manual_trigger=True)
