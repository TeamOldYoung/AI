import json
import re
from typing import Any, Dict
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

def _extract_json(text: str) -> Dict[str, Any]:
    """
    모델이 앞뒤로 설명을 붙였거나 ```json 코드펜스가 섞여도
    최대한 안전하게 JSON만 추출해서 dict로 반환.
    실패 시 ValueError 발생.
    """
    s = text.strip()

    # 1) 코드펜스 제거
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.IGNORECASE | re.MULTILINE).strip()

    # 2) 바로 시도
    try:
        return json.loads(s)
    except Exception:
        pass

    # 3) 본문 중 가장 바깥쪽 중괄호 블록 추출
    #    (간단한 스택 방식으로 첫 '{' ~ 매칭 '}' 구간을 잡음)
    start = s.find("{")
    if start == -1:
        raise ValueError("No JSON object found.")
    depth = 0
    end = -1
    for i, ch in enumerate(s[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end == -1:
        raise ValueError("Unbalanced JSON braces.")
    candidate = s[start:end]
    return json.loads(candidate)

def estimate_income_bracket(
    familyNum: int,
    Salary: int,
    Pension: int,
    housing_type: str,
    Asset: int,
    Debt: int,
    Car_info: str,
    Disability: bool,
    EmploymentStatus: str,
    pastSupported: bool
) -> str:
    """
    사용자의 재정 상황을 구조화된 입력으로 받아 GPT로 소득분위 추정을 요청하는 함수
    """
    try:
        # 1. system prompt 불러오기
        system_prompt = load_income_prompt()

        # 2. 관련 문서 검색
        query = (
            f"{familyNum}인 가구 기준 중위소득 "
            f"소득인정액 계산 방법 "
            f"소득 분위 구간표 "
            f"소득환산액 공식 "
            f"{housing_type} 거주 공제 기준"
        )
        relevant_docs = retriever.invoke(query)
        retrieved_text = "\n\n".join([doc.page_content for doc in relevant_docs])


        user_profile = (
            f"- 가구원 수: {familyNum}명\n"
            f"- 연소득(세전): {Salary:,.0f}원\n"
            f"- 소득 유형: {Pension}\n"
            f"- 주거 형태: {housing_type}\n"
            f"- 금융 및 부동산 자산: {Asset:,.0f}원\n"
            f"- 부채: {Debt:,.0f}원\n"
            f"- 차량 정보: {Car_info}\n"
            f"- 장애 여부: {'있음' if Disability else '없음'}\n"
            f"- 취업 상태: {EmploymentStatus}\n"
            f"- 연금 수령 여부: {'예' if Pension > 0 else '아니오'}\n"
            f"- 과거 복지 수급 이력: {'있음' if pastSupported else '없음'}"
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
        raw_text = response.content.strip()

        parsed = _extract_json(raw_text)
        return parsed


    except Exception as e:
        return f"[오류] LangChain GPT 처리 중 문제가 발생했습니다: {e}"

if __name__ == "__main__":
    result = estimate_income_bracket(
    familyNum=3,
    Salary=20000000,
    Pension=4000000,
    housing_type="전세",
    Asset=60000000,
    Debt=10000000,
    Car_info="준중형차, 2019년식",
    Disability=False,
    EmploymentStatus="취업",
    pastSupported=False,
    )

    # for _ in range(10):
    print(result)


