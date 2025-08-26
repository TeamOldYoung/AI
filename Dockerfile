# 빌드
FROM python:3.11-slim AS builder

WORKDIR /app

# 시스템 패키지 설치 (빌드용)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# pip 업그레이드 및 캐시 최적화
RUN pip install --no-cache-dir --upgrade pip

# requirements.txt 먼저 복사 → 캐시 최적화
COPY requirements.txt .

# 의존성 캐싱
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

# 실행
FROM python:3.11-slim

WORKDIR /app

# builder 단계에서 설치된 패키지 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 애플리케이션 코드 복사
COPY --from=builder /app .

# Python 환경 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# 비루트 사용자 생성 및 권한 설정
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Flask 포트 3000으로 변경 (app.py에서 설정)
EXPOSE 3000

# 애플리케이션 실행
ENTRYPOINT ["python", "app.py"]