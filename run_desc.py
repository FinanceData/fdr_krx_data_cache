import logging
import sys
from datetime import date
from collectors import collect_listing_desc
from krx_auth import login
from storage import save_csv

# Force print for debugging
def log(msg):
    print(f"DEBUG: {msg}")
    sys.stdout.flush()

def main():
    log("1. Starting Authentication")
    if not login():
        log("FAILED: Authentication Failed")
        return
    
    log("2. Starting collect_listing_desc('KRX')")
    try:
        # We'll see if this hangs
        df = collect_listing_desc("KRX")
        if df is None:
             log("FAILED: df is None")
             return
        if df.empty:
            log("FAILED: df is empty")
            return

        log(f"3. Collected {len(df)} rows. Saving CSV.")
        today = date.today()
        path = save_csv(df, "listing", "desc", today)
        log(f"4. Success: {path}")
        
    except Exception as e:
        log(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
