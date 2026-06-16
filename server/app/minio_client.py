from minio import Minio

from app.config import settings

minio_client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=False,  # локально без https
)


def ensure_bucket():
    """Создаёт «папку» (bucket) для фото, если её ещё нет."""
    found = minio_client.bucket_exists(settings.minio_bucket)
    if not found:
        minio_client.make_bucket(settings.minio_bucket)
        # делаем фото доступными для чтения по ссылке
        import json
        policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{settings.minio_bucket}/*"],
            }],
        }
        minio_client.set_bucket_policy(settings.minio_bucket, json.dumps(policy))