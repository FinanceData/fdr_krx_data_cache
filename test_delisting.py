from collectors import collect_listing_delisting
from krx_auth import login
import pandas as pd
import json

try:
    login()
    df = collect_listing_delisting('1960-01-01')
    with open('out_test.txt', 'w') as f:
        f.write(f"Total collected: {len(df)}\n")
        f.write(str(df.head()))
except Exception as e:
    with open('out_test.txt', 'w') as f:
        f.write(f"ERROR: {e}")
