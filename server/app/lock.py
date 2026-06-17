import asyncio

from app.redis_client import redis_client


class RedisLock:

    def __init__(self, key: str, timeout: int = 10):
        self.key = f"lock:{key}"
        self.timeout = timeout  # на сколько секунд максимум держать замок

    async def __aenter__(self):
        while True:
            ok = await redis_client.set(self.key, "1", nx=True, ex=self.timeout)
            if ok:
                return self
            await asyncio.sleep(0.1)

    async def __aexit__(self, exc_type, exc, tb):
        # снимаем замок
        await redis_client.delete(self.key)
