# database/db.py
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    host = os.getenv("PG_HOST", "127.0.0.1")
    port = int(os.getenv("PG_PORT", "5432"))
    db   = os.getenv("PG_DB", "postgres")
    user = os.getenv("PG_USER", "postgres")
    pwd  = os.getenv("PG_PASSWORD", "")
    sslmode = os.getenv("PG_SSLMODE", "disable")

    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=db,
        user=user,
        password=pwd,
        sslmode=sslmode,
        connect_timeout=int(os.getenv("PG_CONNECT_TIMEOUT", "5")),
        keepalives=1,
        keepalives_idle=int(os.getenv("PG_KEEPALIVES_IDLE", "30")),
        keepalives_interval=int(os.getenv("PG_KEEPALIVES_INTERVAL", "10")),
        keepalives_count=int(os.getenv("PG_KEEPALIVES_COUNT", "5")),
    )
    # 윈도우 콘솔 한글 깨짐 방지
    conn.set_client_encoding("UTF8")
    return conn
