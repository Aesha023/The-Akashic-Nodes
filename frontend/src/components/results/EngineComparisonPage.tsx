import React from 'react';
import { useTranslation } from 'react-i18next';
import { 
  AlertTriangle,
  FileText
} from 'lucide-react';
import { FeatureId } from '../../types';
import { useDemoMode } from '../../context/DemoModeContext';
import { DemoBadge } from '../common/DemoBadge';

interface EngineComparisonPageProps {
  onNavigate: (feature: FeatureId) => void;
}

export const EngineComparisonPage: React.FC<EngineComparisonPageProps> = ({ onNavigate }) => {
  const { i18n } = useTranslation();
  const { isPresentationMode } = useDemoMode();
  const isHi = i18n.language === 'hi';

  // Real intercomparison metrics directly computed by comparison pipeline
  // Source: scratch/headless_test_dir/content/ganga_tier1_runs/C_dx25/outputs/intercomparison_metrics.csv
  const realMetrics = {
    tier0_wet_area_km2: 1.723,
    tier1_wet_area_km2: 7.367,
    overlap_area_km2: 1.723,
    iou: 0.2338,
    dice: 0.3790,
    depth_rmsd_m: 3.421,
    depth_mean_diff_m: -2.822,
    depth_median_diff_m: -3.730,
    threshold_depth_m: 0.05,
    peak_inflow_m3s: 5000.0,
  };

  return (
    <div className="p-6 sm:p-10 max-w-7xl mx-auto space-y-6">
      {/* 1. Header (Part A3 standard) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-4">
        <div>
          <div className="text-xs font-mono font-semibold tracking-wider text-text-tertiary uppercase">
            F06 · {isHi ? 'इंजन तुलना' : 'RESULTS'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text mt-1">
            {isHi ? 'एक ही नदी क्षेत्र पर टियर-0 और टियर-1 हाइड्रोडायनामिक्स की तुलना कैसे होती है?' : 'How do Tier-0 and Tier-1 hydrodynamics compare on the same reach?'}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {isHi 
              ? 'टियर-0 (HAND) और टियर-1 (डेल्फ़्ट3D FM 2D) के बीच वास्तविक क्रॉस-मॉडल तुलना मैट्रिक्स।' 
              : 'Cross-evaluate Tier-0 static gravity screening against dynamic 2D shallow water hydrodynamic envelopes.'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {isPresentationMode && <DemoBadge />}
          <button
            onClick={() => onNavigate('f19_benchmarks')}
            className="py-2 px-3.5 rounded-xl border border-border text-xs font-semibold hover:bg-bg-subtle text-text transition-all"
          >
            {isHi ? 'सत्यापन मानक देखें →' : 'View Benchmarks →'}
          </button>
        </div>
      </div>

      {/* 2. REAL Delft3D Status Card (Part F5 requirement) */}
      <div className="p-5 rounded-2xl bg-[#FFFAEB] border border-[#FEDF89] flex items-start gap-4 shadow-xs">
        <AlertTriangle size={20} className="text-[#B54708] shrink-0 mt-0.5" />
        <div className="space-y-1 text-xs text-[#7A271A]">
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm text-[#B54708]">
              Delft3D Ganga Reach: Intercomparison PENDING Full Calibration
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#FEF0C7] text-[#B54708] uppercase">
              REAL STATUS
            </span>
          </div>
          <p className="leading-relaxed">
            Delft3D Flexible Mesh 2D solver ran to completion on Google Colab (dx=25m, t=3,600s, 7,241,809 m³ inflow). Numerical mass conservation is exact (0 m³ residual). Pre-registered hydrodynamic validity gates d/e failed due to natural terrain depression storage in the steep canyon gorge and insufficient run length. Raw figures below are empirical outputs from <code className="font-mono text-[#B54708]">intercomparison_metrics.csv</code> without tuning.
          </p>
        </div>
      </div>

      {/* 3. REAL Empirical Metrics Grid (Directly from comparison script output) */}
      <div className="bg-white rounded-2xl border border-border p-6 space-y-6 shadow-xs">
        <div>
          <h2 className="text-base font-bold text-text">
            Empirical Cross-Model Intercomparison Metrics (Ganga Reach)
          </h2>
          <p className="text-xs text-text-secondary mt-0.5">
            Computed by <code className="font-mono text-text">intercomparison_analysis.py</code> on identical DEM bathymetry and 5,000 m³/s hypothetical inflow.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pb-4 border-b border-border">
          <div>
            <div className="text-[11px] font-mono text-text-tertiary uppercase">Spatial IoU (Jaccard)</div>
            <div className="text-2xl font-bold text-text mt-0.5 font-mono">
              {realMetrics.iou.toFixed(4)}
            </div>
            <div className="text-[10px] text-text-secondary">Intersection over Union ({realMetrics.threshold_depth_m}m threshold)</div>
          </div>
          <div>
            <div className="text-[11px] font-mono text-text-tertiary uppercase">Dice Coefficient (F1)</div>
            <div className="text-2xl font-bold text-text mt-0.5 font-mono">
              {realMetrics.dice.toFixed(4)}
            </div>
            <div className="text-[10px] text-text-secondary">Harmonic mean of precision & recall</div>
          </div>
          <div>
            <div className="text-[11px] font-mono text-text-tertiary uppercase">Depth RMSD</div>
            <div className="text-2xl font-bold text-text mt-0.5 font-mono">
              {realMetrics.depth_rmsd_m.toFixed(2)} m
            </div>
            <div className="text-[10px] text-text-secondary">Root mean square depth diff</div>
          </div>
          <div>
            <div className="text-[11px] font-mono text-text-tertiary uppercase">Mean Depth Difference</div>
            <div className="text-2xl font-bold text-text mt-0.5 font-mono">
              {realMetrics.depth_mean_diff_m.toFixed(2)} m
            </div>
            <div className="text-[10px] text-text-secondary">T1 (dynamic) - T0 (static HAND)</div>
          </div>
        </div>

        {/* Detailed Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-bg-subtle text-text-secondary font-semibold uppercase tracking-wider text-[11px] border-b border-border">
              <tr>
                <th className="py-3 px-4">Metric Parameter</th>
                <th className="py-3 px-4 text-right">Tier-0 (HAND)</th>
                <th className="py-3 px-4 text-right">Tier-1 (Delft3D FM)</th>
                <th className="py-3 px-4">Intercomparison Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border font-mono">
              <tr className="hover:bg-bg-subtle/50 transition-colors">
                <td className="py-3 px-4 font-sans font-medium text-text">Inundation Extent (Area)</td>
                <td className="py-3 px-4 text-right font-bold text-text">{realMetrics.tier0_wet_area_km2.toFixed(3)} km²</td>
                <td className="py-3 px-4 text-right font-bold text-brand">{realMetrics.tier1_wet_area_km2.toFixed(3)} km²</td>
                <td className="py-3 px-4 font-sans text-text-secondary text-[11px]">
                  Delft3D 2D dynamic momentum spreads into lateral tributary channels unreached by static 1D HAND.
                </td>
              </tr>
              <tr className="hover:bg-bg-subtle/50 transition-colors">
                <td className="py-3 px-4 font-sans font-medium text-text">Intersection / Overlap Area</td>
                <td className="py-3 px-4 text-right" colSpan={2}>
                  <span className="font-bold text-text">{realMetrics.overlap_area_km2.toFixed(3)} km²</span>
                </td>
                <td className="py-3 px-4 font-sans text-text-secondary text-[11px]">
                  100% of the Tier-0 predicted flood zone is confirmed wet by the 2D hydrodynamic solver.
                </td>
              </tr>
              <tr className="hover:bg-bg-subtle/50 transition-colors">
                <td className="py-3 px-4 font-sans font-medium text-text">Peak Inflow Discharge</td>
                <td className="py-3 px-4 text-right text-text">{realMetrics.peak_inflow_m3s.toLocaleString()} m³/s</td>
                <td className="py-3 px-4 text-right text-text">{realMetrics.peak_inflow_m3s.toLocaleString()} m³/s</td>
                <td className="py-3 px-4 font-sans text-text-secondary text-[11px]">
                  Identical boundary hydrograph forcing.
                </td>
              </tr>
              <tr className="hover:bg-bg-subtle/50 transition-colors">
                <td className="py-3 px-4 font-sans font-medium text-text">Numerical Mass Conservation</td>
                <td className="py-3 px-4 text-right text-status-pass font-bold">Exact (Static)</td>
                <td className="py-3 px-4 text-right text-status-pass font-bold">0.0 m³ residual</td>
                <td className="py-3 px-4 font-sans text-text-secondary text-[11px]">
                  Delft3D FM volume balance confirmed exact across all time steps.
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="pt-2 text-xs text-text-tertiary flex items-center gap-1.5">
          <FileText size={14} />
          <span>Artifact provenance: <code className="font-mono">intercomparison_metrics.csv</code> (sha256: 3fcc21e2c8a6...)</span>
        </div>
      </div>
    </div>
  );
};
