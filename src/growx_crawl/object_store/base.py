from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Union
from growx_crawl.object_store.models import ObjectStat


class ObjectStore(ABC):
    """
    Provider-agnostic ObjectStore interface per Section 7 specification.
    Guarantees seamless parity between LocalObjectStore (offline/tests) and R2ObjectStore (production).
    """

    @abstractmethod
    async def put(
        self,
        bucket: str,
        key: str,
        data: Union[bytes, str],
        *,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        compress: bool = True,
    ) -> ObjectStat:
        """Stores an object in the specified bucket and returns its metadata stat."""
        ...

    @abstractmethod
    async def get(self, bucket: str, key: str) -> bytes:
        """Retrieves and returns the full uncompressed bytes of an object."""
        ...

    @abstractmethod
    async def stream(self, bucket: str, key: str, chunk_size: int = 65536) -> AsyncIterator[bytes]:
        """Asynchronously streams chunks of the uncompressed object payload."""
        ...

    @abstractmethod
    async def delete(self, bucket: str, key: str) -> bool:
        """Deletes an object. Returns True if deleted or already absent."""
        ...

    @abstractmethod
    async def exists(self, bucket: str, key: str) -> bool:
        """Checks if an object exists in the specified bucket."""
        ...

    @abstractmethod
    async def stat(self, bucket: str, key: str) -> ObjectStat:
        """Returns metadata and stat information for the object."""
        ...

    @abstractmethod
    async def list(self, bucket: str, prefix: str = "", *, limit: int = 1000) -> List[ObjectStat]:
        """Lists objects matching a key prefix within a bucket."""
        ...

    @abstractmethod
    async def presign_get(self, bucket: str, key: str, *, expires_in: int = 900) -> str:
        """Generates a temporary signed URL for downloading/viewing an object."""
        ...

    @abstractmethod
    async def presign_put(self, bucket: str, key: str, *, expires_in: int = 900) -> str:
        """Generates a temporary signed URL for uploading an object."""
        ...
