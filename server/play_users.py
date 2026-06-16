import asyncio

from sqlalchemy import select

from app.database import async_session
from app.models.user import User
from app.security import hash_password, verify_password


async def main():
    async with async_session() as session:
        new_user = User(
            email="masha@example.com",
            hashed_password=hash_password("my_secret_123"),
        )
        session.add(new_user)
        await session.commit()
        print(f"Создан пользователь id={new_user.id}, email={new_user.email}")

        # читаем всех пользователей из бд
        result = await session.execute(select(User))
        users = result.scalars().all()
        print(f"\nВсего пользователей в базе: {len(users)}")
        for u in users:
            print(f"  - id={u.id}, email={u.email}")
            print(f"    хэш пароля: {u.hashed_password[:30]}...")

        # чекаем пароль
        ok = verify_password("my_secret_123", new_user.hashed_password)
        wrong = verify_password("неверный", new_user.hashed_password)
        print(f"\nПроверка верного пароля: {ok}")
        print(f"Проверка неверного пароля: {wrong}")


if __name__ == "__main__":
    asyncio.run(main())