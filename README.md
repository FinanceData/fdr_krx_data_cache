# FDR KRX Data Cache
KRX(한국거래소) 데이터를 자동 수집하여 Git에 CSV로 저장하는 시스템

## 프로젝트 구조

```
fdr_krx_data_cache/
├── .github/workflows/
│   └── collect.yml        # GitHub Actions 자동 수집 워크플로우
├── data/                  # 수집된 CSV 데이터 (자동 생성)
│   ├── listing/           # 종목 시세 및 정보
│   │   ├── krx/           # KRX 종목 시세
│   │   ├── kosdaq/        # KOSDAQ 종목 시세
│   │   ├── delisting/     # 상장폐지 종목 목록
│   │   └── desc/          # 기업 상세 정보 (업종, 상장일, 대표자 등)
│   ├── index/             # 지수 시세
│   │   ├── ks11/          # KOSPI 지수 (일별)
│   │   ├── year_ks11/     # KOSPI 지수 (연도별 누적)
│   │   ├── year_ks200/    # KOSPI 200 (연도별 누적)
│   │   └── ...
│   └── snap/              # 스냅샷 데이터 (지수구성종목 등)
├── collectors.py          # 데이터 수집 함수 (STAT/KIND API 활용)
├── config.py              # 설정 및 상수
├── krx_auth.py            # KRX 로그인/인증
├── main.py                # 메인 실행 스크립트
└── storage.py             # CSV 저장 유틸리티 (일별/연도별 분할 저장)
```

## 사용법

### 로컬 실행

```bash
# 전체 수집 (오늘 데이터 및 부족한 연도별 히스토리)
uv run python main.py

# 특정 카테고리만 수집
uv run python main.py --only listing     # 종목/상세정보
uv run python main.py --only index       # 지수 시세 (일별)
uv run python main.py --only snap        # 스냅샷 (지수구성종목)
uv run python main.py --only kq-yearly   # 지수 연도별 누적 데이터 (히스토리)

# 기간별 수집 (index 카테고리 권장)
# 시작일~종료일 데이터를 수집하여 각 일자별 파일로 자동 분할 저장합니다.
uv run python main.py --only index --start 2024-01-01 --end 2024-01-31
```

### GitHub Actions 자동 실행
- **스케줄**: 평일(월 ~ 금) KST 09:00 ~ 17:55, 5분 간격 자동 실행
- **수동 실행**: Actions 탭 → `KRX Data Collection` → `Run workflow`

## ⚙️ GitHub Secrets 설정
리포지토리 Settings → Secrets and variables → Actions에 다음을 등록:

| Secret  | 설명            |
|---------|----------------|
| `KRX_ID`| KRX 로그인 ID   |
| `KRX_PW`| KRX 로그인 비밀번호 |

## 수집 데이터

| 카테고리 | 소분류 (sub) | 설명 | 데이터 경로 |
| :--- | :--- | :--- | :--- |
| **listing** | `krx` | KRX 전체 종목 시세 | `data/listing/krx/` |
| **listing** | `kosdaq` | KOSDAQ 종목 시세 | `data/listing/kosdaq/` |
| **listing** | `delisting` | 상장폐지 종목 목록 | `data/listing/delisting/` |
| **listing** | `desc` | 기업 상세 정보 (Sector, Industry, ListingDate 등) | `data/listing/desc/` |
| **index** | `ks11`, `kq11` 등 | 주요 지수 일별 시세 | `data/index/{symbol}/` |
| **index** | `year_ks11` 등 | 주요 지수 연도별 누적 시세 | `data/index/year_{symbol}/` |
| **snap** | `index_list` | KRX 전체 지수 목록 | `data/snap/index_list/` |
| **snap** | `index_stock_1001`| 지수 구성 종목 스냅샷 | `data/snap/index_stock_1001/` |

- **효율적 수집**: 이미 수집된 과거 일자/연도 데이터는 자동으로 건너뛰어 API 호출을 최소화합니다.
- **데이터 정제**: KRX STAT API와 KIND 데이터를 병합하여 `FinanceDataReader` 보다 상세한 기업 정보를 제공합니다.

## 개발

```bash
# 의존성 설치
uv sync

# Python 버전
python 3.13+
```

