"""
Domain exceptions for the GrowX Object Store subsystem per Section 35 specification.
Business modules must not depend directly on cloud provider exception types.
"""


class ObjectStoreError(Exception):
    """Base exception for all object storage operations."""
    pass


class ObjectNotFound(ObjectStoreError):
    """Raised when the requested object key or bucket does not exist."""
    pass


class ObjectAccessDenied(ObjectStoreError):
    """Raised when access credentials or signed URL tokens are invalid or expired."""
    pass


class ObjectUploadFailed(ObjectStoreError):
    """Raised when an upload operation fails after exhausting retries."""
    pass


class ObjectDownloadFailed(ObjectStoreError):
    """Raised when an object download or stream fails."""
    pass


class ObjectIntegrityError(ObjectStoreError):
    """Raised when an object content hash does not match the expected SHA-256 signature."""
    pass


class ObjectConfigurationError(ObjectStoreError):
    """Raised when storage configuration or bucket settings are invalid."""
    pass
