"""Integration tests for MinIO / S3 object storage against live service container (P3)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from backend.app.core.storage import ObjectStorageAdapter


@pytest.fixture
def storage_adapter() -> ObjectStorageAdapter:
    adapter = ObjectStorageAdapter()
    if not adapter.is_available():
        # Try to ensure bucket or check availability
        try:
            adapter.ensure_bucket_exists()
        except Exception as exc:
            pytest.skip(f"Live MinIO / S3 service not reachable at {adapter.endpoint_url}: {exc}")
    return adapter


def test_minio_bucket_lifecycle_and_upload(
    storage_adapter: ObjectStorageAdapter, tmp_path: Path
) -> None:
    """Verify live MinIO bucket creation, file upload, download, and SHA-256 integrity."""
    test_bucket = "pravahx-integration-test"
    assert storage_adapter.ensure_bucket_exists(test_bucket) is True

    test_content = b"PravahX Hydrodynamic Simulation Artifact Payload 2026"
    test_file = tmp_path / "test_artifact.bin"
    test_file.write_bytes(test_content)
    expected_sha256 = hashlib.sha256(test_content).hexdigest()

    remote_key = "runs/integration_test_run/artifact.bin"
    uploaded_url = storage_adapter.upload_file(
        local_path=test_file,
        remote_key=remote_key,
        bucket=test_bucket,
        content_type="application/octet-stream",
    )
    assert uploaded_url

    download_target = tmp_path / "downloaded_artifact.bin"
    storage_adapter.download_file(
        remote_key=remote_key,
        local_path=download_target,
        bucket=test_bucket,
    )
    assert download_target.exists()
    downloaded_content = download_target.read_bytes()
    assert downloaded_content == test_content
    assert hashlib.sha256(downloaded_content).hexdigest() == expected_sha256

    # Presigned URL verification
    presigned = storage_adapter.generate_presigned_url(
        remote_key=remote_key,
        bucket=test_bucket,
        expires_in=300,
    )
    assert "http" in presigned and remote_key in presigned

    # Cleanup
    storage_adapter.delete_file(remote_key=remote_key, bucket=test_bucket)
