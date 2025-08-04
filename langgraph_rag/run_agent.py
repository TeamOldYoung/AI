import os
from dotenv import load_dotenv

from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import HumanMessage, SystemMessage
from langchain.chains.combine_documents import StuffDocumentsChain
from langchain.prompts import PromptTemplate

from langgraph.graph import StateGraph, END

# Load .env
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")

# LangChain components
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3, openai_api_key=openai_key)
embedding_model = OpenAIEmbeddings(openai_api_key=openai_key)
vectorstore = FAISS.load_local("vectorstore", embedding_model)

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# Prompt for combining documents
combine_prompt = PromptTemplate.from_template("""
당신은 친절한 한국어 상담 AI입니다.
아래 문서를 참고하여 사용자의 질문에 정확하고 자세하게 대답해주세요.

문서:
{context}

질문:
{question}
""")

rag_chain = StuffDocumentsChain(
    llm_chain=llm,
    document_prompt=combine_prompt,
    document_variable_name="context"
)

### 1. 상태 정의
class RAGState(dict):
    pass

### 2. 노드 함수 정의

def retrieve_node(state: RAGState):
    query = state["question"]
    docs = retriever.get_relevant_documents(query)
    state["docs"] = docs
    return state

def answer_node(state: RAGState):
    question = state["question"]
    docs = state["docs"]
    response = rag_chain.run({"context": docs, "question": question})
    state["answer"] = response
    return state

### 3. 그래프 정의
graph_builder = StateGraph(RAGState)

graph_builder.add_node("retrieve", retrieve_node)
graph_builder.add_node("answer", answer_node)

graph_builder.set_entry_point("retrieve")
graph_builder.add_edge("retrieve", "answer")
graph_builder.add_edge("answer", END)

graph = graph_builder.compile()

### 4. 실행 예시
def ask_question(question: str):
    result = graph.invoke({"question": question})
    return result["answer"]

if __name__ == "__main__":
    print(" 질문을 입력하세요. (종료: 엔터만 입력)")
    while True:
        q = input("Q: ")
        if q.strip() == "":
            break
        answer = ask_question(q)
        print(f"A: {answer}\n")
