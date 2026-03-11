import requests
try:
    url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
    r = requests.get(url, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Content length: {len(r.text)}")
except Exception as e:
    print(f"Error: {e}")
