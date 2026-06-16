import asyncio

from app.broker import publish_event


async def main():
    await publish_event({"event": "order.created", "order_id": 123, "item_id": 1})
    print("Событие отправлено!")


if __name__ == "__main__":
    asyncio.run(main())