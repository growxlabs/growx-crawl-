import gzip
import hashlib
from typing import Tuple, Union


def compute_sha256(data: Union[bytes, str]) -> str:
    """Computes SHA-256 hexadecimal hash of bytes or string."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def maybe_compress(
    data: Union[bytes, str],
    content_type: str,
    enable_compression: bool = True,
) -> Tuple[bytes, bool]:
    """
    Compresses text payloads (HTML, Markdown, JSON) using gzip per Section 12.
    Binary/already-compressed media (PNG, WEBP, PDF, XLSX) are untouched.
    Returns (processed_bytes, is_compressed).
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    if not enable_compression:
        return data, False

    ct = content_type.lower()
    compressible_types = [
        "text/html",
        "text/plain",
        "text/markdown",
        "application/json",
        "application/x-ndjson",
        "text/csv",
        "application/xml",
        "text/xml",
    ]

    if any(compressible in ct for compressible in compressible_types) and len(data) > 256:
        compressed = gzip.compress(data, compresslevel=6)
        # Only use compressed if it actually reduced size
        if len(compressed) < len(data):
            return compressed, True

    return data, False


def maybe_decompress(data: bytes, content_encoding: str) -> bytes:
    """Decompresses gzip payload if content_encoding is gzip."""
    if content_encoding and content_encoding.lower() == "gzip":
        try:
            return gzip.decompress(data)
        except Exception:
            return data
    return data
