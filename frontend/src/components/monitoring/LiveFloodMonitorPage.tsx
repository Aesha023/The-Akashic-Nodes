import React from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Radio, 
  Satellite, 
  ArrowUpRight, 
  MinusCircle
} from 'lucide-react';
import { FeatureId } from '../../types';
import { DemoBadge } from '../common/DemoBadge';
import { useDemoMode } from '../../context/DemoModeContext';

interface LiveFloodMonitorPageProps {
  onNavigate: (feature: FeatureId) => void;
}

export const LiveFloodMonitorPage: React.FC<LiveFloodMonitorPageProps> = ({ onNavigate }) => {
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
            Live Flood Monitoring uses illustrative near-real-time satellite feeds. Switch to Presentation mode in the top bar to preview this module.
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
            F08 · {isHi ? 'लाइव बाढ़ मॉनिटर' : 'MONITORING'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text mt-1">
            {isHi ? 'वर्तमान में बाढ़ का पानी कहाँ तेजी से बढ़ रहा है?' : 'Where is flood water actively rising right now?'}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {isHi 
              ? 'उपग्रह रडार पास और नदी गेज टेलीमेट्री द्वारा सक्रिय जल स्तर वृद्धि की निगरानी।' 
              : 'Near-real-time satellite radar passes and virtual river gauge telemetry streams.'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <DemoBadge />
        </div>
      </div>

      {/* 2. Telemetry Stream Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl border border-border p-5 space-y-3 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-text-tertiary uppercase">Virtual Gauge Alpha</span>
            <span className="w-2 h-2 rounded-full bg-status-pass animate-pulse" />
          </div>
          <div className="text-2xl font-bold text-text font-mono">14.82 m</div>
          <div className="text-xs text-[#B54708] flex items-center gap-1 font-semibold">
            <ArrowUpRight size={14} />
            <span>+0.34 m/hr (Rising)</span>
          </div>
          <div className="text-[11px] text-text-tertiary">Warning Stage: 15.00 m · Danger: 16.50 m</div>
        </div>

        <div className="bg-white rounded-2xl border border-border p-5 space-y-3 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-text-tertiary uppercase">Virtual Gauge Beta</span>
            <span className="w-2 h-2 rounded-full bg-status-pass animate-pulse" />
          </div>
          <div className="text-2xl font-bold text-text font-mono">8.15 m</div>
          <div className="text-xs text-status-pass flex items-center gap-1 font-semibold">
            <span>Stable (±0.02 m/hr)</span>
          </div>
          <div className="text-[11px] text-text-tertiary">Warning Stage: 10.50 m · Normal Flow</div>
        </div>

        <div className="bg-white rounded-2xl border border-border p-5 space-y-3 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-text-tertiary uppercase">Next SAR Overpass</span>
            <Satellite size={16} className="text-brand" />
          </div>
          <div className="text-2xl font-bold text-brand font-mono">03h 42m</div>
          <div className="text-xs text-text-secondary">Sentinel-1 Descending Track #48</div>
          <div className="text-[11px] text-text-tertiary">Swath coverage: Northern River Valley</div>
        </div>
      </div>

      {/* 3. Live Map Placeholder Canvas */}
      <div className="bg-white rounded-2xl border border-border p-8 text-center space-y-4 shadow-xs">
        <Radio size={36} className="mx-auto text-brand animate-pulse" />
        <div className="space-y-1">
          <h3 className="text-base font-bold text-text">
            {isHi ? 'लाइव रडार कवरेज स्ट्रीम (प्रदर्शन मोड)' : 'Live Radar Flood Stream Canvas (Demo Mode)'}
          </h3>
          <p className="text-xs text-text-secondary max-w-lg mx-auto">
            Simulated automated water segmentation listening for incoming SAR GRD granules and river gauge webhooks.
          </p>
        </div>
        <div className="pt-2">
          <button
            onClick={() => onNavigate('f05_results_explorer')}
            className="py-2.5 px-5 rounded-xl bg-brand text-white text-xs font-semibold hover:bg-brand/90 transition-all"
          >
            {isHi ? 'सत्यापित गंगा परिणाम देखें →' : 'View Verified Ganga Run Results →'}
          </button>
        </div>
      </div>
    </div>
  );
};
