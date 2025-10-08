from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import auth, dashboard, jobs, history

app = FastAPI()

# 정적 파일 마운트 (업로드된 이미지 접근을 위해)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 라우터 등록(필수)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(jobs.router)
app.include_router(history.router)

