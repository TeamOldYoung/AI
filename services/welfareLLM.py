from langchain_community.tools import DuckDuckGoSearchRun
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# DuckDuckGo 검색 도구 초기화
search = DuckDuckGoSearchRun()

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
SERVICE_KEY = os.getenv("DATA_service_key")

# LLM 초기화
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)


# 시스템 프롬프트
def load_income_prompt() -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompt", "welfareprompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def summarize_welfare_info(
    life: str,
    trgter: str,
    theme: str,
    age: int,
    city: str,
    district: str,
    keyword: str = "",
    sort: str = "인기순"
):
    """
    LangChain 기반: 지역 복지 정보를 DuckDuckGo로 검색하고 요약
    """
    system_prompt = load_income_prompt()

    #query = f"{region} 복지 혜택 지원 사업"

    try:
        # # 1. DuckDuckGo 검색 결과 (구조화된 형태)
        # results = search.invoke(query)
        #
        # if not results or len(results) == 0:
        #     return f"{region} 관련 복지 정보를 찾지 못했습니다."
        #
        # print(results)

        # 매핑
        life_code = life_map.get(life, "")
        trgter_code = trgter_map.get(trgter, "")
        theme_code = theme_map.get(theme, "")
        srchKeyCode = "003"  # 서비스명+내용
        arrgOrd = "002" if sort == "인기순" else "001"

        # 검색어 인코딩
        searchWrd = urllib.parse.quote(keyword)

        # URL 생성
        url = (
            f"http://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations/LcgvWelfarelist"
            f"?serviceKey={SERVICE_KEY}"
            f"&pageNo=1"
            f"&numOfRows=100"
            f"&lifeArray={life_code}"
            f"&trgterIndvdlArray={trgter_code}"
            f"&intrsThemaArray={theme_code}"
            # f"&age={age}"
            # f"&ctpvNm={urllib.parse.quote(city)}"
            # f"&sggNm={urllib.parse.quote(district)}"
            f"&srchKeyCode={srchKeyCode}"
            # f"&searchWrd={searchWrd}"
            # f"&arrgOrd={arrgOrd}"
        )

        # API 요청
        response = requests.get(url)
        print("✅ 응답 상태코드:", response.status_code)
        print("📦 응답 내용 (앞부분):\n", response.text)

        return response.text  # 향후 XML 파싱 시 사용


        # # 3. LLM 요약 프롬프트
        # prompt = system_prompt
        #
        # response = llm.invoke(prompt)
        # return response.content.strip()

    except Exception as e:
        return f"[오류] 처리 중 문제가 발생했습니다: {e}"


if __name__ == "__main__":
    print(summarize_welfare_info('''경기도 성남시 분당구'''))