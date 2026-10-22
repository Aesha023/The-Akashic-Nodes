"""Integration test for MinIO/S3 object storage adapter (B1. Platform Core)."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

import pytest
from botocore.stub import Stubber

if TYPE_CHECKING:
    from pathlib import Path

from backend.app.core.storage import ObjectStorageAdapter


@pytest.mark.integration
def test_storage_adapter_initialization() -> None:
    """Verify ObjectStorageAdapter initializes with settings."""
    adapter = ObjectStorageAdapter(
        endpoint_url="http://localhost:9000",
        access_key="test_access",
        secret_key="test_secret",
        region_name="us-east-1",
    )
    assert adapter.endpoint_url == "http://localhost:9000"
    assert adapter.access_key == "test_access"
    assert adapter.region_name == "us-east-1"


@pytest.mark.integration
def test_storage_adapter_operations_with_stubber(tmp_path: Path) -> None:
    """Verify upload, download, exists, and presigned URL operations via boto3 stubber."""
    adapter = ObjectStorageAdapter(
        endpoint_url="http://localhost:9000",
        access_key="test_access",
        secret_key="test_secret",
        default_bucket="pravahx-artifacts",
    )

    with Stubber(adapter.client) as stubber:
        # 1. head_bucket (bucket exists)
        stubber.add_response("head_bucket", {}, {"Bucket": "pravahx-artifacts"})
        assert adapter.ensure_bucket_exists("pravahx-artifacts") is True

        # 2. put_object (upload_bytes)
        test_bytes = b"Sample raster or manifest payload"
        stubber.add_response(
            "put_object",
            {},
            {
                "Bucket": "pravahx-artifacts",
                "Key": "runs/run_01/manifest.json",
                "Body": test_bytes,
                "ContentType": "application/json",
            },
        )
        uri = adapter.upload_bytes(
            data=test_bytes,
            remote_key="runs/run_01/manifest.json",
            content_type="application/json",
        )
        assert uri == "s3://pravahx-artifacts/runs/run_01/manifest.json"

        # 3. get_object (download_bytes)
        body_stream = io.BytesIO(test_bytes)
        stubber.add_response(
            "get_object",
            {"Body": body_stream},
            {"Bucket": "pravahx-artifacts", "Key": "runs/run_01/manifest.json"},
        )
        downloaded = adapter.download_bytes("runs/run_01/manifest.json")
        assert downloaded == test_bytes

        # 4. head_object (exists check)
        stubber.add_response(
            "head_object",
            {"ContentLength": len(test_bytes)},
            {"Bucket": "pravahx-artifacts", "Key": "runs/run_01/manifest.json"},
        )
        assert adapter.exists("runs/run_01/manifest.json") is True

        # 5. delete_object
        stubber.add_response(
            "delete_object",
            {},
            {"Bucket": "pravahx-artifacts", "Key": "runs/run_01/manifest.json"},
        )
        assert adapter.delete_file("runs/run_01/manifest.json") is True


@pytest.mark.integration
def test_storage_adapter_presigned_url() -> None:
    """Verify generation of presigned download URL."""
    adapter = ObjectStorageAdapter(
        endpoint_url="http://localhost:9000",
        access_key="test_access",
        secret_key="test_secret",
        default_bucket="pravahx-exports",
    )
    url = adapter.generate_presigned_url(
        remote_key="briefs/ganga_tier0_brief.pdf",
        expires_in_seconds=1800,
    )
    assert url is not None
    assert "ganga_tier0_brief.pdf" in url
    assert "X-Amz-Signature=" in url
