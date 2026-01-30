import requests
from datetime import datetime, timedelta

def get_twse_attention_history(days=30):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    url = "https://www.twse.com.tw/rwd/zh/announcement/notice"
    params = {
        'response': 'json',
        'startDate': start_date.strftime('%Y%m%d'),
        'endDate': end_date.strftime('%Y%m%d')
    }
    
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if 'data' in data:
            # Code is at index 1, Date is at index 5
            history = {}
            for item in data['data']:
                code = item[1]
                date = item[5]
                if code not in history:
                    history[code] = []
                history[code].append(date)
            return history
    except Exception as e:
        print(f"Error: {e}")
    return {}

def get_tpex_attention_history(days=30):
    url = "https://www.tpex.org.tw/openapi/v1/tpex_trading_warning_information"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            history = {}
            for item in r.json():
                code = item.get('SecuritiesCompanyCode')
                date = item.get('Date') # Compact ROC 1140108
                if code not in history:
                    history[code] = []
                history[code].append(date)
            return history
    except Exception as e:
        print(f"Error: {e}")
    return {}

if __name__ == "__main__":
    twse = get_twse_attention_history()
    print(f"TWSE unique stocks with attention history: {len(twse)}")
    if twse:
        sample_code = list(twse.keys())[0]
        print(f"Sample {sample_code}: {twse[sample_code]}")
        
    tpex = get_tpex_attention_history()
    print(f"TPEx unique stocks with attention history: {len(tpex)}")
    if tpex:
        sample_code = list(tpex.keys())[0]
        print(f"Sample {sample_code}: {tpex[sample_code]}")
