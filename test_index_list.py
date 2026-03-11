import logging
import sys
from datetime import date
from collectors import collect_index_list
from krx_auth import login
from storage import save_csv

logging.basicConfig(level=logging.INFO)

if not login():
    print("Login failed")
    sys.exit(1)

df = collect_index_list()
print(f"Collected {len(df)} rows")
path = save_csv(df, "snap", "index_list", date.today())
print(f"Saved to {path}")
