from krx_auth import session, login
import logging
import sys

# Configure logging to see the output
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

def test_auth():
    print("Testing krx_auth.login()...")
    # This should now succeed anonymously even with default 'id'/'pw'
    success = login()
    print(f"Login success: {success}")
    
    print("\nChecking session cookies...")
    for cookie in session.cookies:
        print(f"[{cookie.domain}] {cookie.name}: {cookie.value}")

    # Try a simple Finder API call that usually requires session
    print("\nTesting Finder API anonymously...")
    url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
    data = {"bld": "dbms/comm/finder/finder_stkisu"}
    r = session.post(url, data=data, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        j = r.json()
        count = len(j.get('block1', []))
        print(f"Found {count} tickers")
    else:
        print(f"Failed: {r.text}")

if __name__ == "__main__":
    test_auth()
