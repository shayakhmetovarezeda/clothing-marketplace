import asyncio
from concurrent import futures

import grpc

from app.database import async_session
from app.grpc_generated import marketplace_pb2, marketplace_pb2_grpc
from app.schemas import ItemCreate
from app.services.item_service import create_item, list_items, get_item


def item_to_response(item) -> marketplace_pb2.ItemResponse:
    """Превращает объект товара (или словарь) в gRPC-ответ."""
    # list_items возвращает словари, остальные — объекты; поддержим оба
    def field(obj, name):
        return obj[name] if isinstance(obj, dict) else getattr(obj, name)

    return marketplace_pb2.ItemResponse(
        id=field(item, "id"),
        owner_id=field(item, "owner_id"),
        title=field(item, "title"),
        description=field(item, "description"),
        price=float(field(item, "price")),
        size=field(item, "size"),
        brand=field(item, "brand"),
        category=field(item, "category"),
        status=field(item, "status"),
    )


class ItemServicer(marketplace_pb2_grpc.ItemServiceServicer):
    """Реализация методов из контракта."""

    async def CreateItem(self, request, context):
        async with async_session() as session:
            data = ItemCreate(
                title=request.title,
                description=request.description,
                price=request.price,
                size=request.size,
                brand=request.brand,
                category=request.category,
            )
            item = await create_item(session, request.owner_id, data)
            return item_to_response(item)

    async def ListItems(self, request, context):
        async with async_session() as session:
            items = await list_items(session)
            return marketplace_pb2.ListItemsResponse(
                items=[item_to_response(it) for it in items]
            )

    async def GetItem(self, request, context):
        async with async_session() as session:
            item = await get_item(session, request.item_id)
            if item is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Товар не найден")
                return marketplace_pb2.ItemResponse()
            return item_to_response(item)


async def serve():
    server = grpc.aio.server()
    marketplace_pb2_grpc.add_ItemServiceServicer_to_server(ItemServicer(), server)
    server.add_insecure_port("[::]:50051")
    print("gRPC-сервер запущен на порту 50051")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())