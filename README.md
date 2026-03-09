# FDR KRX Data Cache
KRX(한국거래소) 데이터를 자동 수집하여 Git에 CSV로 저장하는 시스템입니다.

## 📁 프로젝트 구조

```
fdr_krx_data_cache/
├── .github/workflows/
│   └── collect.yml        # GitHub Actions 자동 수집 워크플로우
├── data/                  # 수집된 CSV 데이터 (자동 생성)
│   ├── listing/           # 종목 시세 (KRX, KOSDAQ, 상장폐지)
│   ├── index/             # 지수 시세 (KS11, KQ11, KS200, KRX-INDEX)
│   └── snap/              # 스냅샷 데이터
├── refs/                  # 참고 자료 (변경 금지)
├── collectors.py          # 데이터 수집 함수
├── config.py              # 설정 및 상수
├── krx_auth.py            # KRX 로그인/인증
├── main.py                # 메인 실행 스크립트
└── storage.py             # CSV 저장 유틸리티
```

## 🚀 사용법

### 로컬 실행

```bash
# 전체 수집 (오늘 데이터)
uv run python main.py

# 특정 카테고리만 수집
uv run python main.py --only listing
uv run python main.py --only index
uv run python main.py --only snap

# 기간별 수집 (index 카테고리 권장)
# 시작일~종료일 데이터를 수집하여 각 일자별 파일로 자동 분할 저장합니다.
uv run python main.py --only index --start 2024-01-01 --end 2024-01-31
```

### GitHub Actions 자동 실행

- **스케줄**: 평일(월~금) KST 09:00~17:55, 5분 간격 자동 실행
- **수동 실행**: Actions 탭 → `KRX Data Collection` → `Run workflow`

## ⚙️ GitHub Secrets 설정

리포지토리 Settings → Secrets and variables → Actions에 다음을 등록하세요:

| Secret  | 설명            |
|---------|----------------|
| `KRX_ID`| KRX 로그인 ID   |
| `KRX_PW`| KRX 로그인 비밀번호 |

## 📊 수집 데이터

| 카테고리     | 소스                    | 데이터 경로             |
|------------|------------------------|----------------------|
| **listing** | `StockListing('KRX')`   | `data/listing/krx/`  |
| **listing** | `StockListing('KOSDAQ')`| `data/listing/kosdaq/`|
| **listing** | `StockListing('KRX-DELISTING')` | `data/listing/delisting/` |
| **index**   | `DataReader('KS11')` 등 | `data/index/ks11/` 등 |
| **index**   | `DataReader('KRX-INDEX:1001')` | `data/index/krx_index_1001/` |
| **snap**    | `SnapDataReader('KRX/INDEX/STOCK/1001')` | `data/snap/index_stock_1001/` |

각 파일은 `data/{카테고리}/{소분류}/{YYYY-MM-DD}.csv` 형식으로 저장됩니다.

## 🔧 개발

```bash
# 의존성 설치
uv sync

# Python 버전
python 3.13+
```
