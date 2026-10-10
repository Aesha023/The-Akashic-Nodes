"""Delft3D Flexible Mesh execution runner supporting CPU, Remote, and Import modes."""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tarfile
import time
from pathlib import Path

from pravahx.config.schema import Delft3DFMMode
from pravahx.engines.base import (
    EngineStatus,
    PreparedCase,
    RawResult,
    compute_file_hash,
)
from pravahx.errors import EngineError

logger = logging.getLogger(__name__)


class Delft3DRunner:
    """Manages Delft3D Flexible Mesh simulation runs across CPU, Remote, and Import modes."""

    def __init__(
        self,
        bin_dir: Path | None = None,
        timeout_s: float = 3600.0,
    ) -> None:
        self.bin_dir = bin_dir or self._discover_bin_dir()
        self.timeout_s = timeout_s

    @staticmethod
    def _discover_bin_dir() -> Path | None:
        """Discover Delft3D binary directory from environment or default locations."""
        env_path = os.getenv("DELFT3DFM_PATH") or os.getenv("PRAVAHX_DELFT3DFM_BIN")
        if env_path:
            p = Path(env_path)
            if p.exists():
                return p
        return None

    def run(
        self,
        case: PreparedCase,
        mode: Delft3DFMMode | str = Delft3DFMMode.CPU,
        import_source: Path | None = None,
    ) -> RawResult:
        """Execute Delft3D FM simulation or import precomputed results.

        Args:
            case: Prepared simulation case.
            mode: Execution mode ('cpu', 'remote', or 'precomputed'/'import').
            import_source: Path to precomputed directory or tar.gz archive.

        Returns:
            RawResult with solver execution status, output directory, and logs.
        """
        mode_str = str(mode).lower()
        if mode_str in (
            "import",
            Delft3DFMMode.PRECOMPUTED.value,
        ):
            return self._run_import(case, import_source)
        elif mode_str == Delft3DFMMode.REMOTE.value:
            return self._run_remote_package(case)
        elif mode_str == Delft3DFMMode.CPU.value:
            return self._run_cpu(case)
        else:
            raise EngineError(
                f"Unsupported Delft3DFM execution mode: {mode}", engine="delft3d_fm"
            )

    def _run_cpu(self, case: PreparedCase) -> RawResult:
        """Execute Delft3D FM locally on CPU."""
        output_dir = case.case_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        log_path = output_dir / "delft3dfm.log"

        start_time = time.perf_counter()

        dflowfm_bin = self._find_binary("dflowfm")
        mdu_name = case.metadata.get("case_mdu", "FlowFM.mdu")
        mdu_path = case.case_dir / mdu_name

        if dflowfm_bin:
            logger.info("Executing Delft3D FM with binary: %s", dflowfm_bin)
            try:
                cmd = [
                    str(dflowfm_bin),
                    "--autostart",
                    str(mdu_path),
                ]
                with open(log_path, "w", encoding="utf-8") as log_file:
                    log_file.write(f"=== Delft3D FM Command: {' '.join(cmd)} ===\n")
                    subprocess.run(
                        cmd,
                        cwd=str(case.case_dir),
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        timeout=self.timeout_s,
                        check=True,
                    )

                wall_time = time.perf_counter() - start_time
                return RawResult(
                    engine_name="delft3d_fm",
                    status=EngineStatus.FINISHED,
                    output_dir=output_dir,
                    log_path=log_path,
                    wall_time_s=wall_time,
                    exit_code=0,
                )

            except Exception as e:
                wall_time = time.perf_counter() - start_time
                return RawResult(
                    engine_name="delft3d_fm",
                    status=EngineStatus.FAILED,
                    output_dir=output_dir,
                    log_path=log_path,
                    wall_time_s=wall_time,
                    exit_code=1,
                    error_message=str(e),
                )
        else:
            raise EngineError(
                "Delft3D FM CPU binary not found. Set DUALSPHYSICS_PATH or PRAVAHX_DELFT3DFM_BIN.",
                engine="delft3d_fm",
            )

    def _run_remote_package(self, case: PreparedCase) -> RawResult:
        """Package case files for remote Linux worker execution (e.g. Colab)."""
        output_dir = case.case_dir / "remote_package"
        output_dir.mkdir(parents=True, exist_ok=True)
        log_path = output_dir / "package.log"

        start_time = time.perf_counter()
        mdu_name = case.metadata.get("case_mdu", "FlowFM.mdu")
        case_base = mdu_name.replace(".mdu", "")

        # Create shell script for remote execution
        script_path = output_dir / "run_linux.sh"
        script_content = r"""#!/bin/bash
set -e
echo "=== Running Delft3D FM Simulation ==="

# Build LD_LIBRARY_PATH dynamically
INTEL_LIBS_DIR=""
if [ -d "/opt/intel" ]; then
    echo "Finding Intel libraries..."
    DIRS=$(find /opt/intel -type f \\( -name "libifcore.so*" -o -name "libimf.so*" \\
        -o -name "libiomp5.so*" -o -name "libmpi.so.12*" \\) \\
        -exec dirname {{}} \\; | sort -u | tr '\\n' ':' | sed 's/:$//')
    if [ -n "$DIRS" ]; then
        INTEL_LIBS_DIR=":$DIRS"
    fi
fi

export LD_LIBRARY_PATH=/content/delft3d_bin/lib${INTEL_LIBS_DIR}:$LD_LIBRARY_PATH
echo "Final LD_LIBRARY_PATH=$LD_LIBRARY_PATH"

echo "Checking missing dependencies with ldd:"
ldd /content/delft3d_bin/bin/dflowfm | grep "not found" || echo "All OK."

# Run D-Flow FM
/content/delft3d_bin/bin/dflowfm --autostartstop {mdu_name} || exit 1

# Generate Hash Manifest of output NetCDF and log files
echo "=== Generating Hash Manifest ==="
python3 -c "
import hashlib, json, os, glob
manifest = {{'files': {{}}}}
# D-Flow FM outputs files like DFM_OUTPUT_FlowFM/FlowFM_map.nc
output_dir = 'DFM_OUTPUT_{case_base}'
if os.path.exists(output_dir):
    for root, _, files in os.walk(output_dir):
        for f in files:
            p = os.path.join(root, f)
            with open(p, 'rb') as fp:
                manifest['files'][p] = hashlib.sha256(fp.read()).hexdigest()
with open(os.path.join(output_dir, 'manifest.json'), 'w') as mf:
    json.dump(manifest, mf, indent=2)
"
echo "=== Simulation Complete. Manifest Generated. ==="
"""
        with open(script_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(script_content)

        # Create package tar.gz containing the entire case directory
        # (since D-Flow FM needs mdu, ext, bc, etc.)
        archive_path = output_dir / f"{case_base}_linux_package.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            # Add all files in case_dir except remote_package
            for item in case.case_dir.iterdir():
                if item.name == "remote_package":
                    continue
                tar.add(item, arcname=item.name)
            tar.add(script_path, arcname="run_linux.sh")

        wall_time = time.perf_counter() - start_time
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"Remote package created at: {archive_path}\n")
            f.write(f"Package hash (SHA-256): {compute_file_hash(archive_path)}\n")

        return RawResult(
            engine_name="delft3d_fm",
            status=EngineStatus.FINISHED,
            output_dir=output_dir,
            log_path=log_path,
            wall_time_s=wall_time,
            exit_code=0,
        )

    def _run_import(self, case: PreparedCase, import_source: Path | None) -> RawResult:
        """Import precomputed Delft3D simulation results and verify cryptographic hashes."""
        if not import_source or not import_source.exists():
            raise EngineError(
                f"Import source not found: {import_source}. "
                "Delft3D import mode requires a valid results directory or tar.gz archive.",
                engine="delft3d_fm",
            )

        output_dir = case.case_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        log_path = output_dir / "import_verification.log"

        start_time = time.perf_counter()

        if import_source.is_file() and (
            import_source.name.endswith(".tar.gz") or import_source.name.endswith(".tgz")
        ):
            logger.info("Extracting precomputed archive %s to %s", import_source, output_dir)
            with tarfile.open(import_source, "r:gz") as tar:
                tar.extractall(path=output_dir)
        elif import_source.is_dir():
            if import_source.resolve() != output_dir.resolve():
                logger.info("Copying precomputed results from %s to %s", import_source, output_dir)
                for item in import_source.iterdir():
                    dest = output_dir / item.name
                    if item.is_dir():
                        shutil.copytree(item, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, dest)
            else:
                logger.info(
                    "Import source matches output directory %s; skipping redundant copy",
                    output_dir
                )
        else:
            raise EngineError(f"Invalid import source type: {import_source}", engine="delft3d_fm")

        # In Delft3D, outputs are typically in a folder like DFM_OUTPUT_FlowFM
        mdu_name = case.metadata.get("case_mdu", "FlowFM.mdu")
        case_base = mdu_name.replace(".mdu", "")
        expected_dfm_dir = output_dir / f"DFM_OUTPUT_{case_base}"

        manifest_path = expected_dfm_dir / "manifest.json"
        if not manifest_path.exists():
            manifest_path = output_dir / "manifest.json"

        if not manifest_path.exists():
            raise EngineError(
                f"Missing manifest.json in imported Delft3D results at {output_dir}. "
                "Every precomputed import must include cryptographic SHA-256 hashes.",
                engine="delft3d_fm",
            )

        with open(manifest_path, encoding="utf-8") as f:
            manifest_data = json.load(f)

        expected_files = manifest_data.get("files", manifest_data)
        if not expected_files or not isinstance(expected_files, dict):
            raise EngineError("Empty file list in manifest.json", engine="delft3d_fm")

        verification_logs: list[str] = [
            "=== Delft3D Precomputed Result Verification ===",
            f"Import Source: {import_source}",
            f"Manifest Path: {manifest_path}",
            f"Total Files to Verify: {len(expected_files)}",
        ]

        for rel_path, expected_hash in expected_files.items():
            # Handle if the manifest stored paths starting with DFM_OUTPUT_...
            # and we are reading from within output_dir
            actual_file = output_dir / rel_path
            if not actual_file.exists():
                actual_file = expected_dfm_dir / Path(rel_path).name

            if not actual_file.exists():
                msg = f"Missing expected file in imported bundle: {rel_path}"
                logger.error(msg)
                raise EngineError(msg, engine="delft3d_fm")

            actual_hash = compute_file_hash(actual_file)
            if actual_hash != expected_hash:
                msg = (
                    f"Cryptographic hash mismatch for '{rel_path}'!\n"
                    f"  Expected: {expected_hash}\n"
                    f"  Actual:   {actual_hash}\n"
                    "Data integrity validation failed."
                )
                logger.error(msg)
                raise EngineError(msg, engine="delft3d_fm")

            verification_logs.append(f"[OK] {rel_path}: {actual_hash[:16]}...")

        verification_logs.append("All files verified successfully against SHA-256 manifest.")
        log_path.write_text("\n".join(verification_logs) + "\n", encoding="utf-8")

        wall_time = time.perf_counter() - start_time
        return RawResult(
            engine_name="delft3d_fm",
            status=EngineStatus.SUCCESS,
            output_dir=expected_dfm_dir if expected_dfm_dir.exists() else output_dir,
            log_path=log_path,
            wall_time_s=wall_time,
            exit_code=0,
        )

    def _find_binary(self, name: str) -> Path | None:
        """Find executable binary on system or in bin_dir."""
        suffixes = ["", ".exe", "_win64.exe"]
        candidates = [f"{name}{s}" for s in suffixes]

        if self.bin_dir:
            for cand in candidates:
                p = self.bin_dir / cand
                if p.exists():
                    return p

        for cand in candidates:
            found = shutil.which(cand)
            if found:
                return Path(found)

        return None
