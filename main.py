"""
메인 데이터 수집 스크립트

GitHub Actions 또는 로컬에서 실행하여 KRX 데이터를 수집하고 CSV로 저장합니다.

사용법:
    python main.py                    # 전체 수집
    python main.py --only listing     # listing만 수집
    python main.py --only snap        # snap만 수집
    python main.py --only index       # index만 수집
    python main.py --only kq-yearly   # KQ11 연도별 수집 (히스토리)
"""
import argparse
import logging
import sys
import time
from datetime import date

from config import (
    DATA_ROOT,
    INDEX_SYMBOLS,
    KRX_INDEX_SYMBOLS,
    LISTING_MARKETS,
    SNAP_TICKERS,
    YEARLY_INDEX_SYMBOLS,
)
from collectors import (
    collect_index,
    collect_krx_index,
    collect_listing_delisting,
    collect_listing_marcap,
    collect_snap,
)
from krx_auth import login
from storage import normalize_sub_name, save_csv, save_csv_by_day, save_csv_by_year

# ── 로깅 설정 ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def collect_historical_yearly_indices() -> None:
    """특정 지수의 연도별 데이터 수집 (예: KQ11, KRX-INDEX:1001 1995-05-01 ~)"""
    current_year = date.today().year
    
    for symbol in YEARLY_INDEX_SYMBOLS:
        try:
            # 기본 시작일 설정
            if symbol == "KS200":
                start_date_str = "1990-01-01"
            elif symbol in ("KQ11", "KS11", "KRX-INDEX:1001"):
                start_date_str = "1995-05-01"
            else:
                start_date_str = "2000-01-01"
            
            # 저장 폴더 결정
            if symbol == "KRX-INDEX:1001":
                sub = "year_krx_index_1001"
            else:
                sub = f"year_{normalize_sub_name(symbol)}"
                
            # ── 기존 파일 확인하여 수집 시작일 조정 (SKIP logic) ──
            target_dir = DATA_ROOT / "index" / sub
            if target_dir.exists():
                existing_years = sorted([
                    int(p.stem) for p in target_dir.glob("*.csv") 
                    if p.stem.isdigit()
                ])
                # 오늘 연도가 아닌(과거) 연도 중 가장 최근 연도
                past_years = [y for y in existing_years if y < current_year]
                if past_years:
                    last_year = past_years[-1]
                    # 다음 해 1월 1일부터 수집하도록 조정
                    adjusted_start = f"{last_year + 1}-01-01"
                    if adjusted_start > start_date_str:
                        start_date_str = adjusted_start
                        logger.info("[%s] 과거 데이터 존재(최종:%d년) -> 수집 시작일 조정: %s", 
                                    symbol, last_year, start_date_str)

            # 수집 기간이 이미 오늘을 넘었으면 스킵
            if start_date_str > date.today().isoformat():
                logger.info("[%s] 모든 데이터가 최신입니다. 수집을 건너뜁니다.", symbol)
                continue

            logger.info("[%s] 수집 시작 (%s ~) -> %s", symbol, start_date_str, sub)
            
            if symbol.startswith("KRX-INDEX:"):
                df = collect_krx_index(symbol, start_date_str)
            else:
                df = collect_index(symbol, start_date_str)
                
            if not df.empty:
                logger.info("[%s] %d 건 수집 완료", symbol, len(df))
                save_csv_by_year(df, "index", sub)
            time.sleep(1)
        except Exception as e:
            logger.error("yearly_index/%s 수집 실패: %s", symbol, e, exc_info=True)


def collect_all_listings(target_date: date) -> None:
    """StockListing 계열 수집 (오늘/기준일 기준)"""
    for market in LISTING_MARKETS:
        try:
            sub = normalize_sub_name(market)
            if market == "KRX-DELISTING":
                # 상장폐지는 기간 조절이 가능하나 기본적으로 오늘까지 수집
                df = collect_listing_delisting()
            else:
                df = collect_listing_marcap(market)
            save_csv(df, "listing", sub, target_date)
            time.sleep(1)
        except Exception as e:
            logger.error("listing/%s 수집 실패: %s", market, e, exc_info=True)


def collect_all_indices(start_str: str, end_str: str | None = None) -> None:
    """DataReader 지수 계열 수집 (기간별 분할 저장)"""
    is_single_day = (end_str is None) or (start_str == end_str)
    
    for symbol in INDEX_SYMBOLS:
        try:
            sub = normalize_sub_name(symbol)
            df = collect_index(symbol, start_str, end_str)
            if df.empty and is_single_day:
                save_csv(df, "index", sub, date.fromisoformat(start_str))
            else:
                save_csv_by_day(df, "index", sub)
            time.sleep(1)
        except Exception as e:
            logger.error("index/%s 수집 실패: %s", symbol, e, exc_info=True)

    for symbol in KRX_INDEX_SYMBOLS:
        try:
            sub = normalize_sub_name(symbol)
            df = collect_krx_index(symbol, start_str, end_str)
            if df.empty and is_single_day:
                save_csv(df, "index", sub, date.fromisoformat(start_str))
            else:
                save_csv_by_day(df, "index", sub)
            time.sleep(1)
        except Exception as e:
            logger.error("index/%s 수집 실패: %s", symbol, e, exc_info=True)


def collect_all_snaps(target_date: date) -> None:
    """SnapDataReader 계열 수집 (당일 스냅)"""
    for ticker in SNAP_TICKERS:
        try:
            sub = normalize_sub_name(ticker)
            df = collect_snap(ticker)
            save_csv(df, "snap", sub, target_date)
            time.sleep(1)
        except Exception as e:
            logger.error("snap/%s 수집 실패: %s", ticker, e, exc_info=True)


def main():
    parser = argparse.ArgumentParser(description="KRX 데이터 수집기")
    parser.add_argument(
        "--only",
        choices=["listing", "index", "snap", "kq-yearly"],
        help="특정 카테고리만 수집",
    )
    parser.add_argument("--start", help="시작일 (YYYY-MM-DD), 기본값: 오늘")
    parser.add_argument("--end", help="종료일 (YYYY-MM-DD), 기본값: 오늘")
    
    args = parser.parse_args()

    today = date.today()
    start_str = args.start or today.isoformat()
    end_str = args.end or today.isoformat()
    target_date = date.fromisoformat(start_str)

    logger.info("=" * 60)
    logger.info("KRX 데이터 수집 시작: %s ~ %s", start_str, end_str)
    logger.info("=" * 60)

    # ── KRX 로그인 ──
    if not login():
        logger.critical("KRX 로그인 실패 → 수집 중단")
        sys.exit(1)

    # ── 수집 실행 ──
    if args.only == "listing":
        collect_all_listings(target_date)
    elif args.only == "index":
        collect_all_indices(start_str, end_str)
    elif args.only == "snap":
        collect_all_snaps(target_date)
    elif args.only == "kq-yearly":
        collect_historical_yearly_indices()
    elif not args.only:
        logger.info("── listing 계열 수집 시작 ──")
        collect_all_listings(target_date)
        logger.info("── index 계열 수집 시작 ──")
        collect_all_indices(start_str, end_str)
        logger.info("── snap 계열 수집 시작 ──")
        collect_all_snaps(target_date)
        # kq-yearly는 히스토리 수집이므로 기본 포함시키지 않음 (필요시 수동 실행)

    logger.info("=" * 60)
    logger.info("수집 완료")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
