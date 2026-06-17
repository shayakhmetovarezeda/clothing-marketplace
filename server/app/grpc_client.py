import grpc

from app.grpc_generated import marketplace_pb2, marketplace_pb2_grpc

GRPC_SERVER = "localhost:50051"


async def grpc_create_item(owner_id: int, data) -> dict:
    """Зовёт Server по gRPC, чтобы создать товар."""
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = marketplace_pb2_grpc.ItemServiceStub(channel)
        request = marketplace_pb2.CreateItemRequest(
            owner_id=owner_id,
            title=data.title,
            description=data.description,
            price=data.price,
            size=data.size,
            brand=data.brand,
            category=data.category,
        )
        resp = await stub.CreateItem(request)
        return _resp_to_dict(resp)


async def grpc_list_items() -> list[dict]:
    """Зовёт Server по gRPC, чтобы получить список товаров."""
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = marketplace_pb2_grpc.ItemServiceStub(channel)
        resp = await stub.ListItems(marketplace_pb2.ListItemsRequest())
        return [_resp_to_dict(it) for it in resp.items]


async def grpc_get_item(item_id: int) -> dict | None:
    """Зовёт Server по gRPC, чтобы получить один товар."""
    async with grpc.aio.insecure_channel(GRPC_SERVER) as channel:
        stub = marketplace_pb2_grpc.ItemServiceStub(channel)
        try:
            resp = await stub.GetItem(marketplace_pb2.GetItemRequest(item_id=item_id))
            return _resp_to_dict(resp)
        except grpc.aio.AioRpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            raise


def _resp_to_dict(resp) -> dict:
    """Превращает gRPC-ответ в обычный словарь для браузера."""
    return {
        "id": resp.id,
        "owner_id": resp.owner_id,
        "title": resp.title,
        "description": resp.description,
        "price": resp.price,
        "size": resp.size,
        "brand": resp.brand,
        "category": resp.category,
        "status": resp.status,
    }