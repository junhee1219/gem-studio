import os
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Supabase API Client (for Auth)
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Direct Database Connection (psycopg2)
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_DATABASE = os.environ.get("DB_DATABASE")

# 모든 변수가 있는지 확인
if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_DATABASE]):
    raise ValueError("데이터베이스 연결을 위한 모든 환경변수(.env)가 설정되지 않았습니다.")

# File Path Settings
PAGES_DIR = Path(__file__).resolve().parent / "pages"