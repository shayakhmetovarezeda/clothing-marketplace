from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Item
from app.schemas import ItemCreate

import json

from app.redis_client import redis_client

from app.schemas import ItemCreate, ItemUpdate

from app.models.item_photo import ItemPhoto

CACHE_KEY = "items:active"
CACHE_TTL = 60


async def create_item(session: AsyncSession, owner_id: int, data: ItemCreate) -> Item:
    """Создаёт новый товар и сбрасывает кэш."""
    item = Item(
        owner_id=owner_id,
        title=data.title,
        description=data.description,
        price=data.price,
        size=data.size,
        brand=data.brand,
        category=data.category,
        status="ACTIVE",
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    await _clear_items_cache()  # новый товар → кэш устарел
    return item


async def list_items(session: AsyncSession) -> list[dict]:
    """Возвращает активные товары. Сначала смотрит в кэш Redis."""
    # пробуем взять из кэша
    cached = await redis_client.get(CACHE_KEY)
    if cached is not None:
        return json.loads(cached)

    # если нет — берём из базы
    result = await session.execute(
        select(Item).where(Item.status == "ACTIVE").order_by(Item.created_at.desc())
    )
    items = result.scalars().all()

    data = [
        {
            "id": it.id,
            "owner_id": it.owner_id,
            "title": it.title,
            "description": it.description,
            "price": float(it.price),
            "size": it.size,
            "brand": it.brand,
            "category": it.category,
            "status": it.status,
            "created_at": it.created_at.isoformat(),
        }
        for it in items
    ]

    # кладём в кэш на 60 секунд
    await redis_client.set(CACHE_KEY, json.dumps(data), ex=CACHE_TTL)
    return data

async def get_item(session: AsyncSession, item_id: int) -> Item | None:
    result = await session.execute(select(Item).where(Item.id == item_id))
    return result.scalar_one_or_none()

async def _clear_items_cache():
    try:
        await redis_client.delete(CACHE_KEY)
    except Exception:
        pass

async def update_item(session: AsyncSession, item_id: int, owner_id: int, data: ItemUpdate) -> Item:
    """Редактирует товар. Менять может только владелец."""
    item = await get_item(session, item_id)
    if item is None:
        raise ValueError("Товар не найден")
    if item.owner_id != owner_id:
        raise PermissionError("Это не ваш товар")

    # обновляем только переданные поля
    fields = data.model_dump(exclude_unset=True)
    for key, value in fields.items():
        setattr(item, key, value)

    await session.commit()
    await session.refresh(item)
    await _clear_items_cache()
    return item


async def delete_item(session: AsyncSession, item_id: int, owner_id: int) -> None:
    """Удаляет товар (помечает как DELETED). Только владелец."""
    item = await get_item(session, item_id)
    if item is None:
        raise ValueError("Товар не найден")
    if item.owner_id != owner_id:
        raise PermissionError("Это не ваш товар")

    item.status = "DELETED"  # мягкое удаление: не стираем, а помечаем
    await session.commit()
    await _clear_items_cache()