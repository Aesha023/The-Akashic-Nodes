import React from 'react';
import { useTranslation } from 'react-i18next';
import { 
  MinusCircle
} from 'lucide-react';
import { FeatureId } from '../../types';
import { DemoBadge } from '../common/DemoBadge';
import { useDemoMode } from '../../context/DemoModeContext';

interface CascadeRiskPageProps {
  onNavigate?: (feature: FeatureId) => void;
}

export const CascadeRiskPage: React.FC<CascadeRiskPageProps> = () => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';
  const { isPresentationMode } = useDemoMode();

  if (!isPresentationMode) {
    return (
      <div className="p-6 sm:p-10 max-w-5xl mx-auto space-y-6">
        <div className="bg-white rounded-2xl border border-border p-8 text-center space-y-3">
          <MinusCircle size={32} className="mx-auto text-text-tertiary" />
          <h2 className="text-lg font-bold text-text">
            {isHi ? 'परिचालन मोड में उपलब्ध नहीं' : 'Not Active in Operational Mode'}
          </h2>
          <p className="text-xs text-text-secondary max-w-md mx-auto">
            Cascade Risk Analysis is currently illustrative. Switch to Presentation mode in the top bar to inspect this domino breach cascade preview.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 sm:p-10 max-w-7xl mx-auto space-y-6">
      {/* 1. Header (Part A3 standard) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-4">
        <div>
          <div className="text-xs font-mono font-semibold tracking-wider text-text-tertiary uppercase">
            F11 · {isHi ? 'कैस्केड मॉडलिंग' : 'MONITORING'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text mt-1">
            {isHi ? 'क्या इस बांध की विफलता से अनुप्रवाह में अन्य बांध भी टूट सकते हैं?' : 'Will the failure of this dam trigger a domino breach downstream?'}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {isHi 
              ? 'बहु-बांध जलशृंखला में लहर संचरण, अनुप्रवाह भराव दर और संभावित ओवरटॉपिंग जोखिम का विश्लेषण।' 
              : 'Multi-reservoir domino breach modeling: flood wave attenuation and downstream overtopping probability.'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <DemoBadge />
        </div>
      </div>

      {/* 2. Domino Cascade Chain Diagram */}
      <div className="bg-white rounded-2xl border border-border p-6 sm:p-8 space-y-8 shadow-xs">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <span className="text-xs font-mono font-bold text-text-tertiary uppercase tracking-wider">
            Cascade Reach Model: Demo Chain A → B → C
          </span>
          <span className="text-xs text-text-tertiary font-mono">
            Total Fall: 420m · Length: 68 km
          </span>
        </div>

        {/* 3 Chain Steps */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
          {/* Node 1: Dam A */}
          <div className="p-5 rounded-2xl border-2 border-status-fail bg-[#FEF3F2]/40 space-y-3 relative">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[#FEF3F2] text-[#B42318] uppercase">
                Initiating Breach
              </span>
              <span className="text-xs font-mono text-[#B42318] font-bold">t = 0.0 hrs</span>
            </div>
            <h3 className="text-base font-bold text-text">Demo Reservoir Alpha</h3>
            <div className="text-xs text-text-secondary space-y-1">
              <div>Capacity: <strong className="text-text font-mono">350 MCM</strong></div>
              <div>Peak Outflow: <strong className="text-status-fail font-mono">5,000 m³/s</strong></div>
              <div>Failure Mechanism: Overtopping breach</div>
            </div>
          </div>

          {/* Node 2: Dam B */}
          <div className="p-5 rounded-2xl border border-[#FEDF89] bg-[#FFFAEB]/40 space-y-3 relative">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[#FEF0C7] text-[#B54708] uppercase">
                Critical Overtopping Risk
              </span>
              <span className="text-xs font-mono text-[#B54708] font-bold">t = +2.4 hrs</span>
            </div>
            <h3 className="text-base font-bold text-text">Demo Reservoir Beta</h3>
            <div className="text-xs text-text-secondary space-y-1">
              <div>Distance: <strong className="text-text font-mono">24 km downstream</strong></div>
              <div>Inflow Peak: <strong className="text-[#B54708] font-mono">4,150 m³/s</strong> (attenuated)</div>
              <div>Freeboard Remaining: <strong className="text-status-fail font-mono">-0.42 m (Overtopped)</strong></div>
            </div>
          </div>

          {/* Node 3: Dam C */}
          <div className="p-5 rounded-2xl border border-border bg-bg-subtle/40 space-y-3 relative">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[#EFF8FF] text-[#175CD3] uppercase">
                Controlled Sluice Discharge
              </span>
              <span className="text-xs font-mono text-[#175CD3] font-bold">t = +6.1 hrs</span>
            </div>
            <h3 className="text-base font-bold text-text">Demo Reservoir Gamma</h3>
            <div className="text-xs text-text-secondary space-y-1">
              <div>Distance: <strong className="text-text font-mono">68 km downstream</strong></div>
              <div>Inflow Peak: <strong className="text-brand font-mono">2,850 m³/s</strong> (valley storage)</div>
              <div>Status: <strong className="text-status-pass font-mono">Safe Headway (+1.8m)</strong></div>
            </div>
          </div>
        </div>

        {/* Attenuation Summary */}
        <div className="p-4 rounded-xl bg-bg-subtle border border-border text-xs text-text-secondary space-y-1">
          <div className="font-semibold text-text">Cascade Wave Routing Physics:</div>
          <p>
            Hydrograph attenuation calculated using 1D Muskingum-Cunge routing along valley floodplain cross-sections. Reservoir Beta experiences emergency spillway exceedance at hour 2.4 under full pool conditions.
          </p>
        </div>
      </div>
    </div>
  );
};
