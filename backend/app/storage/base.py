from abc import ABC, abstractmethod
from datetime import timedelta


class ObjectStorage(ABC):
    """Persistent binary object storage. Application services depend on this
    interface, never on a specific client (e.g. MinIO) directly."""

    @abstractmethod
    def upload(self, bucket: str, object_key: str, data: bytes, content_type: str) -> None: ...

    @abstractmethod
    def download(self, bucket: str, object_key: str) -> bytes: ...

    @abstractmethod
    def delete(self, bucket: str, object_key: str) -> None: ...

    @abstractmethod
    def exists(self, bucket: str, object_key: str) -> bool: ...

    @abstractmethod
    def generate_presigned_url(
        self, bucket: str, object_key: str, expires: timedelta = timedelta(minutes=15)
    ) -> str: ...
