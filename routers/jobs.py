from fastapi import APIRouter, Depends, Request, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import List
import json
import uuid
import os
import shutil

from common.templates import templates
from common.security import get_current_user
from db import get_db_conn

router = APIRouter(prefix="/jobs", tags=["jobs"])

UPLOAD_DIR = "uploads"

@router.get("/new", response_class=HTMLResponse)
def get_new_job_page(request: Request, user: dict = Depends(get_current_user)):
    """
    새로운 프로필 생성 작업을 위한 페이지를 렌더링합니다.
    """
    return templates.TemplateResponse(
        "job_form.html", 
        {"request": request, "mode": "new", "job_options": {}}
    )

@router.post("", status_code=201)
async def create_job(
    request: Request,
    conn=Depends(get_db_conn),
    user: dict = Depends(get_current_user),
    face_photo: UploadFile = File(...),
    item_photo_1: UploadFile = File(None),
    item_photo_2: UploadFile = File(None),
    item_photo_3: UploadFile = File(None),
    shot_type: str = Form(...),
    background: str = Form(...),
    background_color: str = Form("#ffffff"),
    lighting: str = Form(...),
    expression: str = Form(...),
    mood: str = Form(...)
):
    """
    새로운 프로필 생성 작업을 생성합니다.
    1. 이미지 파일들을 로컬 파일 시스템에 저장합니다.
    2. jobs 및 job_details 테이블에 작업 정보를 저장합니다.
    """
    auth_user_id = user.get("user_id")
    if not auth_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    input_urls = []
    # Optional item photos
    item_photos = [p for p in [item_photo_1, item_photo_2, item_photo_3] if p and p.filename]
    all_photos = [face_photo] + item_photos

    try:
        # 1. 파일 저장
        user_upload_dir = os.path.join(UPLOAD_DIR, auth_user_id)
        os.makedirs(user_upload_dir, exist_ok=True)

        for photo in all_photos:
            if photo.filename:
                file_id = str(uuid.uuid4())
                file_extension = os.path.splitext(photo.filename)[1]
                local_filename = f"{file_id}{file_extension}"
                local_filepath = os.path.join(user_upload_dir, local_filename)

                with open(local_filepath, "wb") as buffer:
                    shutil.copyfileobj(photo.file, buffer)
                
                web_path = f"/uploads/{auth_user_id}/{local_filename}"
                input_urls.append(web_path)

        # 2. 데이터베이스에 작업 정보 저장
        with conn.cursor() as cur:
            # jobs 테이블에 삽입
            cur.execute(
                """
                INSERT INTO public.jobs (auth_user_id, input_urls)
                VALUES (%s, %s)
                RETURNING id;
                """,
                (auth_user_id, json.dumps(input_urls))
            )
            job_id = cur.fetchone()[0]

            # job_details 테이블에 삽입
            details = [
                ('shot_type', 'shot_type', shot_type),
                ('background', 'type', background),
                ('background', 'color', background_color if background == 'monotone' else None),
                ('lighting', 'lighting', lighting),
                ('expression', 'expression', expression),
                ('mood', 'mood', mood)
            ]
            
            for opt_type, opt_key, opt_value in details:
                if opt_value:
                    cur.execute(
                        """
                        INSERT INTO public.job_details (job_id, opt_type, opt_key, opt_value)
                        VALUES (%s, %s, %s, %s);
                        """,
                        (job_id, opt_type, opt_key, opt_value)
                    )
        
        return RedirectResponse(url=f"/jobs/{job_id}", status_code=303)

    except Exception as e:
        print(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail="작업 생성 중 오류가 발생했습니다.")


@router.get("/{job_id}", response_class=HTMLResponse)
def get_job_page(
    request: Request,
    job_id: int,
    conn=Depends(get_db_conn),
    user: dict = Depends(get_current_user)
):
    """
    특정 작업의 상세 정보를 보여주는 페이지를 렌더링합니다.
    """
    auth_user_id = user.get("user_id")
    try:
        with conn.cursor() as cur:
            # Job 정보 가져오기
            cur.execute(
                "SELECT id, auth_user_id, status, input_urls, output_urls, error_msg FROM public.jobs WHERE id = %s",
                (job_id,)
            )
            job_row = cur.fetchone()
            if not job_row or str(job_row[1]) != auth_user_id:
                raise HTTPException(status_code=404, detail="Job not found")

            job = {
                "id": job_row[0],
                "auth_user_id": job_row[1],
                "status": job_row[2],
                "input_urls": job_row[3],
                "output_urls": job_row[4],
                "error_msg": job_row[5]
            }

            # Job details 정보 가져오기
            cur.execute(
                "SELECT opt_type, opt_key, opt_value FROM public.job_details WHERE job_id = %s",
                (job_id,)
            )
            details_rows = cur.fetchall()
            
            # Job details를 템플릿에서 사용하기 쉬운 딕셔너리 형태로 가공
            job_options = {}
            for r in details_rows:
                # r = (opt_type, opt_key, opt_value)
                if r[0] == 'background' and r[1] == 'type':
                    job_options['background'] = r[2]
                elif r[0] == 'background' and r[1] == 'color':
                    job_options['background_color'] = r[2]
                else:
                    job_options[r[1]] = r[2]

        return templates.TemplateResponse(
            "job_form.html",
            {
                "request": request, 
                "mode": "read", 
                "job": job, 
                "job_options": job_options
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error fetching job: {e}")
        raise HTTPException(status_code=500, detail="작업 정보를 가져오는 중 오류가 발생했습니다.")
