import asyncio

import grpc

from app.grpc_generated import marketplace_pb2, marketplace_pb2_grpc


async def main():
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = marketplace_pb2_grpc.ItemServiceStub(channel)

        # запросим список товаров
        response = await stub.ListItems(marketplace_pb2.ListItemsRequest())
        print(f"Получено товаров через gRPC: {len(response.items)}")
        for it in response.items:
            print(f"  - [{it.id}] {it.title} — {it.price}₽, статус {it.status}")


if __name__ == "__main__":
    asyncio.run(main())