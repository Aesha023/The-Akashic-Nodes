"""Raster tile proxy and map visualization endpoints (Phase 7)."""

from __future__ import annotations

import io
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import rasterio
from fastapi import APIRouter, Depends, HTTPException, Response, status
from PIL import Image

from backend.app.core.auth import get_current_user

if TYPE_CHECKING:
    from backend.app.models.user import User

router = APIRouter(prefix="/tiles", tags=["tiles"])


@router.get("/{run_id}/{layer_name}/{z}/{x}/{y}.png")
async def get_raster_tile(
    run_id: str,
    layer_name: str,
    z: int,
    x: int,
    y: int,
    current_user: User = Depends(get_current_user),
) -> Response:
    """Generate or proxy an RGBA PNG tile for the specified hydrodynamic layer."""
    # Look for the raster in the run directory
    raster_path = Path("./runs") / run_id / f"{layer_name}.tif"
    if not raster_path.exists():
        # Check subdirectories
        matches = list((Path("./runs") / run_id).glob(f"**/{layer_name}.tif"))
        if matches:
            raster_path = matches[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Layer '{layer_name}' not found for run '{run_id}'.",
            )

    try:
        with rasterio.open(raster_path) as src:
            data = src.read(1)
            # Create a basic RGBA PNG representation of the tile
            norm = np.clip(data / max(1.0, float(np.max(data))), 0.0, 1.0)
            rgba = np.zeros((src.height, src.width, 4), dtype=np.uint8)
            rgba[..., 0] = (norm * 30).astype(np.uint8)
            rgba[..., 1] = (norm * 144).astype(np.uint8)
            rgba[..., 2] = (norm * 255).astype(np.uint8)
            rgba[..., 3] = (norm * 200).astype(np.uint8)

            img = Image.fromarray(rgba, mode="RGBA").resize((256, 256))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tile rendering error: {e}",
        ) from e
