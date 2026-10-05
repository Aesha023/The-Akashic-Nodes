"""Tests for the typed error hierarchy."""

from __future__ import annotations

from pravahx.errors import (
    AuthError,
    ConfigError,
    ConfigFieldError,
    CouplingError,
    DataCorruptError,
    DataError,
    EgressBlockedError,
    EngineError,
    EnginePrecomputedError,
    EngineTimeoutError,
    HashMismatchError,
    PipelineError,
    PravahXError,
    StageError,
    VolumeConservationError,
)


class TestErrorHierarchy:
    """Verify inheritance and structured detail on all error types."""

    def test_base_error(self) -> None:
        err = PravahXError("test", detail={"key": "val"})
        assert err.code == "INTERNAL_ERROR"
        assert err.message == "test"
        assert err.detail == {"key": "val"}
        assert str(err) == "test"

    def test_config_field_error(self) -> None:
        err = ConfigFieldError("bad value", field="scenario.id", value="")
        assert isinstance(err, ConfigError)
        assert isinstance(err, PravahXError)
        assert err.code == "CONFIG_FIELD_INVALID"
        assert err.detail["field"] == "scenario.id"

    def test_engine_error_with_log(self) -> None:
        err = EngineError("solver crashed", engine="delft3d_fm", log_path="/tmp/solver.log")
        assert err.code == "ENGINE_ERROR"
        assert err.engine == "delft3d_fm"
        assert err.detail["log_path"] == "/tmp/solver.log"

    def test_engine_timeout(self) -> None:
        err = EngineTimeoutError("exceeded 2h limit", engine="dualsphysics")
        assert isinstance(err, EngineError)
        assert err.code == "ENGINE_TIMEOUT"

    def test_engine_precomputed_error(self) -> None:
        err = EnginePrecomputedError("hash mismatch in import", engine="dualsphysics")
        assert err.code == "ENGINE_PRECOMPUTED_ERROR"
        assert isinstance(err, EngineError)

    def test_stage_error(self) -> None:
        err = StageError("terrain failed", stage="terrain", attempt=2)
        assert isinstance(err, PipelineError)
        assert err.code == "STAGE_ERROR"
        assert err.detail["stage"] == "terrain"
        assert err.detail["attempt"] == 2

    def test_hash_mismatch_error(self) -> None:
        err = HashMismatchError(
            "corrupted raster",
            path="/data/max_depth.tif",
            expected="abc",
            actual="def",
        )
        assert err.code == "HASH_MISMATCH"
        assert err.detail["expected"] == "abc"
        assert err.detail["actual"] == "def"

    def test_volume_conservation_error(self) -> None:
        err = VolumeConservationError(
            "volume lost at hand-off",
            expected_m3=1_000_000,
            actual_m3=900_000,
            tolerance=0.05,
        )
        assert err.code == "VOLUME_CONSERVATION_ERROR"
        assert abs(err.detail["error_fraction"] - 0.1) < 1e-9

    def test_egress_blocked(self) -> None:
        err = EgressBlockedError("outbound call to example.com blocked")
        assert err.code == "EGRESS_BLOCKED"

    def test_data_corrupt(self) -> None:
        err = DataCorruptError("DEM file corrupted")
        assert isinstance(err, DataError)
        assert isinstance(err, PravahXError)
