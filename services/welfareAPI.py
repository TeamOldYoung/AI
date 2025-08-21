from dotenv import load_dotenv
import os
import requests
import urllib.parse
from services.welfareparser import parse_and_format_cards
from services.welfareLLM import summarize_welfare_info
from services.welfaredb import save_welfare_item

# .env 파일 로드
load_dotenv()
SERVICE_KEY = os.getenv("DATA_service_key")

def fetch_welfare_info(
    age: bool,
    city: str,
):
    # 매핑
    life_code = '005,006'
    srchKeyCode = "003"  # 서비스명+내용

    if age == 0:
        age_code = '001,002,003,004'  # 0이면 청년
    else:
        age_code = '005,006' # 1이면 장년

    # URL 생성
    url = (
        f"http://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations/LcgvWelfarelist"
        f"?serviceKey={SERVICE_KEY}"
        f"&pageNo=1"
        f"&numOfRows=30"
        f"&lifeArray={life_code}"
        f"&srchKeyCode={srchKeyCode}"
        f"&ctpvNm={city}"
    )

    #API 요청
    response = requests.get(url)
    raw_info = response.text

    cards = parse_and_format_cards(raw_info)
    # if cards == []:
    #     cards = summarize_welfare_info(city)
    #     return cards

    for i in cards:
        save_welfare_item(city, i)

    return f"{len(cards)}의 정보가 등록됨"


