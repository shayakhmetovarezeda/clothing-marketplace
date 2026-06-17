import pytest

from app.schemas import UserCreate
from app.services.user_service import register_user, authenticate_user
from app.security import hash_password, verify_password

async def test_register_user(session):
    user = await register_user(session, UserCreate(email="a@test.com", password="pass123"))
    assert user.id is not None
    assert user.email == "a@test.com"
    assert user.hashed_password != "pass123"

async def test_register_duplicate_email(session):
    await register_user(session, UserCreate(email="dup@test.com", password="pass123"))
    with pytest.raises(ValueError):
        await register_user(session, UserCreate(email="dup@test.com", password="other"))

async def test_authenticate_correct(session):
    await register_user(session, UserCreate(email="b@test.com", password="secret"))
    user = await authenticate_user(session, "b@test.com", "secret")
    assert user is not None

async def test_authenticate_wrong_password(session):
    await register_user(session, UserCreate(email="c@test.com", password="secret"))
    user = await authenticate_user(session, "c@test.com", "wrong")
    assert user is None

def test_password_hashing(session):
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert verify_password("mypassword", hashed) is True
    assert verify_password("wrong", hashed) is False