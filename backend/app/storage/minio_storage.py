import io
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from app.core.errors import StorageError
from app.storage.base import ObjectStorage


class MinIOObjectStorage(ObjectStorage):
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
    ):
        self._client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

    def ensure_bucket(self, bucket: str) -> None:
        try:
            if not self._client.bucket_exists(bucket):
                self._client.make_bucket(bucket)
        except S3Error as exc:
            raise StorageError(f"Failed to ensure bucket '{bucket}' exists", detail=str(exc)) from exc

    def upload(self, bucket: str, object_key: str, data: bytes, content_type: str) -> None:
        try:
            self._client.put_object(
                bucket, object_key, io.BytesIO(data), length=len(data), content_type=content_type
            )
        except S3Error as exc:
            raise StorageError(f"Failed to upload object '{object_key}'", detail=str(exc)) from exc

    def download(self, bucket: str, object_key: str) -> bytes:
        response = None
        try:
            response = self._client.get_object(bucket, object_key)
            return response.read()
        except S3Error as exc:
            raise StorageError(f"Failed to download object '{object_key}'", detail=str(exc)) from exc
        finally:
            if response is not None:
                response.close()
                response.release_conn()

    def delete(self, bucket: str, object_key: str) -> None:
        try:
            self._client.remove_object(bucket, object_key)
        except S3Error as exc:
            raise StorageError(f"Failed to delete object '{object_key}'", detail=str(exc)) from exc

    def exists(self, bucket: str, object_key: str) -> bool:
        try:
            self._client.stat_object(bucket, object_key)
            return True
        except S3Error as exc:
            if exc.code in ("NoSuchKey", "NoSuchObject", "NotFound"):
                return False
            raise StorageError(f"Failed to check object '{object_key}'", detail=str(exc)) from exc

    def generate_presigned_url(
        self, bucket: str, object_key: str, expires: timedelta = timedelta(minutes=15)
    ) -> str:
        try:
            return self._client.presigned_get_object(bucket, object_key, expires=expires)
        except S3Error as exc:
            raise StorageError(f"Failed to presign object '{object_key}'", detail=str(exc)) from exc


_storage: MinIOObjectStorage | None = None


def get_object_storage() -> MinIOObjectStorage:
    global _storage
    if _storage is None:
        from app.config import get_settings

        settings = get_settings()
        _storage = MinIOObjectStorage(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        _storage.ensure_bucket(settings.minio_bucket_documents)
    return _storage
