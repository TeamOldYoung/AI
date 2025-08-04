import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# LLM 초기화
llm = ChatOpenAI(
    temperature=0.3,
    model="gpt-3.5-turbo",
    openai_api_key=openai_api_key
)

# Retriever

base_dir = os.path.dirname(os.path.abspath(__file__))  # 현재 incomeLLM.py 기준
vector_path = os.path.join(base_dir, "..", "vectorstore", "law_and_welfare")
vectorstore = FAISS.load_local(vector_path,
                             OpenAIEmbeddings(),
                             allow_dangerous_deserialization=True)
retriever = vectorstore.as_retriever()


# 시스템 프롬프트
def load_income_prompt() -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompt", "incomeprompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

def estimate_income_bracket(
    household_size: int,
    annual_income: float,
    income_type: str,
    housing_type: str,
    asset_value: float,
    debt_amount: float,
    car_info: str,  # 예: "소형차, 2018년식", "없음"
    has_disability: bool,
    region: str,  # 예: "서울특별시 강남구"
    employment_status: str,  # 예: "실직", "취업", "무직"
    receives_pension: bool,
    past_support_recipient: bool
) -> str:
    """
    사용자의 재정 상황을 구조화된 입력으로 받아 GPT로 소득분위 추정을 요청하는 함수
    """

    try:
        # 1. system prompt 불러오기
        system_prompt = load_income_prompt()

        # 2. 관련 문서 검색
        relevant_docs = retriever.invoke(region)
        retrieved_text = "\n\n".join([doc.page_content for doc in relevant_docs])

        # 3. 입력 정보를 사람이 읽을 수 있는 문장으로 구성
        user_profile = (
            f"- 가구원 수: {household_size}명\n"
            f"- 연소득(세전): {annual_income:,.0f}원\n"
            f"- 소득 유형: {income_type}\n"
            f"- 주거 형태: {housing_type}\n"
            f"- 금융 및 부동산 자산: {asset_value:,.0f}원\n"
            f"- 부채: {debt_amount:,.0f}원\n"
            f"- 차량 정보: {car_info}\n"
            f"- 장애 여부: {'있음' if has_disability else '없음'}\n"
            f"- 지역: {region}\n"
            f"- 취업 상태: {employment_status}\n"
            f"- 연금 수령 여부: {'예' if receives_pension else '아니오'}\n"
            f"- 과거 복지 수급 이력: {'있음' if past_support_recipient else '없음'}"
        )

        # 4. LangChain 메시지 구성
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=(
                f"아래 사용자의 정보를 참고하여 소득분위(1~10분위 중)를 추정해줘.\n\n"
                f"사용자 정보:\n{user_profile}\n\n"
                f"참고 문서:\n{retrieved_text}"
            ))
        ]

        # 5. GPT 응답 생성
        response = llm.invoke(messages)
        return response.content.strip()

    except Exception as e:
        return f"[오류] LangChain GPT 처리 중 문제가 발생했습니다: {e}"

if __name__ == "__main__":
    result = estimate_income_bracket(
        household_size=3,
        annual_income=24000000,
        income_type="근로소득 + 연금소득",
        housing_type="전세",
        asset_value=60000000,
        debt_amount=10000000,
        car_info="준중형차, 2019년식",
        has_disability=False,
        region="서울특별시 마포구",
        employment_status="취업",
        receives_pension=True,
        past_support_recipient=False
    )

    print(result)

