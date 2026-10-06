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

**Main-Reach Drainage Normalization & Tributary Backwater Limits:**
In standard hydrologic HAND (Nobre et al., 2011; Rennó et al., 2008), the entire drainage network (including all minor mountain tributaries) is extracted. If HAND is calculated against all stream segments, every tributary bed receives $HAND = 0$. When a main-stem flood stage $S$ (e.g. 13.3 m) is applied across the domain, all tributary valleys are inundated along their full length (often 1–2 km into steep hillsides).

In physical dam-break and river-blockage hydraulics, the flood surge propagates along the main stem; water only backs up into tributaries where the water surface elevation of the main river exceeds the tributary bed elevation:
$$z(x, y) \le z_{\text{confluence}} + S$$

To model this accurately without full hydrodynamic 2D shallow-water simulations:
1. **Main-Reach Extraction:** The drainage corridor is isolated either downstream of the breach/dam source point or by tracing upstream from the maximum flow accumulation outlet along the primary flow corridor.
2. **Main-Stem HAND:** HAND is computed strictly relative to the main reach cells. Tributary flow paths follow D8 drainage downslope into their confluence with the main stem. The resulting normalized elevation is:
   $$\text{HAND}_{\text{main}}(x, y) = z(x, y) - z(\text{nearest main-reach confluence})$$
3. **Backwater Confluence Inundation:** At the tributary mouth where the bed is within $S$ meters vertically of the confluence, $\text{HAND}_{\text{main}} < S$ and backwater flooding is represented. As the tributary climbs into the mountains, $z(x,y)$ rises rapidly, $\text{HAND}_{\text{main}} \gg S$, and the upper tributary remains dry.
4. **Flood Connectivity Filtering:** Isolated inland sinks, local saddles, and disconnected depression fragments are removed using 8-connectivity flood-fill seeding from the active channel corridor.

**Scientific Literature & Sources:**
- **Rennó, C. D., Nobre, A. D., et al. (2008).** *HAND, a new terrain descriptor using SRTM-DEM: Mapping terra-firme rainforest environments in Amazonia.* Remote Sensing of Environment, 112(9), 3469–3481.
- **Nobre, A. D., Cuartas, L. A., et al. (2011).** *HEIGHT ABOVE THE NEAREST DRAINAGE – a hydrologically normalized Digital Elevation Model for terrain analysis and environmental applications.* Journal of Hydrology, 404(1-2), 13–29.
- **Zheng, X., Maidment, D. R., et al. (2018).** *Geo-statistical representation of river width and depth using HAND.* Water Resources Research, 54(8), 5857–5873.
- **Chow, V. T. (1959).** *Open-channel hydraulics.* McGraw-Hill, New York.

**Peak Attenuation Rule:**
For Tier 0, the peak discharge is currently not attenuated downstream; the initial breach peak is conservatively applied to the entire near-field reach. Future enhancements or subsequent tiers (Tier 1) will account for flood wave attenuation. This method is intentionally conservative and intended only as a first estimate.
