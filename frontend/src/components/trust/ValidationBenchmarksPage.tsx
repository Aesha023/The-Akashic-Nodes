import React from 'react';
import { useTranslation } from 'react-i18next';
import { 
  CheckCircle2
} from 'lucide-react';
import { FeatureId } from '../../types';

interface ValidationBenchmarksPageProps {
  onNavigate?: (feature: FeatureId) => void;
}

export const ValidationBenchmarksPage: React.FC<ValidationBenchmarksPageProps> = () => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  return (
    <div className="p-6 sm:p-10 max-w-7xl mx-auto space-y-8">
      {/* 1. Header (Part A3 standard) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-4">
        <div>
          <div className="text-xs font-mono font-semibold tracking-wider text-text-tertiary uppercase">
            F19 · {isHi ? 'सत्यापन एवं मानक' : 'TRUST'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text mt-1">
            {isHi ? 'क्या ये हाइड्रोडायनामिक गणनाएं वैज्ञानिक रूप से प्रमाणित हैं?' : 'Are these hydrodynamic calculations scientifically proven?'}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {isHi 
              ? 'विश्लेषणात्मक समीकरणों, उपग्रह प्रेक्षणों और प्रयोगशाला मानकों के विरुद्ध कठोर वैज्ञानिक सत्यापन।' 
              : 'Empirical proof ledger: analytical exact solutions, satellite radar mappings, and benchmark convergence.'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-pill text-xs font-bold bg-[#ECFDF3] text-[#067647] border border-[#D1FADF] flex items-center gap-1.5">
            <CheckCircle2 size={14} />
            <span>REAL EVIDENCE ONLY · NO DEMO</span>
          </span>
        </div>
      </div>

      {/* 2. Scientific Benchmark Cards Grid */}
      <div className="space-y-4">
        {/* Benchmark 1: Ritter 1892 (RUN AND PASSED) */}
        <div className="bg-white rounded-2xl border border-border p-6 sm:p-8 space-y-4 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-status-pass-soft text-status-pass flex items-center justify-center font-bold">
                1892
              </div>
              <div>
                <h2 className="text-base sm:text-lg font-bold text-text">
                  Analytical Dam Break Benchmark (Ritter 1892)
                </h2>
                <div className="text-xs font-mono text-text-tertiary">
                  Exact dry horizontal bed shallow water equation analytical solution
                </div>
              </div>
            </div>

            <span className="px-3 py-1 rounded-pill text-xs font-bold bg-[#ECFDF3] text-[#067647] border border-[#D1FADF] self-start sm:self-auto">
              RUN AND PASSED
            </span>
          </div>

          <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
            Evaluated at dimensionless time <code className="font-mono text-text">t = 30s</code> following instantaneous gate removal with reservoir depth <code className="font-mono text-text">h_0 = 10m</code>. Demonstrates exact mass conservation and spatial convergence under mesh refinement (refining cell resolution from Δx = 5.0m to 2.5m reduces water depth RMSE from 0.18m to 0.10m, representing a <strong className="text-text">~45% error reduction</strong>).
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-bg-subtle border border-border text-xs font-mono">
            <div>
              <span className="text-text-tertiary uppercase">Analytical Gate Depth</span>
              <div className="font-bold text-text mt-0.5">4.44 m (4/9 h_0)</div>
            </div>
            <div>
              <span className="text-text-tertiary uppercase">Simulated Depth (Δx=2.5m)</span>
              <div className="font-bold text-brand mt-0.5">4.42 m</div>
            </div>
            <div>
              <span className="text-text-tertiary uppercase">RMSE (Coarse Δx=5m)</span>
              <div className="font-bold text-text mt-0.5">0.18 m</div>
            </div>
            <div>
              <span className="text-text-tertiary uppercase">RMSE (Refined Δx=2.5m)</span>
              <div className="font-bold text-status-pass mt-0.5">0.10 m (-45%)</div>
            </div>
          </div>

          <div className="pt-2 text-xs text-brand font-semibold">
            Documentation: <a href="docs/VALIDATION.md" className="hover:underline">VALIDATION.md §2 (Ritter Dam Break Exact Convergence)</a>
          </div>
        </div>

        {/* Benchmark 2: Kuttanad Sentinel-1 SAR (RUN AND PASSED) */}
        <div className="bg-white rounded-2xl border border-border p-6 sm:p-8 space-y-4 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-brand-soft text-brand flex items-center justify-center font-bold">
                SAR
              </div>
              <div>
                <h2 className="text-base sm:text-lg font-bold text-text">
                  Kuttanad Inundation Mapping (Copernicus Sentinel-1 SAR)
                </h2>
                <div className="text-xs font-mono text-text-tertiary">
                  Google Earth Engine Otsu thresholding on VV polarization GRD backscatter
                </div>
              </div>
            </div>

            <span className="px-3 py-1 rounded-pill text-xs font-bold bg-[#ECFDF3] text-[#067647] border border-[#D1FADF] self-start sm:self-auto">
              RUN AND PASSED
            </span>
          </div>

          <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
            Autonomous Google Earth Engine script ingestion extracting 40.52 km² of flooded surface water across the Kuttanad delta during the peak Kerala 2018 monsoon event. The resulting mapped extent is <strong className="text-text">qualitatively consistent with published Kerala 2018 flood extent studies</strong>.
          </p>

          <div className="pt-2 text-xs text-brand font-semibold">
            Documentation: <a href="docs/VALIDATION.md" className="hover:underline">VALIDATION.md §8 (Satellite Water Detection Benchmark)</a>
          </div>
        </div>

        {/* Benchmark 3: Delft3D FM Ganga Reach 2D (PENDING / RUN AND FAILED) */}
        <div className="bg-white rounded-2xl border border-border p-6 sm:p-8 space-y-4 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#FEF0C7] text-[#B54708] flex items-center justify-center font-bold">
                2D
              </div>
              <div>
                <h2 className="text-base sm:text-lg font-bold text-text">
                  Delft3D Flexible Mesh 2D (Ganga Reach near Rishikesh)
                </h2>
                <div className="text-xs font-mono text-text-tertiary">
                  Sub-grid shallow water equation simulation (t = 3,600s)
                </div>
              </div>
            </div>

            <span className="px-3 py-1 rounded-pill text-xs font-bold bg-[#FFFAEB] text-[#B54708] border border-[#FEDF89] self-start sm:self-auto">
              PENDING / UNDER CALIBRATION
            </span>
          </div>

          <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
            Simulation completed on Google Colab CPU environment. NetCDF output postprocessing and cell-by-cell water depth matrix alignment against the static Tier-0 raster is undergoing calibration. Subgrid bathymetry interpolation is under verification prior to production sign-off.
          </p>

          <div className="pt-2 text-xs text-[#B54708] font-semibold">
            Documentation: <a href="docs/VALIDATION.md" className="hover:underline">VALIDATION.md §11.3 (Delft3D Flexible Mesh Verification)</a>
          </div>
        </div>

        {/* Benchmark 4: DualSPHysics 3D SPH (RUN · not yet validated) */}
        <div className="bg-white rounded-2xl border border-border p-6 sm:p-8 space-y-4 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-bg-subtle text-text-secondary flex items-center justify-center font-bold">
                3D
              </div>
              <div>
                <h2 className="text-base sm:text-lg font-bold text-text">
                  DualSPHysics 3D Smoothed Particle Hydrodynamics
                </h2>
                <div className="text-xs font-mono text-text-tertiary">
                  Near-field breach bore impact and structural hydrodynamic loading
                </div>
              </div>
            </div>

            <span className="px-3 py-1 rounded-pill text-xs font-bold bg-[#F2F4F7] text-[#475467] border border-[#D0D5DD] self-start sm:self-auto">
              RUN · NOT YET VALIDATED
            </span>
          </div>

          <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
            Initial GPU particle dispatch verified on synthetic canyon reach. Formal quantitative validation against laboratory flume pressure transducers will occur upon completion of hardware cluster provisioning.
          </p>

          <div className="pt-2 text-xs text-text-tertiary font-semibold">
            Documentation: <a href="docs/VALIDATION.md" className="hover:underline">VALIDATION.md §9 (DualSPHysics Benchmarks)</a>
          </div>
        </div>

        {/* Benchmark 5: Martin & Moyce 1952 (NOT RUN) */}
        <div className="bg-white rounded-2xl border border-border p-6 sm:p-8 space-y-4 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-bg-muted text-text-tertiary flex items-center justify-center font-bold">
                EXP
              </div>
              <div>
                <h2 className="text-base sm:text-lg font-bold text-text">
                  Martin & Moyce (1952) Physical Water Column Collapse
                </h2>
                <div className="text-xs font-mono text-text-tertiary">
                  Experimental flume column surge surge arrival time
                </div>
              </div>
            </div>

            <span className="px-3 py-1 rounded-pill text-xs font-bold bg-[#F2F4F7] text-[#475467] border border-[#D0D5DD] self-start sm:self-auto">
              NOT RUN
            </span>
          </div>

          <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
            Status: NOT RUN. Sensor coordinate mapping against flume wall cameras is deferred until Phase 8 physical calibration campaign.
          </p>

          <div className="pt-2 text-xs text-text-tertiary font-semibold">
            Documentation: <a href="docs/VALIDATION.md" className="hover:underline">VALIDATION.md §3 (Martin & Moyce Flume)</a>
          </div>
        </div>
      </div>
    </div>
  );
};
