import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.minio_client import minio_client, ensure_bucket
from app.models.item_photo import ItemPhoto
from app.models.item import Item


async def upload_photo(session: AsyncSession, item_id: int, owner_id: int, file_bytes: bytes, content_type: str) -> ItemPhoto:
    """Загружает фото в MinIO и сохраняет ссылку в базу."""
    item = await session.get(Item, item_id)
    if item is None:
        raise ValueError("Товар не найден")
    if item.owner_id != owner_id:
        raise PermissionError("Это не ваш товар")

    ensure_bucket()

    # уникальное имя файла
    ext = content_type.split("/")[-1]  # например, "jpeg"
    object_name = f"{uuid.uuid4()}.{ext}"

    # загружаем в MinIO
    import io
    minio_client.put_object(
        settings.minio_bucket,
        object_name,
        io.BytesIO(file_bytes),
        length=len(file_bytes),
        content_type=content_type,
    )

    # формируем публичную ссылку
    url = f"http://{settings.minio_endpoint}/{settings.minio_bucket}/{object_name}"

    # сохраняем ссылку в базу
    photo = ItemPhoto(item_id=item_id, url=url)
    session.add(photo)
    await session.commit()
    await session.refresh(photo)
    return photo