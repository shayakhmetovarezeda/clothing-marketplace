import pytest

from app.schemas import UserCreate, ItemCreate
from app.services.user_service import register_user
from app.services.item_service import create_item, get_item


async def _make_user(session, email):
    return await register_user(session, UserCreate(email=email, password="pass"))

def _item_data():
    return ItemCreate(title="Куртка", description="Куртка джинсовая", price = 4500, size="M", brand = "Befree", category = "куртки")

async def test_create_item(session):
    user = await _make_user(session, "seller@test.com")
    item = await create_item(session, user.id, _item_data())
    assert item.id is not None
    assert item.title == "Куртка"
    assert item.status == "ACTIVE"
    assert item.owner_id == user.id

async def test_get_item(session):
    user = await _make_user(session, "seller2@test.com")
    created = await create_item(session, user.id, _item_data())
    found = await get_item(session, created.id)
    assert found is not None
    assert found.id == created.id

async def test_get_missing_item(session):
    found= await get_item(session, 99999)
    assert found is None

async def test_new_item_is_active(session):
    user = await _make_user(session, "seller3@test.com")
    item = await create_item(session, user.id, _item_data())
    assert item.status == "ACTIVE"

async def test_price_saved_correctly(session):
    user = await _make_user(session, "seller4@test.com")
    item = await create_item(session, user.id, _item_data())
    assert float(item.price) == 4500.0