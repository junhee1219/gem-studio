from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    nickname: str = Field(..., min_length=2, max_length=20)

class UserLogin(BaseModel):
    email: EmailStr
    password: str
