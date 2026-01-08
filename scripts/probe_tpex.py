import requests
import json
from datetime import datetime, timedelta

today_str = (datetime.now().year - 1911)
str_date = f"{today_str}/{datetime.now().month:02d}/{datetime.now().day:02d}"

base_url = "https://www.tpex.org.tw/openapi/v1"
endpoints = [
    "/tpex_disposal_information",
    "/tpex_trading_warning_information",
    "/tpex_esb_disposal_information"
]

print(f"Testing TPEX Open API for date: {str_date}")

# Note: many open apis don't need date for 'current' info, or use 'd'
# The standard parameter usually is startDate/endDate or l=zh-tw or just returns latest.
# Let's try without params first, then with 'd' or 'Date'

for ep in endpoints:
    url = f"{base_url}{ep}"
    print(f"\nTesting: {url}")
    try:
        # Try raw first
        r = requests.get(url, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Items: {len(data)}")
            if len(data) > 0:
                print("Sample:", json.dumps(data[0], ensure_ascii=False))
        else:
            print(f"Error Body: {r.text[:100]}")
    except Exception as e:
        print(f"Error: {e}")
