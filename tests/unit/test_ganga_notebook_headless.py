"""Test headless end-to-end execution of PravahX_Ganga_Tier1.ipynb notebook."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.show = lambda *args, **kwargs: None


def test_ganga_tier1_notebook_headless(tmp_path: Path) -> None:
    """Execute all code cells of PravahX_Ganga_Tier1.ipynb in headless mode."""
    nb_path = Path("notebooks/PravahX_Ganga_Tier1.ipynb").resolve()
    assert nb_path.exists(), f"Notebook not found at {nb_path}"

    with open(nb_path, encoding="utf-8") as f:
        nb = json.load(f)

    # Prepare isolated content environment
    content_dir = tmp_path / "content"
    content_dir.mkdir(parents=True, exist_ok=True)
    os.environ["PRAVAHX_CONTENT_DIR"] = str(content_dir)
    os.environ["PRAVAHX_STUB_DFLOWFM"] = "1"

    drive_dir = content_dir / "drive" / "MyDrive" / "PravahX"
    ganga_in_dir = drive_dir / "ganga_inputs"
    ganga_in_dir.mkdir(parents=True, exist_ok=True)

    repo_inputs = Path("data/ganga_inputs").resolve()
    for f in repo_inputs.iterdir():
        if f.is_file():
            shutil.copy(f, ganga_in_dir / f.name)

    # Engine stub directory
    bin_dir = content_dir / "delft3d_bin" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    dflowfm_bin = bin_dir / "dflowfm"
    dflowfm_bin.write_text("#!/bin/sh\nexit 0\n")

    ns = {
        "__name__": "__main__",
    }

    executed_cells = 0
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue

        src = "".join(cell["source"])
        first_line = cell["source"][0].strip() if cell["source"] else f"Cell {i}"
        try:
            exec(src, ns)
            executed_cells += 1
        except Exception as e:
            pytest.fail(f"Cell {i} ({first_line}) failed with {type(e).__name__}: {e}")

    assert executed_cells >= 10, f"Expected at least 10 code cells, executed {executed_cells}"
