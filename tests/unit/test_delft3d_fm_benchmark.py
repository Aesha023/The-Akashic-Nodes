import tarfile
from pathlib import Path

import netCDF4

from pravahx.engines.delft3d_fm.benchmark import Delft3DBenchmark


def test_delft3d_benchmark_generation(tmp_path: Path):
    """Test that the pure Python generator produces valid Delft3D files."""
    benchmark = Delft3DBenchmark(length=2000, width=50, dx=5.0)
    case_dir = benchmark.generate_case(tmp_path)

    # Check files produced
    assert case_dir.exists()
    assert (case_dir / "grid_net.nc").exists()
    assert (case_dir / "upstream.pol").exists()
    assert (case_dir / "initial.ini").exists()
    assert (case_dir / "ritter.mdu").exists()
    assert (case_dir / "run_linux.sh").exists()

    # Check NetCDF mesh properties
    ds = netCDF4.Dataset(case_dir / "grid_net.nc", "r")
    assert "NetNode_x" in ds.variables
    assert "NetElemNode" in ds.variables
    assert len(ds.variables["NetNode_x"][:]) == (401 * 11)  # (2000/5 + 1) * (50/5 + 1)
    ds.close()

    # Check MDU parses back (or at least has no obsolete keys)
    mdu_text = (case_dir / "ritter.mdu").read_text(encoding="utf-8")
    assert "mapformat = 4" in mdu_text.lower()
    assert "initial.ini" in mdu_text.lower()
    assert "TransportMethod" not in [
        line.split("=")[0].strip() for line in mdu_text.splitlines() if not line.startswith("#")
    ]

    # Check remote packaging
    tar_path = tmp_path / "ritter_package.tar.gz"
    benchmark.package_for_remote(case_dir, tar_path)
    assert tar_path.exists()

    with tarfile.open(tar_path, "r:gz") as tar:
        names = tar.getnames()
        assert "ritter.mdu" in names
        assert "grid_net.nc" in names
        assert "run_linux.sh" in names
