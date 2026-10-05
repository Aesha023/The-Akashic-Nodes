"""PravahX command-line interface.

Usage:
    pravahx run scenario.yaml          Run a scenario from a config file
    pravahx validate scenario.yaml     Validate a config without running
    pravahx verify <run_dir>           Verify artefact hashes of a completed run
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
import structlog

from pravahx.config.schema import ScenarioConfig, load_scenario_config
from pravahx.pipeline.provenance import RunManifest, verify_artifacts

logger = structlog.get_logger()


@click.group()
@click.version_option(package_name="pravahx")
def main() -> None:
    """PravahX — Dam break and river blockage inundation modelling."""


@main.command()
@click.argument("config_path", type=click.Path(exists=True, path_type=Path))
def validate(config_path: Path) -> None:
    """Validate a scenario config file without running anything."""
    try:
        config = load_scenario_config(config_path)
    except Exception as exc:
        click.secho(f"Invalid config: {exc}", fg="red", err=True)
        sys.exit(1)

    click.secho(
        f"Config valid: scenario '{config.scenario.name}' "
        f"(id={config.scenario.id}, type={config.scenario.type.value})",
        fg="green",
    )

    # Summarise enabled tiers
    tiers = []
    if config.tiers.tier0.enabled:
        tiers.append("Tier 0 (HAND)")
    if config.tiers.delft3d_fm.enabled:
        tiers.append("Tier 1 (Delft3D FM)")
    if config.tiers.dualsphysics.enabled:
        mode = config.tiers.dualsphysics.mode.value
        tiers.append(f"Tier 2 (DualSPHysics, mode={mode})")
    click.echo(f"Enabled tiers: {', '.join(tiers) or 'none'}")

    if config.compare.enabled:
        click.echo(f"Comparison: enabled (max refinements: {config.compare.max_refinements})")
    if config.cascade.enabled:
        click.echo("Cascade: enabled")
    if config.gee.enabled:
        click.echo("Earth Engine: enabled")
    if config.impact.enabled:
        click.echo("Impact: enabled")
    click.echo(f"Exports: {', '.join(e.value for e in config.exports)}")


@main.command()
@click.argument("config_path", type=click.Path(exists=True, path_type=Path))
@click.option("--work-dir", type=click.Path(path_type=Path), default=None, help="Working directory for run outputs.")
def run(config_path: Path, work_dir: Path | None) -> None:
    """Run a scenario from a config file.

    This is a placeholder for Phase 0. The full orchestrator is built in later phases.
    """
    try:
        config = load_scenario_config(config_path)
    except Exception as exc:
        click.secho(f"Invalid config: {exc}", fg="red", err=True)
        sys.exit(1)

    click.secho(
        f"Scenario '{config.scenario.name}' validated. "
        "Pipeline orchestrator not yet built (Phase 0 — foundations only).",
        fg="yellow",
    )
    click.echo("Use 'pravahx validate' to check configs. Full runs arrive in Phase 1+.")


@main.command()
@click.argument("run_dir", type=click.Path(exists=True, path_type=Path))
def verify(run_dir: Path) -> None:
    """Verify artefact hashes of a completed run."""
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        click.secho(f"No manifest.json found in {run_dir}", fg="red", err=True)
        sys.exit(1)

    manifest = RunManifest.load(manifest_path)
    issues = verify_artifacts(manifest, run_dir)

    if issues:
        click.secho(f"Verification FAILED — {len(issues)} issue(s):", fg="red")
        for issue in issues:
            click.echo(f"  • {issue}")
        sys.exit(1)
    else:
        click.secho(
            f"Verification PASSED — {len(manifest.artifacts)} artefact(s) intact.",
            fg="green",
        )


if __name__ == "__main__":
    main()
