"""Peng and Zhang (2012) landslide dam breach parameters."""

from typing import Literal


def compute_peng_zhang_2012(
    volume_m3: float, height_m: float, erodibility: Literal["high", "medium", "low"] = "medium"
) -> None:
    """Compute breach parameters for landslide dams (Peng and Zhang 2012).

    Raises:
        NotImplementedError: Until the exact regression coefficients from the paper
        (Landslides 9(1):13-31, DOI 10.1007/s10346-011-0271-y) are provided by the user.
    """
    raise NotImplementedError(
        "Method not available: Peng and Zhang (2012) equations not available from an "
        "accessible source."
    )
