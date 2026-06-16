from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Item
from app.schemas import ItemCreate


async def create_item(session: AsyncSession, ownher_id: int, data:ItemCreate) -> Item:
    item = Item(
        owner_id = ownher_id,
        title = data.title,
        description = data.description,
        price = data.price,
        size = data.size,
        brand = data.brand,
        category = data.category,
        status = "ACTIVE"
    )

    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item

async def list_items(session: AsyncSession) -> List[Item]:

    result = await session.execute(
        select(Item).where(Item.status == "ACTIVE").order_by(Item.created_at.desc())

    )
    return list(result.scalars().all())

async def get_item(session: AsyncSession, item_id: int) -> Item | None:
    result = await session.execute(select(Item).where(Item.id == item_id))
    return result.scalar_one_or_none()