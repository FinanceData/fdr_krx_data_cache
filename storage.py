"""
CSV 파일 저장 유틸리티

data/{category}/{sub}/{YYYY-MM-DD}.csv 형식으로 저장합니다.
"""
import logging
from datetime import date
from pathlib import Path

import pandas as pd

from config import DATA_ROOT

logger = logging.getLogger(__name__)


def get_csv_path(category: str, sub: str, dt: date | None = None) -> Path:
    """
    데이터 저장 경로 생성

    Args:
        category: 대분류 (listing, index, detail, snap)
        sub: 소분류 (krx, kosdaq, delisting, ks11, ...)
        dt: 기준일 (기본값: 오늘)

    Returns:
        Path: data/{category}/{sub}/{YYYY-MM-DD}.csv
    """
    dt = dt or date.today()
    directory = DATA_ROOT / category / sub
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{dt.isoformat()}.csv"


def save_csv(df: pd.DataFrame, category: str, sub: str, dt: date | None = None) -> Path | None:
    """
    DataFrame을 단일 CSV 파일로 저장. 
    오늘 날짜가 아니면서 파일이 이미 존재하면 건너뜁니다. 오늘 날짜면 덮어씁니다.
    """
    target_dt = dt or date.today()
    path = get_csv_path(category, sub, target_dt)
    
    # 오늘이 아니면서 이미 존재하면 건너뜀
    if target_dt != date.today() and path.exists():
        logger.info("과거 데이터 존재 → 건너뜀: %s", path)
        return path

    is_overwrite = path.exists()
    df.to_csv(path, index=True, encoding="utf-8-sig")
    
    if is_overwrite:
        logger.info("업데이트 완료 (덮어쓰기): %s (%d rows)", path, len(df))
    else:
        logger.info("저장 완료: %s (%d rows)", path, len(df))
        
    return path


def save_csv_by_day(df: pd.DataFrame, category: str, sub: str) -> list[Path]:
    """
    DataFrame의 인덱스(날짜)별로 분할하여 각각 CSV로 저장합니다.
    인덱스는 반드시 DatetimeIndex여야 합니다.
    """
    if df.empty:
        # 분할 저장의 경우 날짜가 없으면 저장 대상이 모호하므로 리턴
        return []

    # 인덱스가 DatetimeIndex가 아니면 시도
    if not isinstance(df.index, pd.DatetimeIndex):
        if "Date" in df.columns:
            df = df.set_index("Date")
        else:
            # 인덱스를 날짜로 변환 시도
            try:
                df.index = pd.to_datetime(df.index)
            except Exception:
                logger.error("날짜 인덱스를 찾을 수 없어 분할 저장에 실패했습니다. (%s/%s)", category, sub)
                return []

    saved_paths = []
    # 날짜별로 그룹화하여 저장
    for dt, group in df.groupby(df.index.date):
        path = save_csv(group, category, sub, dt)
        if path:
            saved_paths.append(path)
    
    return saved_paths


def save_csv_by_year(df: pd.DataFrame, category: str, sub: str) -> list[Path]:
    """
    DataFrame의 인덱스(날짜)별로 분할하여 연도별 CSV로 저장합니다.
    파일명은 YYYY.csv 형식이 됩니다.
    """
    if df.empty:
        return []

    # 인덱스가 DatetimeIndex가 아니면 시도
    if not isinstance(df.index, pd.DatetimeIndex):
        if "Date" in df.columns:
            df = df.set_index("Date")
        else:
            try:
                df.index = pd.to_datetime(df.index)
            except Exception:
                logger.error("날짜 인덱스를 찾을 수 없어 연도별 저장에 실패했습니다. (%s/%s)", category, sub)
                return []

    saved_paths = []
    directory = DATA_ROOT / category / sub
    directory.mkdir(parents=True, exist_ok=True)

    current_year = date.today().year

    for year, group in df.groupby(df.index.year):
        path = directory / f"{year}.csv"
        
        # 오늘 연도가 아니면서 이미 존재하면 건너뜀
        if year != current_year and path.exists():
            logger.info("과거 연도 데이터 존재 → 건너뜀: %s", path)
            saved_paths.append(path)
            continue
            
        group.to_csv(path, index=True, encoding="utf-8-sig")
        logger.info("연도별 저장 완료: %s (%d rows)", path, len(group))
        saved_paths.append(path)
    
    return saved_paths


def normalize_sub_name(raw: str) -> str:
    """
    API 파라미터를 폴더명으로 변환

    Examples:
        'KRX'                    → 'krx'
        'KOSDAQ'                 → 'kosdaq'
        'KRX-DELISTING'          → 'delisting'
        'KS11'                   → 'ks11'
        'KRX-INDEX:1001'         → 'krx_index_1001'
        'KRX-DETAIL:005930'      → '005930'
        'KRX/INDEX/STOCK/1001'   → 'index_stock_1001'
    """
    raw = raw.strip()

    # StockListing 시장명
    if raw in ("KRX", "KOSPI", "KOSDAQ", "KONEX"):
        return raw.lower()
    if raw == "KRX-DELISTING":
        return "delisting"

    # DataReader KRX-INDEX:XXXX
    if raw.startswith("KRX-INDEX:"):
        code = raw.split(":")[1]
        return f"krx_index_{code}"


    # SnapDataReader KRX/INDEX/STOCK/XXXX
    if raw.startswith("KRX/INDEX/STOCK/"):
        code = raw.split("/")[-1]
        return f"index_stock_{code}"

    # 기타: 소문자, 특수문자 → 언더스코어
    return raw.lower().replace("-", "_").replace(":", "_").replace("/", "_")
