# app.py
import asyncio, json, os, socket
from typing import Any, Dict, List, Tuple
from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool
from datetime import timedelta, datetime
from prompt import PROMPT_TMPL

DB_DSN = os.getenv("DB_DSN", "postgresql+psycopg://user:pass@localhost:5432/dbname")  # psycopg3
WORKER_ID = os.getenv("WORKER_ID", socket.gethostname())
POLL_INTERVAL_SEC = int(os.getenv("POLL_INTERVAL_SEC", "10"))
LOCK_TIMEOUT_SEC = int(os.getenv("LOCK_TIMEOUT_SEC", "300"))  # 5분

app = FastAPI()
pool: AsyncConnectionPool | None = None


# ---------- Prompt builder ----------
def map_shot_type(v: str) -> str:
    return v.replace("_", " ")

def build_background(detail: Dict[str, Dict[str, str]]) -> str:
    bg = detail.get("background", {})
    bg_type = bg.get("type", "")
    if bg_type == "monotone":
        color = bg.get("color")
        if color:
            return f"monotone (color: {color})"
        return "monotone"
    return bg_type or "studio"

def make_prompt(options: Dict[str, Any]) -> str:
    구도 = map_shot_type(options.get("shot_type", "half body"))
    표정 = options.get("expression", "natural smile")
    조명 = options.get("lighting", "studio light")
    느낌 = options.get("mood", "professional")
    배경 = build_background(options)

    return PROMPT_TMPL.format(구도=구도, 표정=표정, 조명=조명, 느낌=느낌, 배경=배경)


# ---------- DB helpers ----------
async def fetch_queued_jobs(conn, limit: int = 5) -> List[Dict[str, Any]]:
    """
    락 경쟁 방지를 위해 SKIP LOCKED 사용.
    오래된 락은 무시하고 다시 잡도록 조건 추가.
    """
    sql = """
    WITH picked AS (
      SELECT id
      FROM public.jobs
      WHERE status = 'QUEUED'::job_status
        AND (locked_at IS NULL OR locked_at < now() - INTERVAL '1 second' * %(lock_timeout)s)
      ORDER BY priority ASC, created_at ASC
      FOR UPDATE SKIP LOCKED
      LIMIT %(limit)s
    )
    UPDATE public.jobs j
      SET locked_by = %(worker)s,
          locked_at = now()
      FROM picked
      WHERE j.id = picked.id
      RETURNING j.id, j.auth_user_id, j.input_urls, j.status, j.priority, j.locked_by, j.locked_at, j.created_at, j.updated_at;
    """
    rows = []
    async with conn.cursor() as cur:
        await cur.execute(sql, {"limit": limit, "worker": WORKER_ID, "lock_timeout": LOCK_TIMEOUT_SEC})
        recs = await cur.fetchall()
        for r in recs:
            # psycopg3는 기본적으로 튜플; 컬럼 순서 맞춰 dict로 변환
            rows.append({
                "id": r[0],
                "auth_user_id": r[1],
                "input_urls": r[2],
                "status": r[3],
                "priority": r[4],
                "locked_by": r[5],
                "locked_at": r[6],
                "created_at": r[7],
                "updated_at": r[8],
            })
    return rows

async def fetch_job_details(conn, job_id: int) -> Dict[str, Dict[str, str]]:
    """
    결과 예:
    {
      "shot_type": {"shot_type": "upper_body"},
      "background": {"type": "monotone", "color": "#FFFFFF"},
      "lighting": {"lighting": "natural"},
      "expression": {"expression": "smile"},
      "mood": {"mood": "casual"}
    }
    """
    sql = """
    SELECT opt_type::text, opt_key, opt_value
    FROM public.job_details
    WHERE job_id = %(job_id)s
    ORDER BY id ASC
    """
    out: Dict[str, Dict[str, str]] = {}
    async with conn.cursor() as cur:
        await cur.execute(sql, {"job_id": job_id})
        for opt_type, opt_key, opt_value in await cur.fetchall():
            bucket = out.setdefault(opt_type, {})
            bucket[opt_key] = opt_value
    return out

async def save_prompt_detail(conn, job_id: int, prompt: str):
    """
    프롬프트를 detail에 저장해두고, 외부 호출 워커가 가져가도록.
    option_type enum에 'prompt'가 없다면 이 함수는 주석 처리하거나 테이블을 별도로 두세요.
    """
    sql = """
    INSERT INTO public.job_details (job_id, opt_type, opt_key, opt_value)
    VALUES (%(job_id)s, 'prompt'::option_type, 'prompt', %(prompt)s)
    """
    try:
        async with conn.cursor() as cur:
            await cur.execute(sql, {"job_id": job_id, "prompt": prompt})
    except Exception:
        # enum에 prompt가 없다면 주석으로 남김
        pass

async def mark_job_error(conn, job_id: int, msg: str):
    sql = """
    UPDATE public.jobs
       SET error_msg = %(msg)s,
           locked_by = NULL,
           locked_at = NULL,
           updated_at = now()
     WHERE id = %(job_id)s
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, {"job_id": job_id, "msg": msg})

async def mark_job_unlocked(conn, job_id: int):
    sql = """
    UPDATE public.jobs
       SET locked_by = NULL,
           locked_at = NULL,
           updated_at = now()
     WHERE id = %(job_id)s
    """
    async with conn.cursor() as cur:
        await cur.execute(sql, {"job_id": job_id})


# ---------- Worker ----------
async def worker_loop():
    global pool
    assert pool is not None
    while True:
        try:
            async with pool.connection() as conn:
                async with conn.transaction():
                    jobs = await fetch_queued_jobs(conn, limit=5)
                # 각 잡 처리
                for job in jobs:
                    try:
                        async with conn.transaction():
                            details = await fetch_job_details(conn, job["id"])
                            # 옵션 평탄화
                            options = {
                                "shot_type": details.get("shot_type", {}).get("shot_type"),
                                "expression": details.get("expression", {}).get("expression"),
                                "lighting": details.get("lighting", {}).get("lighting"),
                                "mood": details.get("mood", {}).get("mood"),
                                "background": details.get("background", {}),  # dict 형태로 넘겨서 build_background에서 처리
                            }

                            prompt = make_prompt(options)
                            # 프롬프트 저장(선택)
                            await save_prompt_detail(conn, job["id"], prompt)

                            # input_urls 파싱
                            input_urls = job["input_urls"]
                            if isinstance(input_urls, str):
                                input_urls = json.loads(input_urls)
                            main_image = input_urls[0] if input_urls else None
                            prop_images = input_urls[1:4] if input_urls and len(input_urls) > 1 else []

                            # 실제 호출 자리
                            await send_to_nano_banana(job_id=job["id"],
                                                      prompt=prompt,
                                                      main_image=main_image,
                                                      prop_images=prop_images)

                            # 처리 끝났으면 락 해제 (상태 변경 로직은 팀 규칙에 맞게 추가)
                            await mark_job_unlocked(conn, job["id"])

                    except Exception as e:
                        await mark_job_error(conn, job["id"], f"worker error: {e!r}")
        except Exception:
            # 풀 전체 에러는 다음 주기로 재시도
            pass

        await asyncio.sleep(POLL_INTERVAL_SEC)


# 실제 연동부 - 자리만 잡아둠
async def send_to_nano_banana(job_id: int, prompt: str, main_image: str | None, prop_images: List[str]):
    """
    여기서 Nano Banana API 호출하면 됨.
    - prompt
    - main_image(필수)
    - prop_images(선택)
    성공 시 public.jobs.output_urls 업데이트 등 후처리 추가.
    """
    # TODO: HTTP 호출 작성
    # print로 대체
    print(f"[job {job_id}] prompt:\n{prompt}\nmain={main_image}\nprops={prop_images}\n")


# ---------- FastAPI lifecycle ----------
@app.on_event("startup")
async def on_startup():
    global pool
    # psycopg3 async pool
    pool = AsyncConnectionPool(conninfo=os.getenv(
        "PG_CONNINFO",
        os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/dbname")
    ), open=True)
    asyncio.create_task(worker_loop())


@app.get("/healthz")
async def healthz():
    return {"ok": True}
