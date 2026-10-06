# Blocked Items

## Phase 2a: Volume, breach and Delft3D FM
- **Peng and Zhang (2012) equations:** The regression coefficients for predicting landslide dam breach parameters (peak discharge, width, failure time) from Peng and Zhang (2012) *Landslides* 9(1):13-31 (DOI: 10.1007/s10346-011-0271-y) are pending. The user will supply them from Table 4, along with test data from Tables 8 and 9. `landslide.py` is blocked until provided.
- **Existing Lake Area-Volume Scaling ($\kappa, \zeta$):** Area-volume scaling power laws ($V = \kappa A^\zeta$) vary strongly by lake geomorphic type (e.g., moraine-dammed glacial lakes vs thermokarst vs tectonic vs artificial reservoirs) and region (e.g. Huggel et al. 2002, Cook & Quincey 2015, Cael et al. 2017). Universal default coefficients cannot be assumed; `kappa` and `zeta` are required explicit inputs with no defaults.
