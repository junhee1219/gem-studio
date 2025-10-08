from fastapi import FastAPI
from routers import auth, dashboard, jobs, history

app = FastAPI()

# 라우터 등록(필수)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(jobs.router)
app.include_router(history.router)

