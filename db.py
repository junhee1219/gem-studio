import psycopg2
from settings import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_DATABASE

def get_db_conn():
    """FastAPI 의존성 함수: 각 요청에 대한 psycopg2 DB 연결을 관리합니다."""
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_DATABASE,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()