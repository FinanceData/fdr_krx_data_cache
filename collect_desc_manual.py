"""
KRX-DESC 독립 수집 스크립트
krx_auth 세션을 사용하여 data.krx.co.kr API 기반으로 수집
data/listing/desc/yyyy-mm-dd.csv 로 저장
"""
import io
import json
import ssl
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Referer': 'https://data.krx.co.kr/contents/MDC/MDI/outerLoader/index.cmd'
}
DATA_DIR = Path(__file__).parent / "data" / "listing" / "desc"
URL_API = 'http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd'


def collect_and_save():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ── 0. 최신 거래일 ──
    print("[0/5] 최신 거래일 조회...", flush=True)
    url_b128 = (
        "http://data.krx.co.kr/comm/bldAttendant/executeForResourceBundle.cmd"
        "?baseName=krx.mdc.i18n.component&key=B128.bld"
    )
    r = requests.get(url_b128, headers=HEADERS, timeout=15)
    trade_date = r.json()["result"]["output"][0]["max_work_dt"]
    print(f"    최신 거래일: {trade_date}", flush=True)

    # ── 1. Finder API ──
    print("[1/5] Finder API 호출 중...", flush=True)
    r = requests.post(URL_API, data={'bld': 'dbms/comm/finder/finder_stkisu'},
                      headers=HEADERS, timeout=15)
    df_finder = pd.DataFrame(r.json().get('block1', []))
    if df_finder.empty:
        print("ERROR: Finder 데이터 없음", flush=True)
        return
    df_finder = df_finder.rename(columns={
        'full_code': 'FullCode', 'short_code': 'Code', 'codeName': 'Name',
        'marketEngName': 'Market',
    })
    print(f"    Finder: {len(df_finder)}건", flush=True)

    # ── 2. STAT API (MDCSTAT01501 - 전종목 시세) ──
    print("[2/5] STAT API (전종목 시세) 호출 중...", flush=True)
    stat_data = {
        'bld': 'dbms/MDC/STAT/standard/MDCSTAT01501',
        'mktId': 'ALL', 'trdDd': trade_date,
        'share': '1', 'money': '1', 'csvxls_isNo': 'false',
    }
    r = requests.post(URL_API, data=stat_data, headers=HEADERS, timeout=15)
    df_stat = pd.DataFrame(r.json().get('OutBlock_1', []))
    df_detail = None
    if not df_stat.empty:
        df_stat = df_stat.rename(columns={
            'ISU_SRT_CD': 'Code', 'SECT_TP_NM': 'Sector',
        })
        df_detail = df_stat[['Code', 'Sector']].copy()
        print(f"    STAT: {len(df_detail)}건", flush=True)
    else:
        print("    STAT: 데이터 없음", flush=True)

    # ── 3. KIND (optional) ──
    df_kind = None
    try:
        print("[3/5] KIND 호출 중 (timeout=10s)...", flush=True)
        ssl._create_default_https_context = ssl._create_unverified_context
        url_kind = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
        r = requests.get(url_kind, headers={
            'User-Agent': 'Chrome/78.0.3904.87 Safari/537.36',
            'Referer': 'https://data.krx.co.kr/contents/MDC/MDI/outerLoader/index.cmd'
        }, timeout=10)
        dfs = pd.read_html(io.StringIO(r.text), header=0)
        df_kind = dfs[0]
        df_kind = df_kind.rename(columns={
            '회사명': 'Name', '종목코드': 'Code', '업종': 'Industry',
            '주요제품': 'Products', '상장일': 'ListingDate', '결산월': 'SettleMonth',
            '대표자명': 'Representative', '홈페이지': 'HomePage', '지역': 'Region',
        })
        df_kind['Code'] = df_kind['Code'].astype(str).str.zfill(6)
        df_kind['ListingDate'] = pd.to_datetime(df_kind['ListingDate'], errors='coerce')
        df_kind = df_kind[['Code', 'Industry', 'Products', 'ListingDate',
                           'SettleMonth', 'Representative', 'HomePage', 'Region']]
        print(f"    KIND: {len(df_kind)}건", flush=True)
    except Exception as e:
        print(f"    KIND 실패: {e} (무시하고 계속)", flush=True)

    # ── 4. 병합 ──
    print("[4/5] 데이터 병합 중...", flush=True)
    merged = df_finder[['Code', 'Name', 'Market']].copy()

    if df_detail is not None:
        merged = pd.merge(merged, df_detail, how='left', on='Code')
    else:
        merged['Sector'] = None

    if df_kind is not None:
        merged = pd.merge(merged, df_kind, how='left', on='Code')
    else:
        for col in ['Industry', 'Products', 'ListingDate', 'SettleMonth',
                     'Representative', 'HomePage', 'Region']:
            merged[col] = None

    merged = merged.drop_duplicates(subset='Code').reset_index(drop=True)

    # ── 5. 저장 ──
    today = date.today()
    path = DATA_DIR / f"{today.isoformat()}.csv"
    merged.to_csv(path, index=True, encoding='utf-8-sig')
    print(f"[5/5] 저장 완료: {path} ({len(merged)}건)", flush=True)


if __name__ == "__main__":
    collect_and_save()
