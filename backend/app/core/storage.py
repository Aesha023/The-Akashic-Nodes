"""Object storage adapter for MinIO / AWS S3 using boto3 (B1. Platform Core)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from backend.app.core.config import Settings

logger = logging.getLogger(__name__)


class ObjectStorageAdapter:
    """S3-compatible object storage client for rasters, exports, and PDF briefs."""

    def __init__(
        self,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region_name: str | None = None,
        default_bucket: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.settings = Settings()
        self.endpoint_url = endpoint_url or self.settings.s3_endpoint
        self.access_key = (
            access_key if access_key is not None else self.settings.s3_access_key.get_secret_value()
        )
        self.secret_key = (
            secret_key if secret_key is not None else self.settings.s3_secret_key.get_secret_value()
        )
        self.region_name = region_name or self.settings.s3_region
        self.default_bucket = default_bucket or self.settings.s3_bucket_artifacts

        if client is not None:
            self._client = client
        else:
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url if self.endpoint_url else None,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region_name,
                config=Config(signature_version="s3v4"),
            )

    @property
    def client(self) -> Any:
        """Underlying boto3 S3 client."""
        return self._client

    def is_available(self) -> bool:
        """Check if object storage is reachable."""
        try:
            self._client.head_bucket(Bucket=self.default_bucket)
            return True
        except Exception:
            return False

    def ensure_bucket_exists(self, bucket: str | None = None) -> bool:
        """Create bucket if it does not already exist."""
        target_bucket = bucket or self.default_bucket
        try:
            self._client.head_bucket(Bucket=target_bucket)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchBucket"):
                create_kwargs: dict[str, Any] = {"Bucket": target_bucket}
                if self.region_name and self.region_name != "us-east-1":
                    create_kwargs["CreateBucketConfiguration"] = {
                        "LocationConstraint": self.region_name
                    }
                self._client.create_bucket(**create_kwargs)
                return True
            raise

    def upload_file(
        self,
        local_path: str | Path,
        remote_key: str,
        bucket: str | None = None,
        content_type: str | None = None,
    ) -> str:
        """Upload a local file to object storage."""
        target_bucket = bucket or self.default_bucket
        p = Path(local_path)
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"Source file not found: {local_path}")

        extra_args: dict[str, Any] = {}
        if content_type:
            extra_args["ContentType"] = content_type

        self._client.upload_file(
            Filename=str(p),
            Bucket=target_bucket,
            Key=remote_key,
            ExtraArgs=extra_args if extra_args else None,
        )
        return f"s3://{target_bucket}/{remote_key}"

    def download_file(
        self,
        remote_key: str,
        local_path: str | Path,
        bucket: str | None = None,
    ) -> Path:
        """Download an object from storage to a local path."""
        target_bucket = bucket or self.default_bucket
        dest = Path(local_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        self._client.download_file(
            Bucket=target_bucket,
            Key=remote_key,
            Filename=str(dest),
        )
        return dest

    def upload_bytes(
        self,
        data: bytes,
        remote_key: str,
        bucket: str | None = None,
        content_type: str | None = None,
    ) -> str:
        """Upload raw bytes to object storage."""
        target_bucket = bucket or self.default_bucket
        kwargs: dict[str, Any] = {
            "Bucket": target_bucket,
            "Key": remote_key,
            "Body": data,
        }
        if content_type:
            kwargs["ContentType"] = content_type

        self._client.put_object(**kwargs)
        return f"s3://{target_bucket}/{remote_key}"

    def download_bytes(
        self,
        remote_key: str,
        bucket: str | None = None,
    ) -> bytes:
        """Download an object's payload as bytes."""
        target_bucket = bucket or self.default_bucket
        response = self._client.get_object(Bucket=target_bucket, Key=remote_key)
        body: bytes = response["Body"].read()
        return body

    def exists(
        self,
        remote_key: str,
        bucket: str | None = None,
    ) -> bool:
        """Check if an object exists in storage."""
        target_bucket = bucket or self.default_bucket
        try:
            self._client.head_object(Bucket=target_bucket, Key=remote_key)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                return False
            raise

    def delete_file(
        self,
        remote_key: str,
        bucket: str | None = None,
    ) -> bool:
        """Delete an object from storage."""
        target_bucket = bucket or self.default_bucket
        try:
            self._client.delete_object(Bucket=target_bucket, Key=remote_key)
            return True
        except ClientError:
            return False

    def generate_presigned_url(
        self,
        remote_key: str,
        bucket: str | None = None,
        expires_in_seconds: int = 3600,
        http_method: str = "get_object",
    ) -> str:
        """Generate a time-limited signed URL for secure object access."""
        target_bucket = bucket or self.default_bucket
        url: str = self._client.generate_presigned_url(
            ClientMethod=http_method,
            Params={"Bucket": target_bucket, "Key": remote_key},
            ExpiresIn=expires_in_seconds,
        )
        return url
