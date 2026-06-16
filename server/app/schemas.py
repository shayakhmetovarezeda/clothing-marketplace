from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    created_at: datetime


class ItemCreate(BaseModel):
    title: str
    description: str = ""
    price: float
    size: str
    brand: str = ""
    category: str


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    owner_id: int
    title: str
    description: str
    price: float
    size: str
    brand: str
    category: str
    status: str
    created_at: datetime