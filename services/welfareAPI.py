from dotenv import load_dotenv
import os
import requests
import urllib.parse
from services.welfareparser import parse_and_format_cards

# .env 파일 로드
load_dotenv()
SERVICE_KEY = os.getenv("DATA_service_key")

def fetch_welfare_info(
    city: str
):
    # 매핑
    life_code = '005'
    srchKeyCode = "003"  # 서비스명+내용

    # URL 생성
    url = (
        f"http://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations/LcgvWelfarelist"
        f"?serviceKey={SERVICE_KEY}"
        f"&pageNo=1"
        f"&numOfRows=15"
        f"&lifeArray={life_code}"
        f"&srchKeyCode={srchKeyCode}"
        f"&ctpvNm={city}"
    )

    #API 요청
    response = requests.get(url)
    raw_info = response.text

    cards = parse_and_format_cards(raw_info)

    return cards


