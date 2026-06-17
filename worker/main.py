import asyncio
import json

import aio_pika
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


# RABBITMQ_URL = "amqp://guest:guest@localhost:5672/"
# QUEUE_NAME = "order_events"
# DATABASE_URL = "postgresql+asyncpg://postgres:admin@localhost:5433/marketplace"
# REDIS_URL = "redis://localhost:6379/0"
import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE_NAME = "order_events"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:admin@localhost:5433/marketplace")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

import redis.asyncio as redis

engine = create_async_engine(DATABASE_URL)
SessionMaker = async_sessionmaker(engine, expire_on_commit=False)
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


async def handle_message(message: aio_pika.IncomingMessage):
    """Обрабатывает событие из очереди (пока просто логируем)."""
    async with message.process():
        data = json.loads(message.body.decode())
        print("Событие:", data)


async def check_expired_orders():
    """Каждые 5 секунд ищет заказы, у которых истёк TTL, и отменяет их."""
    # импорты моделей внутри, чтобы Worker не зависел от структуры server
    from sqlalchemy import update
    while True:
        await asyncio.sleep(5)
        async with SessionMaker() as session:
            # берём все PENDING заказы
            rows = await session.execute(
                select_pending()
            )
            pending = rows.all()
            for order_id, item_id in pending:
                # если TTL-ключ исчез — время вышло
                exists = await redis_client.exists(f"order_ttl:{order_id}")
                if not exists:
                    # отменяем заказ и возвращаем товар в продажу
                    await session.execute(
                        update_order_cancelled(order_id)
                    )
                    await session.execute(
                        update_item_active(item_id)
                    )
                    await session.commit()
                    await redis_client.delete("items:active")  # сброс кэша
                    print(f" Заказ {order_id} отменён по таймауту, товар {item_id} снова ACTIVE")


# Вспомогательные SQL-запросы (через сырой SQL, чтобы не тащить модели)
from sqlalchemy import text

def select_pending():
    return text("SELECT id, item_id FROM orders WHERE status = 'PENDING'")

def update_order_cancelled(order_id):
    return text("UPDATE orders SET status = 'CANCELLED' WHERE id = :oid").bindparams(oid=order_id)

def update_item_active(item_id):
    return text("UPDATE items SET status = 'ACTIVE' WHERE id = :iid").bindparams(iid=item_id)


async def main():
    # подключаемся к брокеру
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    await queue.consume(handle_message)
    print("Worker запущен: слушаю события + проверяю таймауты...")

    # параллельно крутим проверку таймаутов
    await check_expired_orders()


if __name__ == "__main__":
    asyncio.run(main())