print("1. Start")
import requests
url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
headers = {'User-Agent': 'Mozilla/5.0'}
print(f"2. Fetching {url}")
r = requests.get(url, headers=headers, timeout=5)
print(f"3. Status: {r.status_code}")
print(f"4. Length: {len(r.text)}")
print("5. End")
