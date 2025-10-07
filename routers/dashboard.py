from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from common.security import try_get_current_user
from common.templates import templates
from settings import supabase

router = APIRouter()

@router.get("/")
def get_dashboard(request: Request, user: dict | None = Depends(try_get_current_user)):
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # 세션에서 user_id를 가져와 profiles 테이블에서 닉네임을 조회합니다.
    user_id = user.get("user_id")
    try:
        profile_res = supabase.from_("profiles").select("nickname").eq("auth_user_id", user_id).execute()
        if profile_res.data:
            nickname = profile_res.data[0].get("nickname", "사용자")
        else:
            nickname = "사용자" # No profile found
    except Exception as e:
        print(f"Error fetching nickname: {e}") # 서버 로그에 오류 기록
        nickname = "사용자" # 오류 발생 시 기본값

    # --- 임시 데이터 (나중에 실제 DB와 연동 필요) ---
    pending_items = [
        {"title": "요청사항 #123 처리"},
        {"title": "프로필 사진 업데이트"},
        {"title": "결제 정보 확인"},
    ]
    completed_albums = [
        {"title": "가족 여행 앨범"},
        {"title": "2024년 여름"},
    ]
    # -------------------------------------------------

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "nickname": nickname,
            "pending_items": pending_items,
            "completed_albums": completed_albums,
        },
    )
