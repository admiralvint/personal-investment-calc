import pandas as pd
import requests
import io
import traceback
import urllib3

# Suppress warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_trigon_debug():
    url = "https://trigoncapital.com/asset-management/trigon-dividend-fund/hable-download?name=TNESCFD"
    print(f"Fetching from: {url}")
    
    try:
        # Use requests with verify=False
        resp = requests.get(url, verify=False)
        resp.raise_for_status()
        
        print("Fetch successful (status 200).")
        
        # content is bytes, decode? or use io.BytesIO
        # CSV usually text
        content = resp.content.decode('utf-8')
        
        df = pd.read_csv(io.StringIO(content), header=None, names=['Date', 'Close'], on_bad_lines='skip')
        
        print(df.head())
        print(f"Rows: {len(df)}")
        
        # Check cleaning logic
        df = df[df['Date'].str.match(r'\d{4}-\d{2}-\d{2}')]
        print(f"Rows after date filter: {len(df)}")
        
        df['Date'] = pd.to_datetime(df['Date'])
        last_date = df['Date'].max()
        last_price = df.loc[df['Date'] == last_date, 'Close'].values[0]
        print(f"Last Date: {last_date}, Clos: {last_price}")
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    fetch_trigon_debug()
