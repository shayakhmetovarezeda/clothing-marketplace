from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item
from app.models.order import Order
from app.broker import publish_event
from app.services.item_service import _clear_items_cache

from app.redis_client import redis_client

from app.lock import RedisLock

async def create_order(session: AsyncSession, buyer_id: int, item_id: int) -> Order:
    # запрем товар на время операции чтобы не купили дважды одновременно
    async with RedisLock(f"item:{item_id}"):
        item = await session.get(Item, item_id)
        if item is None:
            raise ValueError("Товар не найден")

        if item.status != "ACTIVE":
            raise ValueError("Товар недоступен для покупки")

        if item.owner_id == buyer_id:
            raise ValueError("Нельзя купить собственный товар")

        order = Order(item_id=item_id, buyer_id=buyer_id, status="PENDING")
        item.status = "RESERVED"
        session.add(order)
        await session.commit()
        await session.refresh(order)
        await _clear_items_cache()

        await publish_event({"event": "order.created", "order_id": order.id, "item_id": item_id})
        await redis_client.set(f"order_ttl:{order.id}", "1", ex=900)
        return order



async def confirm_order(session: AsyncSession, buyer_id: int, order_id: int) -> Order:
    """Подтверждает заказ: заказ → CONFIRMED, товар → SOLD."""
    order = await session.get(Order, order_id)
    if order is None:
        raise ValueError("Заказ не найден")
    if order.buyer_id != buyer_id:
        raise PermissionError("Это не ваш заказ")

    # подтвердить можно только ожидающий заказ
    if order.status != "PENDING":
        raise ValueError(f"Нельзя подтвердить заказ в статусе {order.status}")

    order.status = "CONFIRMED"
    item = await session.get(Item, order.item_id)
    item.status = "SOLD"
    await redis_client.delete(f"order_ttl:{order.id}")
    await session.commit()
    await session.refresh(order)
    await _clear_items_cache()

    await publish_event({"event": "order.confirmed", "order_id": order.id, "item_id": order.item_id})
    return order


async def cancel_order(session: AsyncSession, buyer_id: int, order_id: int) -> Order:
    """Отменяет заказ: заказ → CANCELLED, товар → ACTIVE."""
    order = await session.get(Order, order_id)
    if order is None:
        raise ValueError("Заказ не найден")
    if order.buyer_id != buyer_id:
        raise PermissionError("Это не ваш заказ")

    # отменить можно только ожидающий заказ
    if order.status != "PENDING":
        raise ValueError(f"Нельзя отменить заказ в статусе {order.status}")

    order.status = "CANCELLED"
    item = await session.get(Item, order.item_id)
    item.status = "ACTIVE"  # товар снова доступен
    await redis_client.delete(f"order_ttl:{order.id}")
    await session.commit()
    await session.refresh(order)
    await _clear_items_cache()

    await publish_event({"event": "order.cancelled", "order_id": order.id, "item_id": order.item_id})
    return order