"""
KRX data.krx.co.kr 로그인 및 인증 세션 관리
"""
import logging
import requests

from config import KRX_HEADERS, KRX_ID, KRX_PW

logger = logging.getLogger(__name__)

# 모듈 레벨 세션 (로그인 후 재사용)
session = requests.Session()
session.headers.update(KRX_HEADERS)

_LOGIN_PAGE = "https://data.krx.co.kr/contents/MDC/COMS/client/MDCCOMS001.cmd"
_LOGIN_JSP = "https://data.krx.co.kr/contents/MDC/COMS/client/view/login.jsp?site=mdc"
_LOGIN_URL = "https://data.krx.co.kr/contents/MDC/COMS/client/MDCCOMS001D1.cmd"


def login(login_id: str = KRX_ID, login_pw: str = KRX_PW) -> bool:
    """
    KRX data.krx.co.kr 세션 초기화 및 로그인

    인증 흐름:
      1. 세션 기본 초기화 (B128.bld resource bundle 호출로 쿠키 발급)
      2. 만약 ID/PW가 'id'/'pw'(기본값)이거나 빈 값이면 익명 세션으로 간주하고 성공 반환
      3. 유효한 ID/PW가 있다면 실제 로그인 과정 수행
    """
    try:
        # 1. 세션 기본 초기화 (Cookie 발급)
        # 이 단계만으로도 많은 공용 API (Finder 등) 사용 가능
        init_url = (
            "http://data.krx.co.kr/comm/bldAttendant/executeForResourceBundle.cmd"
            "?baseName=krx.mdc.i18n.component&key=B128.bld"
        )
        session.get(init_url, timeout=15)
        
        # 2. 익명 세션 체크
        if login_id in [None, "", "id"] or login_pw in [None, "", "pw"]:
            logger.info("KRX 익명 세션 초기화 완료")
            return True

        # 3. 실제 로그인 수행
        logger.info("KRX 회원 로그인 시도: %s", login_id)
        session.get(_LOGIN_PAGE, timeout=15)
        session.get(_LOGIN_JSP, headers={"Referer": _LOGIN_PAGE}, timeout=15)

        payload = {
            "mbrNm": "",
            "telNo": "",
            "di": "",
            "certType": "",
            "mbrId": login_id,
            "pw": login_pw,
        }

        # 로그인 POST
        resp = session.post(
            _LOGIN_URL,
            data=payload,
            headers={"Referer": _LOGIN_PAGE},
            timeout=15,
        )
        data = resp.json()
        error_code = data.get("_error_code", "")

        # CD011 중복 로그인 처리
        if error_code == "CD011":
            logger.info("중복 로그인 감지 → skipDup=Y 재시도")
            payload["skipDup"] = "Y"
            resp = session.post(
                _LOGIN_URL,
                data=payload,
                headers={"Referer": _LOGIN_PAGE},
                timeout=15,
            )
            data = resp.json()
            error_code = data.get("_error_code", "")

        if error_code == "CD001":
            logger.info("KRX 회원 로그인 성공")
            return True
        else:
            logger.warning("KRX 회원 로그인 실패 (error_code=%s). 익명 세션으로 계속 진행합니다.", error_code)
            # 로그인은 실패했지만, 위에서 쿠키는 받았으므로 공용 데이터 수집은 가능할 수 있음
            return True

    except Exception as e:
        logger.error("KRX 인증 중 예외 발생: %s", e)
        # 예외 발생 시에도 세션 초기화는 시도한 것이므로 True를 반환하여 
        # 수집기들이 수집을 시도해볼 수 있게 함 (KIND 등은 개별적으로 작동함)
        return True
