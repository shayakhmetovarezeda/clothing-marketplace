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


class ItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    price: float | None = None
    size: str | None = None
    brand: str | None = None
    category: str | None = None

class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    item_id: int
    buyer_id: int
    status: str
    created_at: datetime