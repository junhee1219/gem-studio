import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv
from fastapi.responses import FileResponse

# .env 파일에서 환경 변수 로드
load_dotenv()

# FastAPI 앱 초기화
app = FastAPI()

# Supabase 클라이언트 설정
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# 요청 본문을 위한 Pydantic 모델 정의
class UserCreate(BaseModel):
    email: str
    password: str
    nickname: str

@app.get("/signup")
def get_signup_page():
    return FileResponse('pages/sign_up.html')

# 회원가입 API 엔드포인트
@app.post("/signup")
def sign_up(user: UserCreate):
    """
    Supabase를 사용하여 새로운 사용자를 등록하고 확인 이메일을 보냅니다.
    """
    try:
        res = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {
                "data": {
                    "nickname": user.nickname
                }
            }
        })

        if res.user:
            supabase.from_('profiles').insert({
                "auth_user_id": str(res.user.id),
                "nickname": user.nickname
            }).execute()
            return {"message": f"회원가입 성공! {user.email}로 인증 메일을 확인해주세요."}
        else:
            raise HTTPException(status_code=400, detail="회원가입에 실패했습니다.")

    except Exception as e:
        error_message = str(e)
        if "User already registered" in error_message:
            raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
        raise HTTPException(status_code=500, detail=f"서버 오류: {error_message}")

# uvicorn main:app --reload