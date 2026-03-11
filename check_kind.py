import requests
import io
import ssl
import pandas as pd

# 1. KIND URL TEST
ssl._create_default_https_context = ssl._create_unverified_context
url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Referer': 'https://data.krx.co.kr/contents/MDC/MDI/outerLoader/index.cmd'
}
print(f"Fetching KIND: {url}")
try:
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Length: {len(r.text)}")
    dfs = pd.read_html(io.StringIO(r.text), header=0)
    print(f"First 5 rows:\n{dfs[0].head()}")
except Exception as e:
    print(f"Error KIND: {e}")
