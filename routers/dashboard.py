from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
import uuid

from common.security import try_get_current_user
from common.templates import templates
from db import get_db_conn

router = APIRouter()

@router.get("/")
def get_dashboard(request: Request, user: dict | None = Depends(try_get_current_user), conn=Depends(get_db_conn)):
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    user_id = user.get("user_id")
    nickname = "사용자"
    coin_balance = 0
    pending_jobs = []
    completed_jobs = []

    try:
        with conn.cursor() as cur:
            # 닉네임 조회
            cur.execute("SELECT nickname FROM profiles WHERE auth_user_id = %s", (user_id,))
            profile_row = cur.fetchone()
            if profile_row:
                nickname = profile_row[0]

            # 코인 잔액 조회
            cur.execute(
                "SELECT SUM(delta) FROM public.point_history WHERE auth_user_id = %s",
                (user_id,)
            )
            balance_row = cur.fetchone()
            if balance_row and balance_row[0] is not None:
                coin_balance = balance_row[0]

            # 작업 목록 조회
            cur.execute(
                "SELECT id, status, output_urls FROM public.jobs WHERE auth_user_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
            all_jobs = cur.fetchall()

            for job_row in all_jobs:
                job = {"id": job_row[0], "status": job_row[1], "output_urls": job_row[2]}
                if job["status"] in ['QUEUED', 'PROCESSING']:
                    pending_jobs.append(job)
                elif job["status"] == 'COMPLETED':
                    completed_jobs.append(job)

    except Exception as e:
        print(f"Error fetching dashboard data: {e}")

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "nickname": nickname,
            "coin_balance": coin_balance,
            "pending_jobs": pending_jobs,
            "completed_jobs": completed_jobs,
        },
    )
