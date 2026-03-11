import requests
from krx_auth import session, login
import pandas as pd

login()
url = 'http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd'
data = {'bld': 'dbms/comm/finder/finder_stkisu'}
print(f"Fetching Finder: {url}")
try:
    r = session.post(url, data=data, timeout=10)
    print(f"Status: {r.status_code}")
    jo = r.json()
    df = pd.DataFrame(jo.get('block1', []))
    print(f"Count: {len(df)}")
    print(df.head())
except Exception as e:
    print(f"Error Finder: {e}")
