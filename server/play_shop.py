import asyncio

from app.database import async_session
from app.schemas import UserCreate, ItemCreate
from app.services.user_service import register_user, authenticate_user
from app.services.item_service import create_item, list_items


async def main():
    async with async_session() as session:
        # регистрируем продавца (email уникальный — добавим случайности)
        import random
        email = f"seller{random.randint(1, 100000)}@example.com"
        seller = await register_user(session, UserCreate(email=email, password="pass123"))
        print(f"Продавец: id={seller.id}, {seller.email}")

        # проверяем вход
        ok = await authenticate_user(session, email, "pass123")
        bad = await authenticate_user(session, email, "wrong")
        print(f"Вход с верным паролем: {'успех' if ok else 'отказ'}")
        print(f"Вход с неверным паролем: {'успех' if bad else 'отказ'}")

        # создаём товар
        item = await create_item(session, seller.id, ItemCreate(
            title="Джинсовая куртка Levi's",
            description="Винтаж, отличное состояние",
            price=2500.00,
            size="M",
            brand="Levi's",
            category="Верхняя одежда",
        ))
        print(f"\nСоздан товар: id={item.id}, {item.title}, {item.price}₽, статус={item.status}")

        # список товаров
        items = await list_items(session)
        print(f"\nАктивных товаров в магазине: {len(items)}")
        for it in items:
            print(f"  - [{it.id}] {it.title} — {it.price}₽, размер {it.size}")


if __name__ == "__main__":
    asyncio.run(main())