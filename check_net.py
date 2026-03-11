import requests
import sys

print("Testing simple requests.get...")
try:
    r = requests.get("https://www.google.com", timeout=5)
    print(f"Status Google: {r.status_code}")
except Exception as e:
    print(f"Error Google: {e}")

try:
    url = "http://kind.krx.co.kr"
    print(f"Testing KIND Home: {url}")
    r = requests.get(url, timeout=5)
    print(f"Status KIND: {r.status_code}")
except Exception as e:
    print(f"Error KIND: {e}")
