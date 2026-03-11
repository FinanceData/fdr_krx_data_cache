"""
프로젝트 설정 및 상수 정의
"""
import os
from pathlib import Path
import dotenv
dotenv.load_dotenv()

# ── 프로젝트 경로 ──
PROJECT_ROOT = Path(__file__).parent
DATA_ROOT = PROJECT_ROOT / "data"

# ── KRX 계정 (환경변수 우선, 없으면 기본값) ──
KRX_ID = os.environ.get("KRX_ID", "id")
KRX_PW = os.environ.get("KRX_PW", "pw")

# ── 공통 헤더 ──
KRX_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": "https://data.krx.co.kr/contents/MDC/MDI/outerLoader/index.cmd",
}

# ── 수집 대상 정의 ──
# StockListing 수집 대상
LISTING_MARKETS = ["KRX", "KOSDAQ", "KRX-DELISTING"]

# DataReader 지수 수집 대상
INDEX_SYMBOLS = ["KS11", "KQ11", "KS200"]

# DataReader KRX 지수 수집 대상
KRX_INDEX_SYMBOLS = ["KRX-INDEX:1001"]

# 연도별 저장 지수 수집 대상
YEARLY_INDEX_SYMBOLS = ["KQ11", "KS11", "KS200"]


# SnapDataReader 수집 대상
SNAP_TICKERS = ["KRX/INDEX/STOCK/1001"]
