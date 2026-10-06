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

## Reservoir Volume Estimation (Phase 2a)

1. **New Lake / Valley Blockage (Post-DEM):**
   When a lake or river blockage forms after the reference DEM acquisition, the volume is computed by integrating water depths across the water mask:
   $$V = \sum_{(x,y) \in \text{Lake}} \max\left(0, z_{\text{shore}} - z_{\text{DEM}}(x, y)\right) \cdot A_{\text{cell}}$$
   where $z_{\text{shore}}$ is the median elevation along the perimeter of the water mask.

2. **Existing Lake (Pre-DEM):**
   For lakes present during DEM acquisition, the DEM records the flat water surface, so surface minus DEM yields zero. A power-law area-volume scaling relation is used:
   $$V = \kappa \cdot A_{\text{km}^2}^\zeta \quad (\text{with } V \text{ in km}^3)$$
   Because $\kappa$ and $\zeta$ vary significantly by lake geomorphic type (e.g. glacial moraine-dammed vs thermokarst vs tectonic) and geographic setting, universal defaults are not assumed and explicit parameters must be provided.

3. **Registered Dams:**
   Direct lookup of gross/live storage capacity from the National Register of Large Dams (NRLD) or equivalent official register.

## Embankment Dam Breach Parameters (Froehlich, 2008)

For earthen and rockfill embankment dams, empirical regression equations from Froehlich (2008) predict final breach geometry and formation time:
- **Average Breach Width ($B_{\text{avg}}$):**
  $$B_{\text{avg}} = 0.27 \cdot K_o \cdot V_w^{0.32} \cdot h_b^{0.04}$$
  where $K_o = 1.3$ for overtopping failure and $1.0$ for piping/internal erosion; $V_w$ is reservoir storage at failure ($\text{m}^3$); $h_b$ is breach height ($\text{m}$).
- **Breach Formation Time ($t_f$):**
  $$t_f = 63.2 \cdot \sqrt{\frac{V_w}{g \cdot h_b^2}} \quad (\text{in seconds})$$
- **Breach Side Slope ($z$):**
  $z = 1.0$ (1H:1V) for overtopping; $z = 0.7$ (0.7H:1V) for piping.
- **Bottom Width ($b_{\text{bottom}}$):**
  $$b_{\text{bottom}} = \max\left(0, B_{\text{avg}} - z \cdot h_b\right)$$

## Dynamic Trapezoidal Breach Hydrograph Routing

The outflow hydrograph $Q(t)$ is routed dynamically by solving conservation of volume through a time-varying trapezoidal broad-crested weir:

$$\frac{dV}{dt} = -Q(t)$$

1. **Trapezoidal Broad-Crested Weir Flow:**
   $$Q(t) = C_{v1} \cdot b(t) \cdot h(t)^{1.5} + C_{v2} \cdot z(t) \cdot h(t)^{2.5}$$
   - $C_{v1} \approx 1.70 \text{ m}^{1/2}/\text{s}$: Rectangular broad-crested weir coefficient.
   - $C_{v2} \approx 1.35 \text{ m}^{1/2}/\text{s}$: Triangular side-slope weir coefficient ($2.45$ in US Customary).
   - Sources: Fread (1988), Wahl (1998 Eq. 2), HEC-RAS Hydraulic Reference Manual Ch. 14.

2. **Stage-Storage Hypsometry $h(t)$:**
   The reservoir head above the breach invert is derived from the remaining volume using a power-law hypsometric relationship:
   $$V(h) = K_v \cdot h^m \implies h(t) = H_0 \cdot \left(\frac{V(t)}{V_0}\right)^{1/m}$$
   where $m = 3.0$ models a pyramidal/V-shaped mountain gorge ($A(h) \propto h^2$), $m = 2.0$ models a parabolic valley, and $m = 1.0$ models a vertical-walled prismatic tank. Source: Singh (1996).

3. **Breach Geometry Progression:**
   The breach expands linearly from initiation ($t=0$) to its ultimate dimensions at $t = t_f$:
   $$b(t) = b_{\text{bottom}} \cdot \min\left(1.0, \frac{t}{t_f}\right), \quad z(t) = z \cdot \min\left(1.0, \frac{t}{t_f}\right)$$
   For $t > t_f$, the breach geometry remains constant at its final dimensions until the reservoir is emptied.

4. **Comparison with Froehlich (1995) Empirical Peak Outflow:**
   Froehlich (1995) provides an empirical regression for peak discharge based on historical dam breaks:
   $$Q_p = 0.607 \cdot V_w^{0.295} \cdot h_w^{1.24} \quad (\text{SI units: } \text{m}^3/\text{s}, \text{m}^3, \text{m})$$
   - *Physical Rationale for Differences:*
     Dynamic broad-crested weir routing evaluates frictionless 1D weir discharge at the breach throat without 2D reservoir drawdown funnels or tailwater submergence. Real-world historical dam failures (reflected in Froehlich 1995) exhibit 40%–60% lower peak outflows due to downstream tailwater backwater, 3D contraction headlosses, breach channel frictional drag, and progressive vertical headcut incision lag.

## Scientific Literature & Sources
- **Chow, V. T. (1959).** *Open-channel hydraulics.* McGraw-Hill, New York.
- **Fread, D. L. (1988).** *BREACH: An Erosion Model for Earthen Dam Failures.* Hydrologic Research Laboratory, National Weather Service, NOAA, Silver Spring, MD.
- **Froehlich, D. C. (1995).** *Peak Outflow from Breached Embankment Dams.* ASCE Journal of Water Resources Planning and Management, 121(1), 90–97.
- **Froehlich, D. C. (2008).** *Embankment dam breach parameters and their uncertainties.* ASCE Journal of Hydraulic Engineering, 134(12), 1708–1721.
- **Nobre, A. D., Cuartas, L. A., et al. (2011).** *HEIGHT ABOVE THE NEAREST DRAINAGE – a hydrologically normalized Digital Elevation Model for terrain analysis and environmental applications.* Journal of Hydrology, 404(1-2), 13–29.
- **Rennó, C. D., Nobre, A. D., et al. (2008).** *HAND, a new terrain descriptor using SRTM-DEM: Mapping terra-firme rainforest environments in Amazonia.* Remote Sensing of Environment, 112(9), 3469–3481.
- **Singh, V. P. (1996).** *Dam Breach Modeling Technology.* Water Science and Technology Library, Kluwer Academic Publishers, Dordrecht.
- **US Army Corps of Engineers (2020).** *HEC-RAS Hydraulic Reference Manual, Version 6.0.* Hydrologic Engineering Center, Davis, CA.
- **Wahl, T. L. (1998).** *Prediction of Embankment Dam Breach Parameters: A Literature Review and Needs Assessment.* Dam Safety Research Report DSO-98-004, U.S. Department of the Interior, Bureau of Reclamation, Denver, CO.
- **Zheng, X., Maidment, D. R., et al. (2018).** *Geo-statistical representation of river width and depth using HAND.* Water Resources Research, 54(8), 5857–5873.

