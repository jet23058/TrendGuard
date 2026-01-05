import json
from pathlib import Path
from datetime import datetime

data_text = """
3455    由田       光電業     119.5   112.5     4  116.5
3516    亞帝歐      光電業      21.4    20.9     5  19.95
8064    東捷       光電業     48.45   48.35     4     47
3481    群創       光電業      18.1   17.75     5  16.29
3289    宜特      其他電子業    126.5  119.87     3    119
3402    漢科      其他電子業    142.5   136.5     3    137
3580    友威科     其他電子業     69.1      67     4   65.3
5452    佶優      其他電子業     30.9    28.7     2   28.7
8431    匯鑽科     其他電子業     74.1    70.9     3   67.2
5351    鈺創       半導體業     55.8    52.4     6   50.3
2330    台積電      半導體業     1585    1550     5   1545
2337    旺宏       半導體業    43.35   42.25     3  40.05
2449   京元電子      半導體業    267.5   261.5     2  252.5
2454    聯發科      半導體業     1470    1460     4   1440
3006    晶豪科      半導體業    129.5     118     3    117
3711   日月光投控     半導體業      258     255     2    250
4967    十銓       半導體業    193.5     189     4  183.5
6531    愛普*      半導體業    458.5     448     3    445
8110    華東       半導體業     62.3    59.5     3   58.2
5263    智崴      文化創意業    113.5   103.5     3    108
1460    宏遠       紡織纖維     6.39    6.38     2   6.34
8423   保綠-KY     綠能環保     18.3   18.15     3   18.2
8438    昶昕       綠能環保    46.05    41.9     7  43.55
5704    老爺知      觀光餐旅     29.4    28.8     3  28.05
3163    波若威     通信網路業    418.5     408     3    400
2025    千興       鋼鐵工業     11.3    11.2     2  10.17
3360    尚立      電子通路業     15.2   13.85     4   14.7
6265    方土昶     電子通路業    33.45   32.15     6   32.8
3624    光頡      電子零組件業    64.2    58.4     3   59.1
3689    湧德      電子零組件業     127     118     3  115.5
2460    建通      電子零組件業    22.1    21.5     2  19.89
2467    志聖      電子零組件業     270   259.5     4    250
3092    鴻碩      電子零組件業    26.8    26.5     6   24.5
3308    聯德      電子零組件業    22.1    20.1     5  21.15
4912  聯德控股-KY   電子零組件業   105.5    97.6     4   97.9
5288   豐祥-KY     電機機械      147   142.5     3  136.5
5289    宜鼎     電腦及週邊設備業    595     576     4    559
2399    映泰     電腦及週邊設備業   27.3   26.95     2   26.1
"""

stocks = []
for line in data_text.strip().split('\n'):
    parts = line.split()
    if len(parts) >= 7:
        stock = {
            "ticker": parts[0],
            "name": parts[1],
            "sector": parts[2],
            "currentPrice": float(parts[3]),
            "prevHigh": float(parts[4]),
            "consecutiveRed": int(parts[5]),
            "stopLoss": float(parts[6]),
             # Add dummy data for required fields
            "recommendation": {"type": "buy", "priority": 100},
            "ohlc": []
        }
        stocks.append(stock)

output = {
    "date": "2026-01-02",
    "updatedAt": "2026-01-02T14:30:00",
    "scanType": "livermore_breakout",
    "stocks": stocks,
    "summary": {
        "total": len(stocks),
    }
}

output_path = Path("frontend/public/data/daily_recommendations.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Seeded {len(stocks)} stocks from 01/02 data to {output_path}")
