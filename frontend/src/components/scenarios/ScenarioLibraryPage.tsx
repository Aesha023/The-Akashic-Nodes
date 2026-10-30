import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  PlusCircle, 
  Play, 
  GitCompare
} from 'lucide-react';
import { FeatureId } from '../../types';
import { DemoBadge } from '../common/DemoBadge';

interface ScenarioLibraryPageProps {
  onNavigate: (feature: FeatureId) => void;
}

interface ScenarioItem {
  id: string;
  name: string;
  reach: string;
  inflow_m3s: number;
  tier: string;
  version: string;
  created_at: string;
  status: string;
  is_precomputed?: boolean;
}

export const ScenarioLibraryPage: React.FC<ScenarioLibraryPageProps> = ({ onNavigate }) => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  const [scenarios] = useState<ScenarioItem[]>([
    {
      id: 'scen_ganga_01',
      name: 'Ganga Reach near Rishikesh 5,000 m³/s Baseline',
      reach: 'Ganga Valley (5×5 km)',
      inflow_m3s: 5000,
      tier: 'Tier-0',
      version: 'v1.0.0',
      created_at: '2026-10-22 12:00 UTC',
      status: 'VERIFIED',
      is_precomputed: true,
    },
    {
      id: 'scen_ganga_02',
      name: 'Ganga Reach High-Discharge Sensitivity 10,000 m³/s',
      reach: 'Ganga Valley (5×5 km)',
      inflow_m3s: 10000,
      tier: 'Tier-0',
      version: 'v1.1.0',
      created_at: '2026-10-25 15:30 UTC',
      status: 'ARCHIVED',
    },
    {
      id: 'scen_west_01',
      name: 'Western Ghats Reservoir Embankment Screening',
      reach: 'NRLD-0042 Reach',
      inflow_m3s: 3200,
      tier: 'Tier-0',
      version: 'v1.0.0',
      created_at: '2026-10-28 09:15 UTC',
      status: 'READY',
    },
  ]);

  const [showComparisonModal, setShowComparisonModal] = useState(false);

  return (
    <div className="p-6 sm:p-10 max-w-7xl mx-auto space-y-6">
      {/* 1. Header (Part A3 standard) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-4">
        <div>
          <div className="text-xs font-mono font-semibold tracking-wider text-text-tertiary uppercase">
            F14 · {isHi ? 'परिदृश्य पुस्तकालय' : 'SCENARIOS'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text mt-1">
            {isHi ? 'कौन से ऐतिहासिक और पूर्व-गणना किए गए परिदृश्य संग्रहीत हैं?' : 'Which historical and precomputed breach scenarios are archived?'}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {isHi 
              ? 'अनुमोदित विफलता मॉडल संस्करण, इनफ्लो पैरामीटर और सिमुलेशन वंश का प्रबंधन करें।' 
              : 'Browse validated breach models, version increments, and simulation diff lineages.'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowComparisonModal(true)}
            className="py-2.5 px-4 rounded-xl border border-border text-text font-medium text-sm hover:bg-bg-subtle active:scale-[0.98] transition-all flex items-center gap-2"
          >
            <GitCompare size={16} />
            <span>{isHi ? 'रन तुलना' : 'Compare Runs'}</span>
            <DemoBadge />
          </button>
          <button
            onClick={() => onNavigate('f02_new_scenario')}
            className="py-2.5 px-4 rounded-xl bg-brand text-white font-semibold text-sm hover:bg-brand/90 active:scale-[0.98] transition-all flex items-center gap-2 shadow-2xs"
          >
            <PlusCircle size={16} />
            <span>{isHi ? 'नया परिदृश्य बनाएँ' : 'New Scenario'}</span>
          </button>
        </div>
      </div>

      {/* 2. Scenarios Table */}
      <div className="bg-white rounded-2xl border border-border overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <span className="text-xs font-mono font-bold text-text-tertiary uppercase tracking-wider">
            {isHi ? 'संग्रहीत परिदृश्य सूची' : 'Archived Scenarios Ledger'}
          </span>
          <span className="text-xs text-text-tertiary font-mono">
            {scenarios.length} {isHi ? 'परिदृश्य' : 'Records'} · Source: /api/v1/scenarios
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-bg-subtle/80 text-text-secondary text-xs uppercase font-semibold border-b border-border sticky top-0">
              <tr>
                <th className="py-3 px-6">{isHi ? 'परिदृश्य नाम' : 'Scenario Name'}</th>
                <th className="py-3 px-4">{isHi ? 'भौगोलिक क्षेत्र' : 'Reach / Basin'}</th>
                <th className="py-3 px-4 text-right">{isHi ? 'चरम प्रवाह' : 'Peak Inflow'}</th>
                <th className="py-3 px-4">{isHi ? 'सॉल्वर टियर' : 'Tier'}</th>
                <th className="py-3 px-4">{isHi ? 'संस्करण' : 'Version'}</th>
                <th className="py-3 px-4">{isHi ? 'स्थिति' : 'Status'}</th>
                <th className="py-3 px-6 text-right">{isHi ? 'क्रियाएं' : 'Actions'}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {scenarios.map((scen) => (
                <tr key={scen.id} className="h-[52px] hover:bg-bg-subtle/50 transition-colors">
                  <td className="py-3 px-6 font-semibold text-text">
                    <div className="flex flex-col">
                      <span>{scen.name}</span>
                      <span className="text-[11px] font-mono text-text-tertiary">{scen.id}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-text-secondary">{scen.reach}</td>
                  <td className="py-3 px-4 text-right font-mono font-semibold text-brand">
                    {scen.inflow_m3s.toLocaleString()} m³/s
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-bg-muted text-text-secondary">
                      {scen.tier}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-xs text-text-tertiary">{scen.version}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2.5 py-0.5 rounded-pill text-[11px] font-bold border ${
                      scen.status === 'VERIFIED'
                        ? 'bg-[#ECFDF3] text-[#067647] border-[#D1FADF]'
                        : scen.status === 'READY'
                        ? 'bg-[#EFF8FF] text-[#175CD3] border-[#B2DDFF]'
                        : 'bg-[#F2F4F7] text-[#475467] border-[#D0D5DD]'
                    }`}>
                      {scen.status}
                    </span>
                  </td>
                  <td className="py-3 px-6 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => onNavigate('f05_results_explorer')}
                        className="py-1 px-3 rounded-lg border border-border text-xs font-medium hover:bg-bg-subtle active:scale-[0.98] transition-all flex items-center gap-1"
                      >
                        <Play size={12} className="text-brand" />
                        <span>{isHi ? 'परिणाम देखें' : 'View Result'}</span>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Comparison Modal (DEMO badge) */}
      {showComparisonModal && (
        <div className="fixed inset-0 bg-[#0B1220]/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl border border-border max-w-2xl w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <GitCompare size={18} className="text-brand" />
                <h3 className="text-base font-bold text-text">
                  {isHi ? 'परिदृश्य अंतर तुलना (Lineage Diff)' : 'Scenario Parameter Diff View'}
                </h3>
                <DemoBadge />
              </div>
              <button
                onClick={() => setShowComparisonModal(false)}
                className="text-text-tertiary hover:text-text text-sm font-semibold p-1"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs text-text-secondary leading-relaxed">
              <p>
                Comparing <strong className="text-text">scen_ganga_01 (5,000 m³/s)</strong> vs{' '}
                <strong className="text-text">scen_ganga_02 (10,000 m³/s)</strong>:
              </p>
              <div className="grid grid-cols-2 gap-4 p-4 rounded-xl bg-bg-subtle border border-border font-mono">
                <div>
                  <div className="text-text-tertiary uppercase">Run A (Baseline)</div>
                  <div className="font-bold text-text mt-1">Inundated: 1.72 km²</div>
                  <div className="text-text-secondary">Max Depth: 7.73 m</div>
                  <div className="text-text-secondary">Population: 2,696</div>
                </div>
                <div>
                  <div className="text-text-tertiary uppercase">Run B (+100% Inflow)</div>
                  <div className="font-bold text-brand mt-1">Inundated: 2.48 km² (+44%)</div>
                  <div className="text-text-secondary">Max Depth: 9.85 m (+27%)</div>
                  <div className="text-text-secondary">Population: 4,110 (+52%)</div>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowComparisonModal(false)}
                className="py-2 px-5 rounded-xl bg-bg-subtle border border-border text-xs font-semibold hover:bg-bg-muted transition-all"
              >
                {isHi ? 'बंद करें' : 'Close Comparison'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
