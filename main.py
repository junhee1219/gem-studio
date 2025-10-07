from fastapi import FastAPI
from routers import auth, dashboard

app = FastAPI()

# 라우터 등록(필수)
app.include_router(auth.router)
app.include_router(dashboard.router)

