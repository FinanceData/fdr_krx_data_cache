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
    KRX data.krx.co.kr 로그인 후 세션 쿠키(JSESSIONID)를 갱신합니다.

    로그인 흐름:
      1. GET MDCCOMS001.cmd  → 초기 JSESSIONID 발급
      2. GET login.jsp       → iframe 세션 초기화
      3. POST MDCCOMS001D1.cmd → 실제 로그인
      4. CD011(중복 로그인) → skipDup=Y 추가 후 재전송

    Returns:
        True: 로그인 성공, False: 로그인 실패
    """
    try:
        # 초기 세션 발급
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
            logger.info("KRX 로그인 성공")
            return True
        else:
            logger.error("KRX 로그인 실패: error_code=%s", error_code)
            return False

    except Exception as e:
        logger.error("KRX 로그인 중 예외 발생: %s", e)
        return False
