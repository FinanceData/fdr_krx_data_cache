import logging
import sys
from datetime import date
from collectors import collect_listing_desc
from krx_auth import login
from storage import save_csv

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

def test():
    try:
        logger.info("Attempting login...")
        if not login():
            logger.error("Login failed")
            return
        
        logger.info("Attempting collect_listing_desc('KRX')...")
        df = collect_listing_desc("KRX")
        if df.empty:
            logger.warning("Collected data is empty")
        else:
            logger.info(f"Collected {len(df)} rows")
            logger.info(f"Columns: {list(df.columns)}")
            
            # Test storage path
            path = save_csv(df, "listing", "desc", date.today())
            logger.info(f"Saved to: {path}")
            
    except Exception as e:
        logger.exception(f"An error occurred: {e}")

if __name__ == "__main__":
    test()
