import json

import aio_pika

from app.config import settings

QUEUE_NAME = "order_events"


async def publish_event(body: dict):
    """Кладёт событие в очередь RabbitMQ."""
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.declare_queue(QUEUE_NAME, durable=True)
        message = aio_pika.Message(
            body=json.dumps(body).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await channel.default_exchange.publish(message, routing_key=QUEUE_NAME)
        