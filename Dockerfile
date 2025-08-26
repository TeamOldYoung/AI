# ===== Builder =====
FROM python:3.11-slim-bookworm AS builder
WORKDIR /app

# 휠만 설치하도록 강제 + 설치 도구 최신화
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ONLY_BINARY=:all: \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 빌드 도구는 생략 가능(휠만 설치할 것이므로) — 필요 시 주석 해제
# RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel

# requirements 캐시 최적화
COPY requirements.txt .
RUN pip install -r requirements.txt

# 소스 복사
COPY . .

# ===== Final =====
FROM python:3.11-slim-bookworm
WORKDIR /app

# 런타임 의존성(lxml/psycopg2-binary 등)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl \
    libxml2 libxslt1.1 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

# builder에서 설치된 패키지/스크립트 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 앱 소스 복사
COPY --from=builder /app .

# 비루트 사용자
RUN groupadd -r appuser && useradd -r -g appuser appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 3000

# 애플리케이션 실행(필요 시 gunicorn으로 교체 가능)
ENTRYPOINT ["python", "app.py"]
