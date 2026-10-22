"""Unit test verifying consistency between BACKEND_STATUS.md and VALIDATION.md."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_backend_status_engine_table_numbers_verbatim_in_validation() -> None:
    """Every numeric value in BACKEND_STATUS engine table must appear in VALIDATION.md."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    check_script = repo_root / "scripts" / "check_engine_table.py"

    result = subprocess.run(
        [sys.executable, str(check_script)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"check_engine_table.py failed:\n{result.stdout}\n{result.stderr}"
    )
