from fastapi import APIRouter, HTTPException, Response, Depends, Cookie
from fastapi import Request
from models.user import UserCreate, UserLogin
from settings import supabase
from common.templates import templates
from session_store import session_store
from common.security import get_current_user
from db import get_db_conn

router = APIRouter(tags=["auth"])


@router.get("/signup")
def get_signup_page():
    return templates.TemplateResponse("sign_up.html")


@router.post("/signup")
def sign_up(user: UserCreate, conn = Depends(get_db_conn)):
    try:
        with conn.cursor() as cur:
            # 1. 먼저 DB에 해당 이메일로 가입된 프로필이 있는지 확인 (SQL 인젝션 방지)
            cur.execute("SELECT email FROM profiles WHERE email = %s", (user.email,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

        # 2. Supabase Auth 서비스에 사용자 생성 요청
        auth_res = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {"data": {"nickname": user.nickname}}
        })
        
        if not auth_res.user:
             raise HTTPException(status_code=500, detail="Supabase Auth에서 사용자 생성에 실패했습니다.")

        # 3. FastAPI 앱에서 DB에 직접 프로필 정보 저장 (SQL 인젝션 방지)
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO profiles (auth_user_id, nickname, email) VALUES (%s, %s, %s)",
                (str(auth_res.user.id), user.nickname, user.email)
            )
        # get_db_conn 의존성에서 conn.commit()이 호출되어 트랜잭션이 완료됩니다.

        return {"message": f"회원가입 성공! {user.email}로 인증 메일을 확인해주세요."}

    except HTTPException as http_exc:
        raise http_exc # 이미 처리된 HTTP 예외는 다시 발생시킴
    except Exception as e:
        # DB 오류 또는 Supabase 오류가 발생하면 get_db_conn 의존성에서 conn.rollback()이 호출됩니다.
        raise HTTPException(status_code=500, detail=f"회원가입 처리 중 오류 발생: {str(e)}")


@router.get("/login")
def get_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(user: UserLogin, response: Response):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })

        if getattr(res, "user", None) and getattr(res, "session", None):
            session_id = session_store.create({"user_id": str(res.user.id), "email": res.user.email})
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                samesite="lax",
                secure=False
            )
            return {"message": "로그인 성공!"}
        else:
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.post("/logout")
def logout(response: Response, session_id: str | None = Cookie(None)):
    if session_id:
        session_store.delete(session_id)
    response.delete_cookie("session_id")
    return {"message": "로그아웃 되었습니다."}

@router.get("/users/me", summary="Get current user info")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user
