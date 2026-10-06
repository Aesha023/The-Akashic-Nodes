# Blocked Items and Known Issues

## Phase 2a: Volume, breach and Hydrograph Known Issues
- **Peng and Zhang (2012) equations:** Method not available. No accessible source. `core/pravahx/breach/landslide.py` raises `NotImplementedError("Method not available: Peng and Zhang (2012) equations not available from an accessible source.")`.
- **Existing Lake Area-Volume Scaling ($\kappa, \zeta$):** Area-volume scaling power laws ($V = \kappa A^\zeta$) vary strongly by lake geomorphic type (e.g., moraine-dammed glacial lakes vs thermokarst vs tectonic vs artificial reservoirs) and region (e.g. Huggel et al. 2002, Cook & Quincey 2015, Cael et al. 2017). Universal default coefficients cannot be assumed; `kappa` and `zeta` are required explicit inputs with no defaults.
- **Von Thun and Gillette Equations & Input Enforcement:** Re-verify formation-time equations and $C_b$ threshold storage table against HEC-RAS reference page; make erodibility a required input parameter with no default.
- **Teton Dam Level-Pool Overprediction & Range Labeling:** Label every benchmark table row against the full published historical peak range ($28,300 - 65,129\text{ m}^3/\text{s}$ / $1.0\text{M} - 2.3\text{M cfs}$) and document plainly that 1D level-pool routing overpredicts actual dam-break discharge due to lack of 2D reservoir drawdown and unmodeled breach headcut friction / submergence losses.
- **Piping Failure Orifice-to-Weir Transition:** Standard 1D hydrograph routing in HEC-RAS models piping breaches with an orifice equation while the pipe is submerged beneath the embankment crest, transitioning to open-channel weir flow only after the crest collapses. Implement orifice-to-weir transition in breach routing.
- **Trapezoidal Breach Weir Coefficients:** Compare metric weir coefficient $C_{v1} = 1.70$ ($C_d \approx 3.09$ in US Customary) against HEC-RAS user guidance and sensitivity ranges ($2.6 - 3.1$).
- **Strict Verification of USGS Details:** Mark any USGS PP / OFR details not present on a live fetched web page as `[UNVERIFIED]`.

## Phase 2b: Delft3D FM
- **Delft3D FM Container Execution:** The `run()` method of `Delft3DFMAdapter` is blocked pending access to the Deltares Harbor container registry (`containers.deltares.nl`). `prepare()` (HYDROLIB-core case generation) and `postprocess()` (xarray NetCDF output extraction) are implemented and unit tested.

