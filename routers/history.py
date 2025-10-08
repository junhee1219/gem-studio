from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
import uuid

from common.security import get_current_user
from common.templates import templates
from db import get_db_conn

router = APIRouter(prefix="/history", tags=["history"])

@router.get("", response_class=HTMLResponse)
def get_history_page(request: Request, user: dict = Depends(get_current_user), conn=Depends(get_db_conn)):
    """
    포인트 사용 내역 페이지를 렌더링합니다.
    """
    user_id = user.get("user_id")
    coin_balance = 0
    history = []

    try:
        with conn.cursor() as cur:
            # 현재 코인 잔액 조회
            cur.execute(
                "SELECT SUM(delta) FROM public.point_history WHERE auth_user_id = %s",
                (uuid.UUID(user_id),)
            )
            balance_row = cur.fetchone()
            if balance_row and balance_row[0] is not None:
                coin_balance = balance_row[0]

            # 포인트 내역 조회
            cur.execute(
                "SELECT created_at, reason, delta FROM public.point_history WHERE auth_user_id = %s ORDER BY created_at DESC",
                (uuid.UUID(user_id),)
            )
            history_rows = cur.fetchall()
            for row in history_rows:
                history.append({"created_at": row[0], "reason": row[1], "delta": row[2]})

    except Exception as e:
        print(f"Error fetching history data: {e}")

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "coin_balance": coin_balance,
            "history": history
        }
    )
