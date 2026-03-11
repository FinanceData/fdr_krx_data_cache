import logging
import sys
import pandas as pd
from krx_auth import login
from collectors import collect_listing_desc
from storage import save_csv
from datetime import date

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    try:
        if not login():
            print("Login failed")
            return
        
        print("Starting collect_listing_desc('KRX')...")
        df = collect_listing_desc("KRX")
        if df is not None and not df.empty:
            print(f"Collected {len(df)} rows.")
            path = save_csv(df, "listing", "desc", date.today())
            print(f"File saved to: {path}")
        else:
            print("No data collected or DataFrame is empty.")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
