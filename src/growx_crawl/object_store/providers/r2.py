import asyncio
from datetime import datetime, timezone
import hashlib
import hmac
import logging
import os
from typing import Any, AsyncIterator, Dict, List, Optional, Union
from urllib.parse import quote, urlencode

import httpx

from growx_crawl.object_store.base import ObjectStore
from growx_crawl.object_store.errors import (
    ObjectAccessDenied,
    ObjectConfigurationError,
    ObjectNotFound,
    ObjectStoreError,
    ObjectUploadFailed,
)
from growx_crawl.object_store.hashing import compute_sha256, maybe_compress, maybe_decompress
from growx_crawl.object_store.models import ObjectStat

logger = logging.getLogger("growx_crawl.object_store.r2")


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _get_signature_key(secret_key: str, date_stamp: str, region: str, service: str) -> bytes:
    k_date = _sign(f"AWS4{secret_key}".encode("utf-8"), date_stamp)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    k_signing = _sign(k_service, "aws4_request")
    return k_signing


class R2ObjectStore(ObjectStore):
    """
    Cloudflare R2 (S3-compatible) ObjectStore implementation using pure-Python
    AWS Signature Version 4 (SigV4) and asynchronous httpx client.
    Requires no heavy external dependencies (zero boto3 requirement).
    """

    def __init__(
        self,
        account_id: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        region: str = "auto",
    ):
        self.account_id = account_id or os.environ.get("R2_ACCOUNT_ID", "")
        self.access_key = access_key_id or os.environ.get("R2_ACCESS_KEY_ID", "")
        self.secret_key = secret_access_key or os.environ.get("R2_SECRET_ACCESS_KEY", "")
        self.region = region

        if endpoint_url:
            self.endpoint = endpoint_url.rstrip("/")
        elif self.account_id:
            self.endpoint = f"https://{self.account_id}.r2.cloudflarestorage.com"
        else:
            self.endpoint = os.environ.get("R2_ENDPOINT", "").rstrip("/")

    def _verify_config(self):
        if not self.access_key or not self.secret_key or not self.endpoint:
            raise ObjectConfigurationError(
                "Cloudflare R2 credentials missing. "
                "Ensure R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, and R2_SECRET_ACCESS_KEY are set."
            )

    def _generate_auth_headers(
        self,
        method: str,
        bucket: str,
        key: str,
        payload_hash: str,
        content_type: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        now = datetime.now(timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")

        host = self.endpoint.replace("https://", "").replace("http://", "").split("/")[0]
        canonical_uri = f"/{bucket}/{quote(key.lstrip('/'))}"

        headers = {
            "host": host,
            "x-amz-date": amz_date,
            "x-amz-content-sha256": payload_hash,
        }
        if content_type:
            headers["content-type"] = content_type
        if extra_headers:
            for k, v in extra_headers.items():
                headers[k.lower()] = str(v)

        # Build canonical request
        sorted_headers = sorted(headers.items())
        canonical_headers = "".join([f"{k}:{v}\n" for k, v in sorted_headers])
        signed_headers = ";".join([k for k, _ in sorted_headers])

        canonical_request = f"{method}\n{canonical_uri}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"

        # String to sign
        credential_scope = f"{date_stamp}/{self.region}/s3/aws4_request"
        string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"

        # Compute signature
        signing_key = _get_signature_key(self.secret_key, date_stamp, self.region, "s3")
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        auth_header = (
            f"AWS4-HMAC-SHA256 Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        headers["authorization"] = auth_header
        return headers

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
        self._verify_config()
        raw_bytes = data.encode("utf-8") if isinstance(data, str) else data
        content_hash = compute_sha256(raw_bytes)
        ct = content_type or "application/octet-stream"

        payload_to_upload, is_compressed = maybe_compress(raw_bytes, ct, enable_compression=compress)
        encoding = "gzip" if is_compressed else None

        payload_hash = hashlib.sha256(payload_to_upload).hexdigest()
        extra_headers = {}
        if encoding:
            extra_headers["content-encoding"] = encoding

        headers = self._generate_auth_headers(
            method="PUT",
            bucket=bucket,
            key=key,
            payload_hash=payload_hash,
            content_type=ct,
            extra_headers=extra_headers,
        )

        url = f"{self.endpoint}/{bucket}/{quote(key.lstrip('/'))}"

        # Bounded retry with exponential backoff (Section 33)
        retries = 3
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    res = await client.put(url, headers=headers, content=payload_to_upload)
                    if res.status_code in [200, 201]:
                        return ObjectStat(
                            bucket=bucket,
                            key=key,
                            size_bytes=len(raw_bytes),
                            content_type=ct,
                            content_encoding=encoding,
                            content_hash=content_hash,
                            last_modified=datetime.now(timezone.utc).isoformat(),
                            metadata=metadata or {},
                        )
                    elif res.status_code == 403:
                        raise ObjectAccessDenied(f"R2 access denied for {bucket}/{key}: {res.text}")
                    elif res.status_code == 404:
                        raise ObjectNotFound(f"R2 bucket not found: {bucket}")
                    else:
                        logger.warning(f"R2 upload attempt {attempt+1} failed ({res.status_code}): {res.text}")
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if attempt == retries - 1:
                    raise ObjectUploadFailed(f"Failed to upload to R2 after {retries} attempts: {e}")
                await asyncio.sleep(0.5 * (2**attempt))

        raise ObjectUploadFailed(f"Failed to upload {key} to R2")

    async def get(self, bucket: str, key: str) -> bytes:
        self._verify_config()
        headers = self._generate_auth_headers(
            method="GET",
            bucket=bucket,
            key=key,
            payload_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # empty hash
        )
        url = f"{self.endpoint}/{bucket}/{quote(key.lstrip('/'))}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.get(url, headers=headers)
            if res.status_code == 404:
                raise ObjectNotFound(f"Object not found in R2: {bucket}/{key}")
            elif res.status_code == 403:
                raise ObjectAccessDenied(f"R2 access denied for {bucket}/{key}")
            elif res.status_code != 200:
                raise ObjectStoreError(f"R2 get failed ({res.status_code}): {res.text}")

            encoding = res.headers.get("content-encoding", "")
            return maybe_decompress(res.content, encoding)

    async def stream(self, bucket: str, key: str, chunk_size: int = 65536) -> AsyncIterator[bytes]:
        data = await self.get(bucket, key)
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]

    async def delete(self, bucket: str, key: str) -> bool:
        self._verify_config()
        headers = self._generate_auth_headers(
            method="DELETE",
            bucket=bucket,
            key=key,
            payload_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )
        url = f"{self.endpoint}/{bucket}/{quote(key.lstrip('/'))}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.delete(url, headers=headers)
            return res.status_code in [200, 204]

    async def exists(self, bucket: str, key: str) -> bool:
        try:
            await self.stat(bucket, key)
            return True
        except ObjectNotFound:
            return False

    async def stat(self, bucket: str, key: str) -> ObjectStat:
        self._verify_config()
        headers = self._generate_auth_headers(
            method="HEAD",
            bucket=bucket,
            key=key,
            payload_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )
        url = f"{self.endpoint}/{bucket}/{quote(key.lstrip('/'))}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.head(url, headers=headers)
            if res.status_code == 404:
                raise ObjectNotFound(f"Object not found in R2: {bucket}/{key}")
            elif res.status_code != 200:
                raise ObjectStoreError(f"R2 HEAD failed ({res.status_code})")

            size = int(res.headers.get("content-length", 0))
            ct = res.headers.get("content-type", "application/octet-stream")
            encoding = res.headers.get("content-encoding")
            etag = res.headers.get("etag", "").strip('"')

            return ObjectStat(
                bucket=bucket,
                key=key,
                size_bytes=size,
                content_type=ct,
                content_encoding=encoding,
                content_hash=etag,
                last_modified=res.headers.get("last-modified", datetime.now(timezone.utc).isoformat()),
            )

    async def list(self, bucket: str, prefix: str = "", *, limit: int = 1000) -> List[ObjectStat]:
        # For Phase 02 minimal listing via S3 REST
        return []

    async def presign_get(self, bucket: str, key: str, *, expires_in: int = 900) -> str:
        """Generates standard S3 SigV4 query-parameter signed URL for R2 object download."""
        self._verify_config()
        now = datetime.now(timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")

        host = self.endpoint.replace("https://", "").replace("http://", "").split("/")[0]
        credential_scope = f"{date_stamp}/{self.region}/s3/aws4_request"
        canonical_uri = f"/{bucket}/{quote(key.lstrip('/'))}"

        query_params = {
            "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
            "X-Amz-Credential": f"{self.access_key}/{credential_scope}",
            "X-Amz-Date": amz_date,
            "X-Amz-Expires": str(expires_in),
            "X-Amz-SignedHeaders": "host",
        }

        canonical_query = urlencode(sorted(query_params.items()))
        canonical_headers = f"host:{host}\n"
        canonical_request = f"GET\n{canonical_uri}\n{canonical_query}\n{canonical_headers}\nhost\nUNSIGNED-PAYLOAD"

        string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        signing_key = _get_signature_key(self.secret_key, date_stamp, self.region, "s3")
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        return f"{self.endpoint}{canonical_uri}?{canonical_query}&X-Amz-Signature={signature}"

    async def presign_put(self, bucket: str, key: str, *, expires_in: int = 900) -> str:
        self._verify_config()
        now = datetime.now(timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")

        host = self.endpoint.replace("https://", "").replace("http://", "").split("/")[0]
        credential_scope = f"{date_stamp}/{self.region}/s3/aws4_request"
        canonical_uri = f"/{bucket}/{quote(key.lstrip('/'))}"

        query_params = {
            "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
            "X-Amz-Credential": f"{self.access_key}/{credential_scope}",
            "X-Amz-Date": amz_date,
            "X-Amz-Expires": str(expires_in),
            "X-Amz-SignedHeaders": "host",
        }

        canonical_query = urlencode(sorted(query_params.items()))
        canonical_headers = f"host:{host}\n"
        canonical_request = f"PUT\n{canonical_uri}\n{canonical_query}\n{canonical_headers}\nhost\nUNSIGNED-PAYLOAD"

        string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        signing_key = _get_signature_key(self.secret_key, date_stamp, self.region, "s3")
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        return f"{self.endpoint}{canonical_uri}?{canonical_query}&X-Amz-Signature={signature}"
