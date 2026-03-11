import requests
import io
import pandas as pd
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Referer': 'https://data.krx.co.kr/contents/MDC/MDI/outerLoader/index.cmd'
}

print(f"1. Fetching URL: {url}")
try:
    # Use a bigger timeout just in case it's just slow
    r = requests.get(url, headers=headers, timeout=20)
    print(f"Status: {r.status_code}")
    print(f"Length: {len(r.text)}")
    print("2. Parsing HTML...")
    # KIND uses EUC-KR often. Let's try to set encoding if it's wrong
    if r.encoding == 'ISO-8859-1':
        r.encoding = 'EUC-KR'
    
    dfs = pd.read_html(io.StringIO(r.text), header=0)
    print(f"Found {len(dfs)} tables")
    if dfs:
        print(f"First table shape: {dfs[0].shape}")
        print(dfs[0].head())
except Exception as e:
    print(f"Error: {e}")
