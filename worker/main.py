import asyncio
import json

import aio_pika

# локально брокер тут; позже можно вынести в .env
RABBITMQ_URL = "amqp://guest:guest@localhost:5672/"
QUEUE_NAME = "order_events"


async def handle_message(message: aio_pika.IncomingMessage):
    """Обрабатывает одно событие из очереди."""
    async with message.process():
        data = json.loads(message.body.decode())
        print("Получено событие:", data)


async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    print("Worker запущен, жду события... (Ctrl+C для выхода)")
    await queue.consume(handle_message)
    await asyncio.Future()  # работать бесконечно


if __name__ == "__main__":
    asyncio.run(main())