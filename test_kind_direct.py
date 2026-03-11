import requests
import io
import pandas as pd
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
headers = {'User-Agent': 'Mozilla/5.0'}

print(f"1. Fetching URL: {url}")
try:
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Length: {len(r.text)}")
    print("2. Parsing HTML...")
    dfs = pd.read_html(io.StringIO(r.text), header=0)
    print(f"Found {len(dfs)} tables")
    if dfs:
        print(f"First table shape: {dfs[0].shape}")
except Exception as e:
    print(f"Error: {e}")
