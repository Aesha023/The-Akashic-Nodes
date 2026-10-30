import React from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Satellite, 
  CheckCircle2, 
  Info,
  Calendar,
  FileText
} from 'lucide-react';
import { FeatureId } from '../../types';

interface SatelliteValidationPageProps {
  onNavigate?: (feature: FeatureId) => void;
}

export const SatelliteValidationPage: React.FC<SatelliteValidationPageProps> = () => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  return (
    <div className="p-6 sm:p-10 max-w-7xl mx-auto space-y-6">
      {/* 1. Header (Part A3 standard) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-4">
        <div>
          <div className="text-xs font-mono font-semibold tracking-wider text-text-tertiary uppercase">
            F07 · {isHi ? 'उपग्रह सत्यापन' : 'RESULTS'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text mt-1">
            {isHi ? 'बाढ़ सिमुलेशन सेंटिनल-1 उपग्रह रडार से कितना सटीक मेल खाता है?' : 'How well does the flood simulation match Sentinel-1 satellite radar?'}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {isHi 
              ? 'सिन्थेटिक एपर्चर रडार (SAR) प्रेक्षणों के आधार पर वास्तविक जलप्लावन सीमा का अनुभवजन्य सत्यापन।' 
              : 'Empirical cross-validation of simulated water extents against Sentinel-1 Synthetic Aperture Radar (SAR).'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-pill text-xs font-bold bg-[#ECFDF3] text-[#067647] border border-[#D1FADF] flex items-center gap-1.5">
            <CheckCircle2 size={14} />
            <span>REAL EVIDENCE ONLY · NO SYNTHETIC CSI</span>
          </span>
        </div>
      </div>

      {/* 2. REAL Kuttanad Sentinel-1 Mapping Card */}
      <div className="bg-white rounded-2xl border border-border p-6 sm:p-8 space-y-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-brand-soft border border-brand/20 flex items-center justify-center text-brand">
              <Satellite size={22} />
            </div>
            <div>
              <h2 className="text-lg font-bold text-text">
                Kuttanad Inundation Mapping (Sentinel-1 SAR)
              </h2>
              <div className="text-xs font-mono text-text-tertiary">
                Observation Date: August 2018 · Sentinel-1A IW GRDH (Polarization: VH/VV)
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-pill text-xs font-mono font-bold bg-bg-subtle text-text-secondary border border-border">
              Area: 40.52 km²
            </span>
          </div>
        </div>

        {/* 4 KPI metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-bg-subtle border border-border space-y-1">
            <div className="text-[11px] font-mono text-text-tertiary uppercase">Mapped SAR Inundation</div>
            <div className="text-2xl font-bold text-text font-mono">40.52 km²</div>
            <div className="text-[10px] text-text-secondary">Otsu backscatter threshold</div>
          </div>

          <div className="p-4 rounded-xl bg-bg-subtle border border-border space-y-1">
            <div className="text-[11px] font-mono text-text-tertiary uppercase">Sensor & Polarization</div>
            <div className="text-2xl font-bold text-brand font-mono">Sentinel-1A VH</div>
            <div className="text-[10px] text-text-secondary">Relative orbit 165 (Descending)</div>
          </div>

          <div className="p-4 rounded-xl bg-bg-subtle border border-border space-y-1">
            <div className="text-[11px] font-mono text-text-tertiary uppercase">Median Backscatter Shift</div>
            <div className="text-2xl font-bold text-text font-mono">-1.5 dB</div>
            <div className="text-[10px] text-text-secondary">-16.87 dB to -18.37 dB</div>
          </div>

          <div className="p-4 rounded-xl bg-bg-subtle border border-border space-y-1">
            <div className="text-[11px] font-mono text-text-tertiary uppercase">Scientific Status</div>
            <div className="text-2xl font-bold text-status-pass font-mono">Consistent</div>
            <div className="text-[10px] text-text-secondary">Qualitatively consistent (no CSI claimed)</div>
          </div>
        </div>

        {/* Detailed Scene Metadata from kuttanad_metadata.json */}
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-bg-subtle text-text-secondary font-semibold uppercase tracking-wider text-[11px] border-b border-border">
              <tr>
                <th className="py-2.5 px-4">Scene Type</th>
                <th className="py-2.5 px-4">Acquisition Date (UTC)</th>
                <th className="py-2.5 px-4">Copernicus Granule Identifier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border font-mono text-[11px]">
              <tr className="hover:bg-bg-subtle/50">
                <td className="py-2.5 px-4 font-sans font-medium text-text">Pre-Event Baseline</td>
                <td className="py-2.5 px-4 text-text">2018-05-29</td>
                <td className="py-2.5 px-4 text-text-secondary truncate max-w-xs">S1A_IW_GRDH_1SDV_20180529T004039_..._F175</td>
              </tr>
              <tr className="hover:bg-bg-subtle/50">
                <td className="py-2.5 px-4 font-sans font-medium text-text">Post-Event Flood Peak</td>
                <td className="py-2.5 px-4 text-text">2018-08-21</td>
                <td className="py-2.5 px-4 text-text-secondary truncate max-w-xs">S1A_IW_GRDH_1SDV_20180821T004044_..._D07A</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Strict Scientific Note */}
        <div className="p-4 rounded-xl bg-bg-subtle/70 border border-border space-y-2 text-xs text-text-secondary">
          <div className="font-semibold text-text flex items-center gap-1.5">
            <Info size={15} className="text-brand" />
            <span>Strict Verification Rule (Zero Invented CSI):</span>
          </div>
          <p className="leading-relaxed">
            In accordance with PravahX scientific provenance standards, Critical Success Index (CSI) and contingency matrices are reported <em>only</em> where ground-surveyed high-water marks exist. For satellite SAR change detection over Kuttanad, the 40.52 km² surface water extent is reported as <strong className="text-text">qualitatively consistent</strong> with peer-reviewed post-event flood mapping (Tiwari et al. 2020), with zero synthetic contingency percentages.
          </p>
          <div className="pt-1 flex items-center gap-4 text-text-tertiary">
            <span className="flex items-center gap-1 font-mono"><Calendar size={13} /> Event: August 2018</span>
            <span className="flex items-center gap-1 font-mono"><FileText size={13} /> Provenance: runs/kerala_2018/needs_human_check/kuttanad_metadata.json</span>
          </div>
        </div>
      </div>
    </div>
  );
};
