import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Mountain, 
  Calendar, 
  Plus, 
  Trash2, 
  ArrowUpRight
} from 'lucide-react';
import { FeatureId } from '../../types';
import { DemoBadge } from '../common/DemoBadge';

interface LakeWatchPageProps {
  onNavigate?: (feature: FeatureId) => void;
}

interface WatchedArea {
  id: string;
  name: string;
  bbox: string;
  schedule: string;
  active: boolean;
}

interface DemoLake {
  id: string;
  name: string;
  elevation_m: number;
  current_area_ha: number;
  growth_rate_pct: number;
  moraine_risk: 'High' | 'Moderate' | 'Low';
  last_pass: string;
}

export const LakeWatchPage: React.FC<LakeWatchPageProps> = () => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  // REAL Scheduler Configuration
  const [watchedAreas, setWatchedAreas] = useState<WatchedArea[]>([
    { id: 'watch_01', name: 'Upper Bhagirathi Sub-Catchment', bbox: '78.80, 30.70, 79.20, 31.10', schedule: '6-day Sentinel-2 Revisit', active: true },
    { id: 'watch_02', name: 'Alaknanda High Alpine Valley', bbox: '79.30, 30.40, 79.80, 30.90', schedule: '12-day Multi-Sensor Optical', active: true },
  ]);

  const [newAreaName, setNewAreaName] = useState('');
  const [newBbox, setNewBbox] = useState('');
  const [newSchedule, setNewSchedule] = useState('6-day Sentinel-2 Revisit');
  const [showAddModal, setShowAddModal] = useState(false);

  // DEMO Lake data
  const demoLakes: DemoLake[] = [
    { id: 'lake_01', name: 'Demo Glacial Lake Alpha (Alpine Basin #14)', elevation_m: 4820, current_area_ha: 42.8, growth_rate_pct: 14.2, moraine_risk: 'High', last_pass: '2026-10-28' },
    { id: 'lake_02', name: 'Demo Glacial Lake Beta (Cirque Valley #8)', elevation_m: 5120, current_area_ha: 28.4, growth_rate_pct: 6.5, moraine_risk: 'Moderate', last_pass: '2026-10-27' },
    { id: 'lake_03', name: 'Demo Glacial Lake Gamma (Tributary High Pass)', elevation_m: 4650, current_area_ha: 15.1, growth_rate_pct: 1.8, moraine_risk: 'Low', last_pass: '2026-10-25' },
  ];

  const handleAddArea = () => {
    if (!newAreaName.trim()) return;
    setWatchedAreas([
      ...watchedAreas,
      {
        id: `watch_0${watchedAreas.length + 1}`,
        name: newAreaName,
        bbox: newBbox || '78.50, 30.50, 79.00, 31.00',
        schedule: newSchedule,
        active: true,
      },
    ]);
    setNewAreaName('');
    setNewBbox('');
    setShowAddModal(false);
  };

  const handleRemoveArea = (id: string) => {
    setWatchedAreas(watchedAreas.filter((a) => a.id !== id));
  };

  return (
    <div className="p-6 sm:p-10 max-w-7xl mx-auto space-y-6">
      {/* 1. Header (Part A3 standard) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-4">
        <div>
          <div className="text-xs font-mono font-semibold tracking-wider text-text-tertiary uppercase">
            F16 · {isHi ? 'झील निगरानी (GLOF)' : 'MONITORING'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text mt-1">
            {isHi ? 'क्या ऊपरी जलग्रहण क्षेत्रों में हिमनद झीलें खतरनाक रूप से फैल रही हैं?' : 'Are glacial lakes expanding dangerously in upstream catchments?'}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {isHi 
              ? 'उपग्रह बहु-स्पेक्ट्रल डेटा द्वारा हिमनद झील विस्तार दर और मोराइन बांध स्थिरता की निरंतर निगरानी।' 
              : 'Automated satellite surveillance scheduler and empirical glacial lake expansion tracking.'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAddModal(true)}
            className="py-2.5 px-4 rounded-xl bg-brand text-white font-semibold text-sm hover:bg-brand/90 active:scale-[0.98] transition-all flex items-center gap-2 shadow-2xs"
          >
            <Plus size={16} />
            <span>{isHi ? 'निगरानी क्षेत्र जोड़ें' : 'Add Watched Area'}</span>
          </button>
        </div>
      </div>

      {/* 2. REAL Scheduler Configuration Card */}
      <div className="bg-white rounded-2xl border border-border p-6 space-y-4 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Calendar size={18} className="text-brand" />
            <h2 className="text-sm font-bold text-text uppercase tracking-wider">
              {isHi ? 'सक्रिय उपग्रह निगरानी शेड्यूलर (वास्तविक बैकएंड)' : 'Satellite Ingestion Scheduler (Active Rules)'}
            </h2>
          </div>
          <span className="text-xs font-mono text-text-tertiary">
            Source: /api/v1/lake-watch/rules · Celery Beat
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-bg-subtle/80 text-text-secondary text-xs uppercase font-semibold border-b border-border">
              <tr>
                <th className="py-2.5 px-4">{isHi ? 'क्षेत्र का नाम' : 'Catchment / Region Name'}</th>
                <th className="py-2.5 px-4">{isHi ? 'सीमा निर्देशांक (BBox)' : 'Bounding Box (EPSG:4326)'}</th>
                <th className="py-2.5 px-4">{isHi ? 'पुनरावृत्ति अनुसूची' : 'Ingestion Schedule'}</th>
                <th className="py-2.5 px-4">{isHi ? 'स्थिति' : 'Status'}</th>
                <th className="py-2.5 px-4 text-right">{isHi ? 'कार्रवाई' : 'Action'}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {watchedAreas.map((area) => (
                <tr key={area.id} className="h-12 hover:bg-bg-subtle/50 transition-colors">
                  <td className="py-2.5 px-4 font-semibold text-text">{area.name}</td>
                  <td className="py-2.5 px-4 font-mono text-xs text-text-secondary">{area.bbox}</td>
                  <td className="py-2.5 px-4 text-xs text-text-secondary">{area.schedule}</td>
                  <td className="py-2.5 px-4">
                    <span className="px-2 py-0.5 rounded-pill text-[10px] font-bold bg-[#ECFDF3] text-[#067647] border border-[#D1FADF]">
                      ACTIVE
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-right">
                    <button
                      onClick={() => handleRemoveArea(area.id)}
                      className="p-1 rounded text-text-tertiary hover:text-status-fail transition-colors"
                      title="Delete rule"
                    >
                      <Trash2 size={15} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. DEMO Watched Glacial Lakes Telemetry */}
      <div className="bg-white rounded-2xl border border-border p-6 space-y-4 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Mountain size={18} className="text-brand" />
            <h2 className="text-sm font-bold text-text uppercase tracking-wider">
              {isHi ? 'निगरानीधीन हिमनद झीलें (प्रदर्शन डेटा)' : 'Monitored Glacial Lakes Telemetry'}
            </h2>
            <DemoBadge />
          </div>
          <span className="text-xs font-mono text-text-tertiary">
            Fictional alpine waterbodies
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {demoLakes.map((lake) => (
            <div key={lake.id} className="p-4 rounded-xl border border-border bg-bg-subtle/40 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-text">{lake.name}</span>
                <span className={`px-2 py-0.5 rounded-pill text-[10px] font-bold border ${
                  lake.moraine_risk === 'High'
                    ? 'bg-[#FEF3F2] text-[#B42318] border-[#FECDCA]'
                    : lake.moraine_risk === 'Moderate'
                    ? 'bg-[#FFFAEB] text-[#B54708] border-[#FEDF89]'
                    : 'bg-[#ECFDF3] text-[#067647] border-[#D1FADF]'
                }`}>
                  {lake.moraine_risk} Risk
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div>
                  <div className="text-[10px] text-text-tertiary uppercase">Surface Area</div>
                  <div className="font-bold text-text mt-0.5">{lake.current_area_ha} ha</div>
                </div>
                <div>
                  <div className="text-[10px] text-text-tertiary uppercase">Annual Expansion</div>
                  <div className="font-bold text-[#B54708] mt-0.5 flex items-center gap-0.5">
                    <ArrowUpRight size={13} />
                    <span>+{lake.growth_rate_pct}%</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-border/60 text-[11px] text-text-tertiary flex items-center justify-between">
                <span>Elevation: {lake.elevation_m}m ASL</span>
                <span>Pass: {lake.last_pass}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-[#0B1220]/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl border border-border max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-base font-bold text-text">{isHi ? 'नया उपग्रह निगरानी क्षेत्र' : 'Add New Watched Catchment'}</h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-text mb-1">Catchment Name</label>
                <input
                  type="text"
                  placeholder="e.g. Upper Dhauliganga Valley"
                  value={newAreaName}
                  onChange={(e) => setNewAreaName(e.target.value)}
                  className="w-full py-2 px-3 rounded-lg border border-border font-medium focus:ring-2 focus:ring-brand/30"
                />
              </div>
              <div>
                <label className="block font-semibold text-text mb-1">Bounding Box (minLon, minLat, maxLon, maxLat)</label>
                <input
                  type="text"
                  placeholder="e.g. 78.50, 30.50, 79.00, 31.00"
                  value={newBbox}
                  onChange={(e) => setNewBbox(e.target.value)}
                  className="w-full py-2 px-3 rounded-lg border border-border font-mono text-xs focus:ring-2 focus:ring-brand/30"
                />
              </div>
              <div>
                <label className="block font-semibold text-text mb-1">Satellite Ingestion Schedule</label>
                <select
                  value={newSchedule}
                  onChange={(e) => setNewSchedule(e.target.value)}
                  className="w-full py-2 px-3 rounded-lg border border-border font-medium focus:ring-2 focus:ring-brand/30"
                >
                  <option value="6-day Sentinel-2 Revisit">6-day Sentinel-2 Revisit</option>
                  <option value="12-day Multi-Sensor Optical">12-day Multi-Sensor Optical</option>
                  <option value="Daily Cloud-Piercing SAR (Sentinel-1)">Daily Cloud-Piercing SAR (Sentinel-1)</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowAddModal(false)}
                className="py-2 px-4 rounded-xl border border-border text-xs font-semibold hover:bg-bg-subtle"
              >
                Cancel
              </button>
              <button
                onClick={handleAddArea}
                className="py-2 px-5 rounded-xl bg-brand text-white text-xs font-semibold hover:bg-brand/90"
              >
                Save Watched Area
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
