# Blocked Items

## Phase 2a: Volume, breach and Delft3D FM
- **Peng and Zhang (2012) equations:** Method not available. No accessible source. `core/pravahx/breach/landslide.py` raises `NotImplementedError("Method not available: Peng and Zhang (2012) equations not available from an accessible source.")`.
- **Existing Lake Area-Volume Scaling ($\kappa, \zeta$):** Area-volume scaling power laws ($V = \kappa A^\zeta$) vary strongly by lake geomorphic type (e.g., moraine-dammed glacial lakes vs thermokarst vs tectonic vs artificial reservoirs) and region (e.g. Huggel et al. 2002, Cook & Quincey 2015, Cael et al. 2017). Universal default coefficients cannot be assumed; `kappa` and `zeta` are required explicit inputs with no defaults.
- **Delft3D FM Container Execution:** The `run()` method of `Delft3DFMAdapter` is blocked pending access to the Deltares Harbor container registry (`containers.deltares.nl`). `prepare()` (HYDROLIB-core case generation) and `postprocess()` (xarray NetCDF output extraction) are implemented and unit tested.
