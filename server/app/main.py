from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session
from app.schemas import UserCreate, UserRead, ItemCreate, ItemRead
from app.services.item_service import create_item, list_items, get_item

from fastapi.security import OAuth2PasswordRequestForm
from app.services.user_service import register_user, authenticate_user
from app.auth import create_access_token, get_current_user
from app.models.user import User

import jwt
from app.config import settings
from app.redis_client import redis_client
from app.auth import oauth2_scheme
from datetime import datetime, timezone
from fastapi import Depends

from app.schemas import ItemUpdate
from app.services.item_service import update_item, delete_item

from app.schemas import OrderRead
from app.services.order_service import create_order, confirm_order, cancel_order

from fastapi import UploadFile, File
from app.services.photo_service import upload_photo

from app.grpc_client import grpc_create_item, grpc_list_items, grpc_get_item

from app.models.item_photo import ItemPhoto
from sqlalchemy import select
app = FastAPI(title="Clothing Marketplace")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

@app.post("/items")
async def create_item_route(
    data: ItemCreate,
    current_user: User = Depends(get_current_user),
):
    return await grpc_create_item(current_user.id, data)

@app.get("/items")
async def get_items_route():
    return await grpc_list_items()

@app.get("/items/{item_id}")
async def get_item_route(item_id: int):
    item = await grpc_get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return item

@app.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    jti = payload.get("jti")
    exp = payload.get("exp")

    # сколько секунд осталось жить токену
    now = int(datetime.now(timezone.utc).timestamp())
    ttl = max(exp - now, 1)

    # кладём в чёрный список ровно до истечения токена
    await redis_client.set(f"blacklist:{jti}", "1", ex=ttl)
    return {"message": "Вы вышли из системы"}

@app.patch("/items/{item_id}", response_model=ItemRead)
async def update_item_route(
    item_id: int,
    data: ItemUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await update_item(session, item_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.delete("/items/{item_id}")
async def delete_item_route(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        await delete_item(session, item_id, current_user.id)
        return {"message": "Товар удалён"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.post("/orders", response_model=OrderRead)
async def create_order_route(
    item_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await create_order(session, current_user.id, item_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/orders/{order_id}/confirm", response_model=OrderRead)
async def confirm_order_route(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await confirm_order(session, current_user.id, order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.post("/orders/{order_id}/cancel", response_model=OrderRead)
async def cancel_order_route(
    order_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        return await cancel_order(session, current_user.id, order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.post("/items/{item_id}/photo")
async def upload_photo_route(
    item_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    file_bytes = await file.read()
    try:
        photo = await upload_photo(session, item_id, current_user.id, file_bytes, file.content_type)
        return {"url": photo.url}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.get("/items/{item_id}/photos")
async def get_item_photos(item_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(ItemPhoto.url).where(ItemPhoto.item_id == item_id)
    )
    return [row[0] for row in result.all()]