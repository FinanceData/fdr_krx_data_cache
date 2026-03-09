
import pandas as pd
from collectors import collect_index
from storage import save_csv_by_year
from krx_auth import login
import time

def run():
    if not login():
        print("Login failed")
        return
    
    symbol = "KQ11"
    start_date = "1995-05-01"
    sub = "year_kq11"
    
    print(f"Collecting {symbol} from {start_date}...")
    df = collect_index(symbol, start_date)
    print(f"Collected {len(df)} rows")
    
    paths = save_csv_by_year(df, "index", sub)
    print(f"Saved {len(paths)} yearly files.")

if __name__ == "__main__":
    run()
