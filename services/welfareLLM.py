from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchRun, DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper


# DuckDuckGo 검색 도구 초기화
wrapper = DuckDuckGoSearchAPIWrapper(
    region="kr-kr",      # 지역 편향 최소화 (예: "kr-kr", "us-en"도 가능)
    safesearch="strict",    # off | moderate | strict
    time="y",            # d | w | m | y (또는 None)
    max_results=50,      # 더 많이 가져오기
    backend="auto",      # api | html | lite | auto
)

# 문자열 하나(요약 스니펫)만 필요하면:
search = DuckDuckGoSearchRun(api_wrapper=wrapper)


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
SERVICE_KEY = os.getenv("DATA_SERVICE_KEY")

# LLM 초기화
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)


# 시스템 프롬프트
def load_income_prompt() -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompt", "welfareprompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def summarize_welfare_info(
    city: str,
):
    """
    LangChain 기반: 지역 복지 정보를 DuckDuckGo로 검색하고 요약
    """
    system_prompt = load_income_prompt()

    query = f"{city} 노인 복지 혜택 지원 사업"

    try:
        # 1. DuckDuckGo 검색 결과 (구조화된 형태)
        results = search.invoke(query)

        if not results or len(results) == 0:
            return f"{region} 관련 복지 정보를 찾지 못했습니다."

        print(results)


        prompt = system_prompt + results

        response = llm.invoke(prompt)
        return response.content.strip()

    except Exception as e:
        return f"[오류] 처리 중 문제가 발생했습니다: {e}"


if __name__ == "__main__":
    print(summarize_welfare_info('''경기도'''))