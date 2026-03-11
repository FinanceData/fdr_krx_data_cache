"""
KRX 데이터 수집기 (Collectors)

각 수집기는 KRX API를 호출하여 pandas DataFrame을 반환합니다.
refs/ 폴더의 krx_listing.py, krx_snap.py를 기반으로 구현합니다.
"""
import io
import json
import logging
import ssl
from datetime import date, datetime, timedelta

import pandas as pd
import requests

from krx_auth import session

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════
#  1. StockListing 계열  (listing/)
# ════════════════════════════════════════════════════════════════

def _get_latest_trade_date() -> str:
    """KRX에서 최신 거래일 문자열(YYYYMMDD)을 가져옵니다."""
    url = (
        "http://data.krx.co.kr/comm/bldAttendant/executeForResourceBundle.cmd"
        "?baseName=krx.mdc.i18n.component&key=B128.bld"
    )
    r = session.get(url, timeout=15)
    j = r.json()
    return j["result"]["output"][0]["max_work_dt"]


def collect_listing_marcap(market: str) -> pd.DataFrame:
    """
    종목 시세 (시가총액 기준) 수집

    Args:
        market: 'KRX'(전체), 'KOSPI', 'KOSDAQ', 'KONEX'

    Returns:
        DataFrame with columns: Code, Name, Close, Dept, Changes, ChagesRatio,
                                Volume, Amount, Open, High, Low, Marcap, Stocks, Market
    """
    mkt_map = {"KRX": "ALL", "KOSPI": "STK", "KOSDAQ": "KSQ", "KONEX": "KNX"}
    if market not in mkt_map:
        raise ValueError(f"market should be one of {list(mkt_map.keys())}")

    date_str = _get_latest_trade_date()
    logger.info("listing_marcap: market=%s, trade_date=%s", market, date_str)

    url = "https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
    data = {
        "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
        "mktId": mkt_map[market],
        "trdDd": date_str,
        "share": "1",
        "money": "1",
        "csvxls_isNo": "false",
    }
    r = session.post(url, data=data, timeout=30)
    j = r.json()
    df = pd.DataFrame(j["OutBlock_1"])

    if df.empty:
        logger.warning("listing_marcap: 데이터 없음 (market=%s)", market)
        return df

    df = df.replace(r",", "", regex=True)
    numeric_cols = [
        "CMPPREVDD_PRC", "FLUC_RT", "TDD_OPNPRC", "TDD_HGPRC", "TDD_LWPRC",
        "ACC_TRDVOL", "ACC_TRDVAL", "MKTCAP", "LIST_SHRS",
    ]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    df = df.sort_values("MKTCAP", ascending=False)

    cols_map = {
        "ISU_SRT_CD": "Code", "ISU_ABBRV": "Name",
        "TDD_CLSPRC": "Close", "SECT_TP_NM": "Dept",
        "FLUC_TP_CD": "ChangeCode", "CMPPREVDD_PRC": "Changes",
        "FLUC_RT": "ChagesRatio", "ACC_TRDVOL": "Volume",
        "ACC_TRDVAL": "Amount", "TDD_OPNPRC": "Open",
        "TDD_HGPRC": "High", "TDD_LWPRC": "Low",
        "MKTCAP": "Marcap", "LIST_SHRS": "Stocks",
        "MKT_NM": "Market", "MKT_ID": "MarketId",
    }
    df = df.rename(columns=cols_map)
    df = df.reset_index(drop=True)
    return df


def collect_listing_kosdaq() -> pd.DataFrame:
    """KOSDAQ 종목 시세 수집"""
    return collect_listing_marcap("KOSDAQ")


def collect_listing_krx() -> pd.DataFrame:
    """KRX 전체 종목 시세 수집"""
    return collect_listing_marcap("KRX")


def _krx_delisting_2years(from_date: datetime, to_date: datetime) -> pd.DataFrame:
    """KRX 상장폐지 목록 (2년 단위)"""
    data = {
        "bld": "dbms/MDC/STAT/issue/MDCSTAT23801",
        "mktId": "ALL",
        "isuCd": "ALL",
        "isuCd2": "ALL",
        "strtDd": from_date.strftime("%Y%m%d"),
        "endDd": to_date.strftime("%Y%m%d"),
        "share": "1",
        "csvxls_isNo": "true",
    }
    url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
    r = session.post(url, data=data, timeout=30)
    jo = r.json()
    df = pd.DataFrame(jo["output"])

    if df.empty:
        return df

    col_map = {
        "ISU_CD": "Symbol", "ISU_NM": "Name", "MKT_NM": "Market",
        "SECUGRP_NM": "SecuGroup", "KIND_STKCERT_TP_NM": "Kind",
        "LIST_DD": "ListingDate", "DELIST_DD": "DelistingDate",
        "DELIST_RSN_DSC": "Reason",
        "ARRANTRD_MKTACT_ENFORCE_DD": "ArrantEnforceDate",
        "ARRANTRD_END_DD": "ArrantEndDate",
        "IDX_IND_NM": "Industry", "PARVAL": "ParValue",
        "LIST_SHRS": "ListingShares",
        "TO_ISU_SRT_CD": "ToSymbol", "TO_ISU_ABBRV": "ToName",
    }
    df = df.rename(columns=col_map)

    df["ListingDate"] = pd.to_datetime(df["ListingDate"], format="%Y/%m/%d")
    df["DelistingDate"] = pd.to_datetime(df["DelistingDate"], format="%Y/%m/%d")
    df["ArrantEnforceDate"] = pd.to_datetime(
        df["ArrantEnforceDate"], format="%Y/%m/%d", errors="coerce"
    )
    df["ArrantEndDate"] = pd.to_datetime(
        df["ArrantEndDate"], format="%Y/%m/%d", errors="coerce"
    )
    df["ParValue"] = pd.to_numeric(
        df["ParValue"].str.replace(",", ""), errors="coerce"
    )
    df["ListingShares"] = pd.to_numeric(
        df["ListingShares"].str.replace(",", ""), errors="coerce"
    )
    return df


def collect_listing_delisting(
    start: str = "1960-01-01", end: str | None = None
) -> pd.DataFrame:
    """
    KRX 상장폐지 종목 수집

    Args:
        start: 시작일 (YYYY-MM-DD)
        end: 종료일 (기본=오늘)
    """
    from_date = pd.to_datetime(start)
    to_date = pd.to_datetime(end) if end else datetime.today()

    logger.info("listing_delisting: %s ~ %s", from_date.date(), to_date.date())

    df_list = []
    _start = from_date
    _end = datetime(_start.year + 2, _start.month, _start.day) - timedelta(days=1)

    while True:
        df = _krx_delisting_2years(_start, _end)
        df_list.append(df)
        if to_date <= _end:
            break
        _start = _end + timedelta(days=1)
        _end = datetime(_start.year + 2, _start.month, _start.day) - timedelta(days=1)

    df = pd.concat(df_list, ignore_index=True)
    if df.empty:
        logger.warning("listing_delisting: 데이터 없음")
        return df

    df = df[
        (from_date <= df["DelistingDate"]) & (df["DelistingDate"] <= to_date)
    ].reset_index(drop=True)
    return df


def collect_listing_desc(market: str = "KRX") -> pd.DataFrame:
    """
    KRX 주식종목 상세정보 수집 (data.krx.co.kr API 기반)

    Finder API 로 종목 기본정보(Code, Name, Market)를 수집하고,
    KRX STAT API (전종목 시세)에서 업종(Sector) 등 상세정보를 병합합니다.

    Args:
        market: 'KRX', 'KOSPI', 'KOSDAQ', 'KONEX'
    """
    mkt_list = ['KRX', 'KOSPI', 'KOSDAQ', 'KONEX']
    if market not in mkt_list:
        raise ValueError(f"market should be one of {mkt_list}")

    logger.info("listing_desc: market=%s", market)

    # ── 0. 최신 거래일 조회 ──
    trade_date = _get_latest_trade_date()
    logger.info("listing_desc: trade_date=%s", trade_date)

    # ── 1. KRX 주식종목검색 (Finder, data.krx.co.kr) ──
    data = {'bld': 'dbms/comm/finder/finder_stkisu'}
    url_api = 'http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd'
    r = session.post(url_api, data=data, timeout=30)
    jo = r.json()
    df_finder = pd.DataFrame(jo.get('block1', []))

    if df_finder.empty:
        logger.warning("listing_desc: Finder 데이터 없음")
        return pd.DataFrame()

    df_finder = df_finder.rename(columns={
        'full_code': 'FullCode',
        'short_code': 'Code',
        'codeName': 'Name',
        'marketCode': 'MarketCode',
        'marketName': 'MarketName',
        'marketEngName': 'Market',
        'ord1': 'Ord1',
        'ord2': 'Ord2',
    })
    logger.info("listing_desc: Finder %d건 수집", len(df_finder))

    # ── 2. KRX 전종목 시세 (MDCSTAT01501, data.krx.co.kr) ──
    # 이 API는 collect_listing_marcap에서도 사용하며 안정적으로 동작함
    stat_data = {
        'bld': 'dbms/MDC/STAT/standard/MDCSTAT01501',
        'mktId': 'ALL',
        'trdDd': trade_date,
        'share': '1',
        'money': '1',
        'csvxls_isNo': 'false',
    }
    r = session.post(url_api, data=stat_data, timeout=30)
    jo = r.json()
    df_stat = pd.DataFrame(jo.get('OutBlock_1', []))

    df_detail = None
    if not df_stat.empty:
        # MDCSTAT01501 컬럼 매핑
        stat_cols = {
            'ISU_SRT_CD': 'Code',
            'ISU_ABBRV': 'Name',
            'MKT_NM': 'Market',
            'SECT_TP_NM': 'Sector',       # 소속부 (유가증권시장, 코스닥시장 등)
            'MKTCAP': 'Marcap',
            'LIST_SHRS': 'Stocks',
        }
        df_stat = df_stat.rename(columns=stat_cols)
        df_detail = df_stat[['Code', 'Sector']].copy()
        logger.info("listing_desc: STAT %d건 수집", len(df_detail))
    else:
        logger.warning("listing_desc: STAT 데이터 없음")

    # ── 3. KIND (kind.krx.co.kr) - 상세 기업정보 (optional) ──
    df_kind = None
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
        url_kind = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
        headers_kind = {
            'User-Agent': 'Chrome/78.0.3904.87 Safari/537.36',
            'Referer': 'https://data.krx.co.kr/contents/MDC/MDI/outerLoader/index.cmd'
        }
        r = requests.get(url_kind, headers=headers_kind, timeout=10)
        dfs = pd.read_html(io.StringIO(r.text), header=0)
        df_kind = dfs[0]
        cols_ren = {
            '회사명': 'Name', '종목코드': 'Code', '업종': 'Industry',
            '주요제품': 'Products', '상장일': 'ListingDate', '결산월': 'SettleMonth',
            '대표자명': 'Representative', '홈페이지': 'HomePage', '지역': 'Region',
        }
        df_kind = df_kind.rename(columns=cols_ren)
        df_kind['Code'] = df_kind['Code'].astype(str).str.zfill(6)
        df_kind['ListingDate'] = pd.to_datetime(df_kind['ListingDate'], errors='coerce')
        df_kind = df_kind[['Code', 'Industry', 'Products', 'ListingDate',
                           'SettleMonth', 'Representative', 'HomePage', 'Region']]
        logger.info("listing_desc: KIND %d건 수집", len(df_kind))
    except Exception as e:
        logger.warning("listing_desc: KIND 접근 실패 (%s)", e)

    # ── 4. 병합 ──
    # Finder 기본 정보
    merged = df_finder[['Code', 'Name', 'Market']].copy()

    # STAT 정보 병합 (Sector)
    if df_detail is not None:
        merged = pd.merge(merged, df_detail, how='left', on='Code')
    else:
        merged['Sector'] = None

    # KIND 정보 병합 (Industry, ListingDate, Representative 등)
    if df_kind is not None:
        merged = pd.merge(merged, df_kind, how='left', on='Code')
    else:
        for col in ['Industry', 'Products', 'ListingDate', 'SettleMonth',
                     'Representative', 'HomePage', 'Region']:
            merged[col] = None

    if market in ['KONEX', 'KOSDAQ', 'KOSPI']:
        merged = merged[merged['Market'] == market].reset_index(drop=True)
    merged = merged.drop_duplicates(subset='Code').reset_index(drop=True)
    logger.info("listing_desc: 최종 %d건 (market=%s)", len(merged), market)
    return merged


# ════════════════════════════════════════════════════════════════
#  2. DataReader 계열 - 지수 (index/)
#
#  ※ FinanceDataReader는 내부적으로 bare requests.post()를 사용하므로
#    우리의 로그인 세션 쿠키가 전달되지 않아 "LOGOUT" 에러가 발생합니다.
#    따라서 동일 KRX API를 인증된 session 객체로 직접 호출합니다.
# ════════════════════════════════════════════════════════════════

# ── 지수 시세: KS11, KQ11, KS200 등 (KRX 일반 지수) ──

_INDEX_SYMBOL_MAP = {
    # symbol → (indIdx, indIdx2)  —  KRX 지수 API 파라미터
    "KS11":  ("1", "001"),   # KOSPI
    "KQ11":  ("2", "001"),   # KOSDAQ
    "KS200": ("1", "028"),   # KOSPI 200
}


def _krx_index_price_2years(
    idx1: str, idx2: str, from_dt: datetime, to_dt: datetime
) -> pd.DataFrame:
    """KRX 지수 시세 (최대 2 년 단위 호출)"""
    url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
    data = {
        "bld": "dbms/MDC/STAT/standard/MDCSTAT00301",
        "indIdx": idx1,
        "indIdx2": idx2,
        "strtDd": from_dt.strftime("%Y%m%d"),
        "endDd": to_dt.strftime("%Y%m%d"),
        "share": "1",
        "money": "1",
        "csvxls_isNo": "false",
    }
    r = session.post(url, data=data, timeout=30)
    try:
        jo = r.json()
    except Exception:
        raise ValueError(f"KRX 지수 응답 파싱 실패: {r.text[:200]}")
    return pd.DataFrame(jo.get("output", []))


def collect_index(symbol: str, start: str, end: str | None = None) -> pd.DataFrame:
    """
    지수 시세 수집 (KS11, KQ11, KS200)

    Args:
        symbol: 지수 심볼
        start: 시작일 (YYYY-MM-DD)
        end: 종료일 (기본=오늘)
    """
    if symbol not in _INDEX_SYMBOL_MAP:
        raise ValueError(f"지원하지 않는 지수 심볼: {symbol}  (지원: {list(_INDEX_SYMBOL_MAP)})")

    idx1, idx2 = _INDEX_SYMBOL_MAP[symbol]
    from_dt = pd.to_datetime(start)
    to_dt = pd.to_datetime(end) if end else pd.Timestamp.today().to_pydatetime()
    logger.info("index: symbol=%s (%s/%s), %s ~ %s", symbol, idx1, idx2, from_dt.date(), to_dt.date())

    # 2 년 단위 분할 호출
    df_list: list[pd.DataFrame] = []
    _start = from_dt
    while True:
        _end = datetime(_start.year + 2, _start.month, _start.day) - timedelta(days=1)
        df = _krx_index_price_2years(idx1, idx2, _start, min(_end, to_dt))
        df_list.append(df)
        if to_dt <= _end:
            break
        _start = _end + timedelta(days=1)

    df = pd.concat(df_list, ignore_index=True)
    if df.empty:
        logger.warning("index/%s: 데이터 없음", symbol)
        return df

    col_map = {
        "TRD_DD": "Date", "CLSPRC_IDX": "Close", "FLUC_TP_CD": "UpDown",
        "PRV_DD_CMPR": "Comp", "UPDN_RATE": "Change",
        "OPNPRC_IDX": "Open", "HGPRC_IDX": "High", "LWPRC_IDX": "Low",
        "ACC_TRDVOL": "Volume", "ACC_TRDVAL": "Amount", "MKTCAP": "MarCap",
    }
    df = df.rename(columns=col_map)
    num_cols = [c for c in ["Close", "Comp", "Change", "Open", "High", "Low", "Volume", "Amount", "MarCap"] if c in df.columns]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", ""), errors="coerce")
    if "Change" in df.columns:
        df["Change"] = df["Change"] / 100.0
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    return df


# ── KRX-INDEX:XXXX 형식 지수 시세 ──

def collect_krx_index(symbol: str, start: str, end: str | None = None) -> pd.DataFrame:
    """
    KRX 지수 시세 수집

    Args:
        symbol: 'KRX-INDEX:1001' 형식
        start: 시작일
        end: 종료일
    """
    code = symbol.split(":")[1]  # '1001'
    idx1, idx2 = code[0], code[1:]
    from_dt = pd.to_datetime(start)
    to_dt = pd.to_datetime(end) if end else pd.Timestamp.today().to_pydatetime()
    logger.info("krx_index: symbol=%s (%s/%s), %s ~ %s", symbol, idx1, idx2, from_dt.date(), to_dt.date())

    df_list: list[pd.DataFrame] = []
    _start = from_dt
    while True:
        _end = datetime(_start.year + 2, _start.month, _start.day) - timedelta(days=1)
        df = _krx_index_price_2years(idx1, idx2, _start, min(_end, to_dt))
        df_list.append(df)
        if to_dt <= _end:
            break
        _start = _end + timedelta(days=1)

    df = pd.concat(df_list, ignore_index=True)
    if df.empty:
        logger.warning("krx_index/%s: 데이터 없음", symbol)
        return df

    col_map = {
        "TRD_DD": "Date", "CLSPRC_IDX": "Close", "FLUC_TP_CD": "UpDown",
        "PRV_DD_CMPR": "Comp", "UPDN_RATE": "Change",
        "OPNPRC_IDX": "Open", "HGPRC_IDX": "High", "LWPRC_IDX": "Low",
        "ACC_TRDVOL": "Volume", "ACC_TRDVAL": "Amount", "MKTCAP": "MarCap",
    }
    df = df.rename(columns=col_map)
    num_cols = [c for c in ["Close", "Comp", "Change", "Open", "High", "Low", "Volume", "Amount", "MarCap"] if c in df.columns]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", ""), errors="coerce")
    if "Change" in df.columns:
        df["Change"] = df["Change"] / 100.0
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    return df




# ════════════════════════════════════════════════════════════════
#  4. SnapDataReader 계열 (snap/)
# ════════════════════════════════════════════════════════════════

def _krx_last_working_day(dt: date | None = None) -> datetime:
    """지정한 날짜에서 가장 가까운 영업일"""
    date_val = pd.to_datetime(dt) if dt else pd.Timestamp.today()
    date_str = date_val.strftime("%Y%m%d")
    url = (
        "http://data.krx.co.kr/comm/bldAttendant/executeForResourceBundle.cmd"
        f"?baseName=krx.mdc.i18n.component&key=B161.bld&inDate={date_str}"
    )
    r = session.get(url, timeout=15)
    j = r.json()
    return pd.to_datetime(j["result"]["output"][0]["bis_work_dt"]).to_pydatetime()


def _krx_index_listings(idx1: str, idx2: str, dt: date | None = None) -> pd.DataFrame:
    """
    지수 구성종목 데이터 수집

    Args:
        idx1: full index code (예: '1')
        idx2: short index code (예: '001')
        dt: 기준일
    """
    end = _krx_last_working_day(dt)
    url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
    form_data = {
        "bld": "dbms/MDC/STAT/standard/MDCSTAT00601",
        "indIdx": idx1,
        "indIdx2": idx2,
        "param1indIdx_finder_equidx0_1": "",
        "trdDd": end.strftime("%Y%m%d"),
        "money": "1",
        "csvxls_isNo": "false",
    }
    r = session.post(url, data=form_data, timeout=30)
    j = r.json()
    df = pd.DataFrame(j["output"])

    cols_map = {
        "ISU_SRT_CD": "Code", "ISU_ABBRV": "Name",
        "TDD_CLSPRC": "Close", "FLUC_TP_CD": "RateCode",
        "CMPPREVDD_PRC": "ComparedRate", "FLUC_RT": "Rate",
        "MKTCAP": "Marcap",
    }

    if df.empty:
        logger.warning("snap_index_listings: 데이터 없음")
        return pd.DataFrame(columns=cols_map.values())

    df = df.replace(r",", "", regex=True)
    numeric_cols = ["TDD_CLSPRC", "STR_CMP_PRC", "FLUC_RT", "MKTCAP"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    df = df.rename(columns=cols_map)
    return df


def collect_snap(ticker: str) -> pd.DataFrame:
    """
    스냅 데이터 수집

    Args:
        ticker: 'KRX/INDEX/STOCK/1001' 형식
    """
    logger.info("snap: ticker=%s", ticker)

    if ticker.startswith("KRX/INDEX/STOCK/"):
        code = ticker.split("/")[-1]
        df = _krx_index_listings(code[0], code[1:])
        return df
    else:
        raise NotImplementedError(f'"{ticker}" is not implemented')

        
def collect_index_list() -> pd.DataFrame:
    """
    [11006] 지수목록 조회 (index_list)
    """
    url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
    form_data = {
        "locale": "ko_KR",
        "mktsel": "1",
        "searchText": "",
        "bld": "dbms/comm/finder/finder_equidx",
    }
    logger.info("index_list: fetching index codes")
    r = session.post(url, data=form_data, timeout=30)
    j = r.json()
    df = pd.DataFrame(j["block1"])
    df = df.sort_values(["full_code", "short_code"])
    df = df.reset_index(drop=True)
    return df
