import logging
import sys
import io
import ssl
import pandas as pd
import requests
from krx_auth import session, login

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

def debug_collect():
    try:
        login()
        logger.info("1. Fetching KIND list...")
        ssl._create_default_https_context = ssl._create_unverified_context
        url_kind = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
        # Try with a common User-Agent if session.get fails or hangs
        r_kind = session.get(url_kind, timeout=30)
        logger.info(f"   Response status: {r_kind.status_code}")
        
        logger.info("2. Parsing KIND HTML...")
        dfs = pd.read_html(io.StringIO(r_kind.text), header=0)
        df_listing = dfs[0]
        logger.info(f"   Found {len(df_listing)} rows in KIND")
        
        logger.info("3. Fetching Finder list...")
        data_finder = {'bld': 'dbms/comm/finder/finder_stkisu'}
        url_finder = 'http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd'
        r_finder = session.post(url_finder, data=data_finder, timeout=30)
        logger.info(f"   Response status: {r_finder.status_code}")
        
        jo = r_finder.json()
        df_finder = pd.DataFrame(jo.get('block1', []))
        logger.info(f"   Found {len(df_finder)} rows in Finder")

        logger.info("4. Merging...")
        # ... (rest of merge logic)
        logger.info("Success!")
        
    except Exception as e:
        logger.exception("Error during debug_collect")

if __name__ == "__main__":
    debug_collect()
