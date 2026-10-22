"""Raster tile proxy and map visualization endpoints (Phase 7 / Results Service)."""

from __future__ import annotations

import io
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import rasterio
from fastapi import APIRouter, Depends, HTTPException, Response, status
from PIL import Image

from backend.app.core.auth import get_optional_current_user

if TYPE_CHECKING:
    from backend.app.models.user import User

router = APIRouter(prefix="/tiles", tags=["tiles"])

# Transparent empty 256x256 PNG cache
_EMPTY_PNG: bytes | None = None


def _get_empty_png() -> bytes:
    global _EMPTY_PNG
    if _EMPTY_PNG is None:
        img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        _EMPTY_PNG = buf.getvalue()
    return _EMPTY_PNG


def _resolve_raster_path(run_id: str, layer_name: str) -> Path | None:
    """Find the raster file for a given run and layer name."""
    # 1. Special case: Tier-0 Ganga accepted benchmark run
    if run_id in ("tier0_ganga", "tier0_accepted", "ganga_tier0"):
        if layer_name.lower() in ("max_depth", "depth", "tier0_max_depth", "tier0_max_depth_cog"):
            for c in [
                Path("data/ganga_inputs/tier0_max_depth_cog.tif"),
                Path("data/ganga_inputs/tier0_max_depth.tif"),
            ]:
                if c.exists():
                    return c
        specific = Path("data/ganga_inputs") / f"{layer_name}.tif"
        if specific.exists():
            return specific
        return None

    # 2. Look in ./runs directory
    base_run = Path("./runs") / run_id
    direct_candidates = [
        base_run / f"{layer_name}.tif",
        base_run / f"{layer_name}_cog.tif",
        base_run / "tier0_max_depth_cog.tif",
        base_run / "tier0_max_depth.tif",
    ]
    for c in direct_candidates:
        if c.exists():
            return c

    # 3. Check glob matches in subdirectories
    matches = list(base_run.glob(f"**/{layer_name}*.tif"))
    if matches:
        return matches[0]

    return None


@router.get("/{run_id}/{layer_name}/{z}/{x}/{y}.png")
async def get_raster_tile(
    run_id: str,
    layer_name: str,
    z: int,
    x: int,
    y: int,
    current_user: User | None = Depends(get_optional_current_user),
) -> Response:
    """Generate or proxy an RGBA PNG tile for the specified hydrodynamic layer via rio-tiler."""
    raster_path = _resolve_raster_path(run_id, layer_name)
    if raster_path is None or not raster_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Layer '{layer_name}' not found for run '{run_id}'.",
        )

    # Use rio-tiler for fast native COG dynamic tile extraction
    try:
        from rio_tiler.colormap import cmap
        from rio_tiler.errors import TileOutsideBounds
        from rio_tiler.io import Reader

        with Reader(str(raster_path)) as image:
            try:
                img = image.tile(x, y, z)
                # Rescale depth values (e.g. 0 to 8m) and apply hydro colormap
                is_depth = "depth" in layer_name.lower() or "max_depth" in str(raster_path)
                rescale = ((0.01, 8.0),) if is_depth else None
                colormap = cmap.get("blues") if is_depth else None

                png_bytes = img.render(
                    img_format="PNG",
                    colormap=colormap,
                    rescale=rescale,
                )
                return Response(
                    content=png_bytes,
                    media_type="image/png",
                    headers={"Cache-Control": "public, max-age=86400"},
                )
            except TileOutsideBounds:
                return Response(
                    content=_get_empty_png(),
                    media_type="image/png",
                    headers={"Cache-Control": "public, max-age=86400"},
                )
    except ImportError:
        # Fallback to rasterio in minimal environments
        with rasterio.open(raster_path) as src:
            data = src.read(1)
            norm = np.clip(data / max(1.0, float(np.max(data))), 0.0, 1.0)
            rgba = np.zeros((src.height, src.width, 4), dtype=np.uint8)
            rgba[..., 0] = (norm * 30).astype(np.uint8)
            rgba[..., 1] = (norm * 144).astype(np.uint8)
            rgba[..., 2] = (norm * 255).astype(np.uint8)
            rgba[..., 3] = (norm * 200).astype(np.uint8)

            img_fb = Image.fromarray(rgba, mode="RGBA").resize((256, 256))
            buf = io.BytesIO()
            img_fb.save(buf, format="PNG")
            return Response(content=buf.getvalue(), media_type="image/png")
