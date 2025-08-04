from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader

import os
from dotenv import load_dotenv


# .env 파일에서 API 키 로드
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")


# 텍스트 문서가 있는 폴더 경로
text_folder = "../data"

# 1. 폴더 내 모든 .txt 파일 불러오기
all_documents = []
for filename in os.listdir(text_folder):
    if filename.endswith(".txt"):
        file_path = os.path.join(text_folder, filename)
        loader = TextLoader(file_path, encoding="utf-8")
        loaded_docs = loader.load()
        all_documents.extend(loaded_docs)

print(f" 총 {len(all_documents)}개의 문서를 로드했습니다.")

# 2. 텍스트 분할
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
split_docs = text_splitter.split_documents(all_documents)

print(f" 총 {len(split_docs)}개의 chunk로 분할했습니다.")

# 3. 임베딩 생성
embedding_model = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(split_docs, embedding_model)

# 4. 저장
vectorstore.save_local("../vectorstore/law_and_welfare")

print(" Vectorstore 저장 완료")
