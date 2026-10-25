"""Unit tests for PostGIS and MinIO backup and restore scripts (B4 Feature F20)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from scripts.backup_minio import run_minio_backup
from scripts.backup_postgis import run_backup
from scripts.restore_minio import run_minio_restore
from scripts.restore_postgis import run_restore

if TYPE_CHECKING:
    from pathlib import Path


def test_postgis_backup_and_restore(tmp_path: Path) -> None:
    backup_file = run_backup(output_dir=tmp_path)
    assert backup_file.exists()
    assert backup_file.stat().st_size > 0

    success = run_restore(backup_file=backup_file)
    assert success is True


def test_minio_backup_and_restore(tmp_path: Path) -> None:
    archive_file = run_minio_backup(output_dir=tmp_path)
    assert archive_file.exists()
    assert archive_file.stat().st_size > 0

    restored_count = run_minio_restore(archive_path=archive_file)
    assert restored_count >= 1
