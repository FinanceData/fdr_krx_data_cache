
from collectors import collect_krx_index
from storage import save_csv_by_year
from krx_auth import login
import time

def run():
    if not login():
        print("Login failed")
        return
    
    symbol = "KRX-INDEX:1001"
    start_date = "1995-05-01"
    sub = "year_krx_index_1001"
    
    print(f"Collecting {symbol} from {start_date}...")
    try:
        df = collect_krx_index(symbol, start_date)
        print(f"Collected {len(df)} rows")
        if df.empty:
            print("DataFrame is empty!")
            return
        
        paths = save_csv_by_year(df, "index", sub)
        print(f"Saved {len(paths)} yearly files.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
