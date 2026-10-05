# PravahX Science and Methods

This document records the formulae, methods, assumptions, and data sources used in the system.

## Roughness (Manning's n)
The mapping from ESA WorldCover 10m v200 classes to Manning's n values is based on standard literature (e.g., Chow, 1959, *Open-channel hydraulics*) adapted for land cover classifications commonly used in large-scale flood modelling (e.g., Baugh et al., 2013, *A routing model for continental-scale hydrology*). 

The table used is:
- 10: Trees (0.100)
- 20: Shrubland (0.070)
- 30: Grassland (0.035)
- 40: Cropland (0.040)
- 50: Built-up (0.015 - note: represents smooth surfaces between buildings; buildings themselves should ideally be raised in the DEM or treated with high roughness)
- 60: Bare / sparse vegetation (0.025)
- 70: Snow and ice (0.020)
- 80: Permanent water bodies (0.030)
- 90: Herbaceous wetland (0.050)
- 95: Mangroves (0.080)
- 100: Moss and lichen (0.030)

## Tier 0: Rapid Envelope (HAND)
Tier 0 produces a rapid, conservative inundation envelope without solving the shallow water equations.

**Method:**
1. Derive a reach-averaged synthetic cross-section from the Height Above Nearest Drainage (HAND) raster. The area is the integral of depth (Stage - HAND) over the inundated cells, divided by the reach length. The wetted perimeter is approximated by the wetted width.
2. Solve Manning's equation iteratively (bisection search) to find the stage $S$ that conveys the peak discharge $Q_{peak}$:
   $$Q = \frac{1}{n} A R^{2/3} S_0^{1/2}$$
   where $R = A/P$, $n$ is the reach-averaged roughness, and $S_0$ is the bed slope.
3. Mark all cells where $HAND < S$ as inundated.

**Peak Attenuation Rule:**
For Tier 0, the peak discharge is currently not attenuated downstream; the initial breach peak is conservatively applied to the entire near-field reach. Future enhancements or subsequent tiers (Tier 1) will account for flood wave attenuation. This method is intentionally conservative and intended only as a first estimate.
