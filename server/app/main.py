from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session
from app.schemas import UserCreate, UserRead, ItemCreate, ItemRead
from app.services.item_service import create_item, list_items, get_item

from fastapi.security import OAuth2PasswordRequestForm
from app.services.user_service import register_user, authenticate_user
from app.auth import create_access_token, get_current_user
from app.models.user import User

app = FastAPI(title="Clothing Marketplace")


@app.get("/")
async def root():
    return {"message": "Магазин одежды работает!"}



@app.post("/register", response_model=UserRead)
async def register(data: UserCreate, session: AsyncSession = Depends(get_session)):
    try:
        return await register_user(session, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login")
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    user = await authenticate_user(session, form.username, form.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/items", response_model=ItemRead)
async def create_item_route(
    data: ItemCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await create_item(session, current_user.id, data)


@app.get("/items", response_model=list[ItemRead])
async def get_items_route(session: AsyncSession = Depends(get_session)):
    return await list_items(session)


@app.get("/items/{item_id}", response_model=ItemRead)
async def get_item_route(item_id: int, session: AsyncSession = Depends(get_session)):
    item = await get_item(session, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return item