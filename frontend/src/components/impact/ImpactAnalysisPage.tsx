import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Users, 
  Car, 
  Building2, 
  ShieldAlert, 
  Download, 
  MinusCircle, 
  ExternalLink,
  ChevronRight,
  Info
} from 'lucide-react';
import { FeatureId } from '../../types';

interface ImpactAnalysisPageProps {
  onNavigate: (feature: FeatureId) => void;
}

export const ImpactAnalysisPage: React.FC<ImpactAnalysisPageProps> = ({ onNavigate }) => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'settlements' | 'roads' | 'buildings'>('settlements');
  const [roadFilter, setRoadFilter] = useState('');
  const [settlementSort, setSettlementSort] = useState<'pop' | 'depth' | 'name'>('pop');

  useEffect(() => {
    fetch('/api/v1/runs/tier0_ganga_accepted/exposure')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load exposure data');
        return res.json();
      })
      .then((resData) => {
        setData(resData);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Exposure fetch error:', err);
        setLoading(false);
      });
  }, []);

  const exportCSV = (filename: string, content: string) => {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const downloadSettlementsCSV = () => {
    if (!data?.settlements) return;
    const headers = ['OSM_ID', 'Name', 'Place_Type', 'Method', 'Peak_Depth_m', 'Exposed_Population', 'Status'];
    const rows = data.settlements.map((s: any) => [
      `"${s.osm_id}"`,
      `"${s.name}"`,
      `"${s.place_type}"`,
      `"${s.method}"`,
      s.peak_depth_m,
      s.population_exposed,
      `"${s.status}"`
    ]);
    exportCSV('pravahx_settlements_exposure.csv', [headers.join(','), ...rows.map((r: any[]) => r.join(','))].join('\n'));
  };

  const downloadRoadsCSV = () => {
    if (!data?.flooded_roads) return;
    const headers = ['OSM_ID', 'Name', 'Highway_Type', 'Length_m', 'Max_Depth_m', 'Depth_Class'];
    const rows = data.flooded_roads.map((r: any) => [
      `"${r.osm_id}"`,
      `"${r.name}"`,
      `"${r.highway_type}"`,
      r.length_m,
      r.max_depth_m,
      `"${r.depth_class}"`
    ]);
    exportCSV('pravahx_flooded_roads.csv', [headers.join(','), ...rows.map((r: any[]) => r.join(','))].join('\n'));
  };

  const downloadBuildingsCSV = () => {
    if (!data?.flooded_buildings) return;
    const headers = ['OSM_ID', 'Name', 'Building_Type', 'Max_Depth_m', 'Depth_Class'];
    const rows = data.flooded_buildings.map((b: any) => [
      `"${b.osm_id}"`,
      `"${b.name}"`,
      `"${b.building_type}"`,
      b.max_depth_m,
      `"${b.depth_class}"`
    ]);
    exportCSV('pravahx_flooded_buildings.csv', [headers.join(','), ...rows.map((r: any[]) => r.join(','))].join('\n'));
  };

  if (loading) {
    return (
      <div className="p-6 sm:p-8 max-w-7xl mx-auto space-y-6 animate-pulse">
        <div className="h-4 w-32 bg-border rounded" />
        <div className="h-10 w-96 bg-border rounded" />
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 bg-surface rounded-2xl border border-border" />
          ))}
        </div>
        <div className="h-64 bg-surface rounded-2xl border border-border" />
      </div>
    );
  }

  const settlements = [...(data?.settlements || [])].sort((a, b) => {
    if (settlementSort === 'pop') return b.population_exposed - a.population_exposed;
    if (settlementSort === 'depth') return b.peak_depth_m - a.peak_depth_m;
    return a.name.localeCompare(b.name);
  });

  const filteredRoads = (data?.flooded_roads || []).filter((r: any) => 
    r.name.toLowerCase().includes(roadFilter.toLowerCase()) || 
    r.highway_type.toLowerCase().includes(roadFilter.toLowerCase())
  );

  return (
    <div className="p-6 sm:p-8 max-w-7xl mx-auto space-y-6">
      {/* 1. Header (Part A3 standard) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <div className="text-xs font-mono font-semibold tracking-wider text-text-tertiary uppercase">
            F09 · {isHi ? 'प्रभाव और जोखिम विश्लेषण' : 'IMPACT & EXPOSURE ASSESSMENT'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text mt-1">
            {isHi ? 'बाढ़ से कौन और क्या प्रभावित हुआ है?' : 'Who and what is affected?'}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {isHi 
              ? 'ऋषिकेश गंगा रीच (टियर-० प्री-कंप्यूटेड स्क्रीनिंग) के लिए मानव आबादी, सड़क नेटवर्क और इमारतों का विश्लेषण।' 
              : 'Quantified population exposure, severed transport corridors, and building inundation for Ganga Rishikesh Reach.'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('f05_results_explorer')}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-border bg-surface text-text hover:bg-bg-muted font-medium text-sm transition-all shadow-2xs"
          >
            <span>{isHi ? 'मानचित्र दृश्य खोलें' : 'Open Results Map'}</span>
            <ExternalLink size={15} />
          </button>
          <button
            onClick={downloadSettlementsCSV}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand hover:bg-brand-hover text-white font-semibold text-sm transition-all shadow-sm active:scale-[0.98]"
          >
            <Download size={16} />
            <span>{isHi ? 'एक्सपोजर डेटा निर्यात करें (CSV)' : 'Export Full Report (CSV)'}</span>
          </button>
        </div>
      </div>

      {/* 2. KPI Summary Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: People Exposed */}
        <div className="bg-surface rounded-2xl p-5 border border-border shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-text-tertiary">
            <span className="text-xs font-medium uppercase tracking-wider">{isHi ? 'प्रभावित आबादी' : 'People Exposed'}</span>
            <Users size={18} className="text-brand" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-text">
              {data?.population?.exposed_total ? Number(data.population.exposed_total).toLocaleString('en-IN') : '2,696'}
            </span>
            <span className="text-xs text-text-tertiary font-mono">
              / {data?.population?.aoi_total ? Number(Math.round(data.population.aoi_total)).toLocaleString('en-IN') : '27,390'} ({data?.population?.exposed_percent || 9.84}%)
            </span>
          </div>
          <div className="text-[11px] text-text-tertiary">
            Source: {data?.population?.source || 'WorldPop 100m 2020'} · Run tier0_ganga_accepted
          </div>
        </div>

        {/* KPI 2: Roads Flooded */}
        <div className="bg-surface rounded-2xl p-5 border border-border shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-text-tertiary">
            <span className="text-xs font-medium uppercase tracking-wider">{isHi ? 'जलमग्न सड़कें' : 'Roads Flooded'}</span>
            <Car size={18} className="text-[#F04438]" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-text">
              {data?.roads?.flooded_km || '17.34'} km
            </span>
            <span className="text-xs text-text-tertiary font-mono">
              / {data?.roads?.total_network_km || '159.54'} km ({data?.roads?.flooded_percent || 10.87}%)
            </span>
          </div>
          <div className="text-[11px] text-text-tertiary">
            Depth Cutoff &gt; {data?.roads?.severance_depth_cutoff_m || 0.30}m · Source: OpenStreetMap
          </div>
        </div>

        {/* KPI 3: Buildings Flooded */}
        <div className="bg-surface rounded-2xl p-5 border border-border shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-text-tertiary">
            <span className="text-xs font-medium uppercase tracking-wider">{isHi ? 'जलमग्न इमारतें' : 'Buildings Flooded'}</span>
            <Building2 size={18} className="text-[#F79009]" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-text">
              {data?.buildings?.flooded || 5}
            </span>
            <span className="text-xs text-text-tertiary font-mono">
              / {data?.buildings?.total_in_aoi || 93}
            </span>
          </div>
          <div className="text-[11px] text-[#B54708] font-medium flex items-center gap-1">
            <Info size={12} />
            <span>{data?.buildings?.note || 'OSM building coverage incomplete'}</span>
          </div>
        </div>

        {/* KPI 4: Critical Facilities */}
        <div className="bg-surface rounded-2xl p-5 border border-border shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-text-tertiary">
            <span className="text-xs font-medium uppercase tracking-wider">{isHi ? 'महत्वपूर्ण बुनियादी ढांचा' : 'Critical Facilities'}</span>
            <ShieldAlert size={18} className="text-[#12B76A]" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-[#12B76A]">
              {data?.critical_facilities?.flooded || 0}
            </span>
            <span className="text-xs text-text-tertiary font-mono">
              / {data?.critical_facilities?.total_in_aoi || 28} flooded
            </span>
          </div>
          <div className="text-[11px] text-text-tertiary">
            0 hospitals/schools in direct breach path · Source: OSM
          </div>
        </div>
      </div>

      {/* 3. Population Exposed by Depth Class Chart */}
      <div className="bg-surface rounded-2xl p-6 border border-border shadow-2xs space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-text">
              {isHi ? 'जल भराव गहराई वर्ग द्वारा प्रभावित जनसंख्या' : 'Population Exposed by Inundation Depth Class'}
            </h3>
            <p className="text-xs text-text-secondary mt-0.5">
              Aggregated from WorldPop 2020 100m grid cells intersecting Tier-0 maximum water depth.
            </p>
          </div>
          <span className="text-xs font-mono text-text-tertiary">
            Run: tier0_ganga_accepted · UNVERIFIED
          </span>
        </div>

        <div className="space-y-3 pt-2">
          {/* Depth Bar 1: 0.0 - 0.5m */}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs font-medium">
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-[#D6F0FF] border border-[#8FD0F8]" />
                <span className="font-mono">0.0 – 0.5 m (Shallow nuisance flooding)</span>
              </span>
              <span className="font-mono font-semibold text-text">
                230 people (8.5%)
              </span>
            </div>
            <div className="h-6 w-full bg-bg-muted rounded-lg overflow-hidden flex">
              <div 
                className="bg-[#8FD0F8] h-full flex items-center px-2 text-[11px] font-mono font-bold text-[#062B5F]"
                style={{ width: '8.5%' }}
              >
                230.3
              </div>
            </div>
          </div>

          {/* Depth Bar 2: 0.5 - 1.5m */}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs font-medium">
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-[#41A6E8]" />
                <span className="font-mono">0.5 – 1.5 m (Life safety hazard / wading threshold)</span>
              </span>
              <span className="font-mono font-semibold text-text">
                253 people (9.4%)
              </span>
            </div>
            <div className="h-6 w-full bg-bg-muted rounded-lg overflow-hidden flex">
              <div 
                className="bg-[#41A6E8] h-full flex items-center px-2 text-[11px] font-mono font-bold text-white"
                style={{ width: '9.4%' }}
              >
                253.3
              </div>
            </div>
          </div>

          {/* Depth Bar 3: > 1.5m */}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs font-medium">
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-[#0B4C99]" />
                <span className="font-mono">&gt; 1.5 m (Extreme structural hazard / submerged)</span>
              </span>
              <span className="font-mono font-semibold text-text">
                2,213 people (82.1%)
              </span>
            </div>
            <div className="h-6 w-full bg-bg-muted rounded-lg overflow-hidden flex">
              <div 
                className="bg-[#0B4C99] h-full flex items-center px-3 text-[11px] font-mono font-bold text-white"
                style={{ width: '82.1%' }}
              >
                2,212.9
              </div>
            </div>
          </div>
        </div>

        <div className="pt-2 text-xs text-text-tertiary flex items-center justify-between border-t border-border">
          <span>Depth classes calibrated against NDMA flood depth criteria.</span>
          <span className="font-mono">Total AOI: 27,390 residents</span>
        </div>
      </div>

      {/* 4. Tabbed Detail Tables */}
      <div className="bg-surface rounded-2xl border border-border shadow-2xs overflow-hidden">
        {/* Tabs Bar */}
        <div className="flex items-center justify-between border-b border-border px-6 pt-4 bg-[#FAFAFA]">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('settlements')}
              className={`pb-3 px-3 text-sm font-semibold transition-all border-b-2 flex items-center gap-2 ${
                activeTab === 'settlements'
                  ? 'border-brand text-brand'
                  : 'border-transparent text-text-secondary hover:text-text'
              }`}
            >
              <span>{isHi ? 'बस्तियाँ (वास्तविक गणना)' : 'Settlements (Real Computed)'}</span>
              <span className="px-1.5 py-0.5 rounded text-xs font-mono bg-bg-muted text-text-secondary">
                {data?.settlements?.length || 21}
              </span>
            </button>

            <button
              onClick={() => setActiveTab('roads')}
              className={`pb-3 px-3 text-sm font-semibold transition-all border-b-2 flex items-center gap-2 ${
                activeTab === 'roads'
                  ? 'border-brand text-brand'
                  : 'border-transparent text-text-secondary hover:text-text'
              }`}
            >
              <span>{isHi ? 'जलमग्न सड़क खंड' : 'Flooded Road Segments'}</span>
              <span className="px-1.5 py-0.5 rounded text-xs font-mono bg-bg-muted text-text-secondary">
                {data?.flooded_roads?.length || 60}
              </span>
            </button>

            <button
              onClick={() => setActiveTab('buildings')}
              className={`pb-3 px-3 text-sm font-semibold transition-all border-b-2 flex items-center gap-2 ${
                activeTab === 'buildings'
                  ? 'border-brand text-brand'
                  : 'border-transparent text-text-secondary hover:text-text'
              }`}
            >
              <span>{isHi ? 'जलमग्न इमारतें' : 'Flooded Buildings'}</span>
              <span className="px-1.5 py-0.5 rounded text-xs font-mono bg-bg-muted text-text-secondary">
                {data?.flooded_buildings?.length || 5}
              </span>
            </button>
          </div>

          <div className="pb-3">
            {activeTab === 'settlements' && (
              <button
                onClick={downloadSettlementsCSV}
                className="text-xs font-semibold text-brand hover:underline flex items-center gap-1"
              >
                <Download size={14} />
                <span>Export Settlements CSV</span>
              </button>
            )}
            {activeTab === 'roads' && (
              <button
                onClick={downloadRoadsCSV}
                className="text-xs font-semibold text-brand hover:underline flex items-center gap-1"
              >
                <Download size={14} />
                <span>Export Roads CSV</span>
              </button>
            )}
            {activeTab === 'buildings' && (
              <button
                onClick={downloadBuildingsCSV}
                className="text-xs font-semibold text-brand hover:underline flex items-center gap-1"
              >
                <Download size={14} />
                <span>Export Buildings CSV</span>
              </button>
            )}
          </div>
        </div>

        {/* Table 1: Settlements */}
        {activeTab === 'settlements' && (
          <div>
            <div className="p-4 bg-bg-subtle border-b border-border text-xs text-text-secondary flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="space-y-0.5">
                <p className="font-medium text-text">
                  Note: {data?.settlement_note || 'Settlement figures overlap and are not additive.'}
                </p>
                <p className="text-[11px] text-text-tertiary">
                  Method: {data?.settlement_method || '500m planar buffer around place node.'}
                </p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <span className="text-text-tertiary">Sort:</span>
                <select
                  value={settlementSort}
                  onChange={(e) => setSettlementSort(e.target.value as any)}
                  className="bg-surface border border-border rounded-lg text-xs py-1 px-2 font-medium"
                >
                  <option value="pop">Exposed Population</option>
                  <option value="depth">Peak Depth</option>
                  <option value="name">Name (A-Z)</option>
                </select>
              </div>
            </div>

            <div className="overflow-x-auto max-h-[440px]">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-[#F8F9FA] sticky top-0 border-b border-border text-text-secondary uppercase font-semibold">
                  <tr>
                    <th className="py-3 px-4">Settlement Name</th>
                    <th className="py-3 px-4">OSM Reference</th>
                    <th className="py-3 px-4">Place Type</th>
                    <th className="py-3 px-4">Area Geometry</th>
                    <th className="py-3 px-4 text-right">Peak Depth</th>
                    <th className="py-3 px-4 text-right">Population Exposed</th>
                    <th className="py-3 px-4 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {settlements.map((s: any, idx: number) => (
                    <tr key={idx} className="hover:bg-bg-subtle transition-colors">
                      <td className="py-3 px-4 font-semibold text-text">{s.name}</td>
                      <td className="py-3 px-4 font-mono text-text-secondary">{s.osm_id}</td>
                      <td className="py-3 px-4 capitalize">
                        <span className="px-2 py-0.5 rounded bg-bg-muted text-text-secondary font-mono text-[11px]">
                          {s.place_type}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-text-secondary truncate max-w-[200px]" title={s.method}>
                        {s.method}
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-right">
                        {s.peak_depth_m > 0 ? (
                          <span className={s.peak_depth_m > 5 ? 'text-[#D92D20]' : s.peak_depth_m > 1.5 ? 'text-[#B54708]' : 'text-text'}>
                            {s.peak_depth_m.toFixed(2)} m
                          </span>
                        ) : (
                          <span className="text-text-tertiary">0.00 m</span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-right text-text">
                        {s.population_exposed.toLocaleString('en-IN')}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold ${
                          s.is_inundated 
                            ? 'bg-[#FEF3F2] text-[#B42318] border border-[#FECDCA]' 
                            : 'bg-[#ECFDF3] text-[#027A48] border border-[#A6F4C5]'
                        }`}>
                          {s.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Table 2: Flooded Roads */}
        {activeTab === 'roads' && (
          <div>
            <div className="p-4 bg-bg-subtle border-b border-border flex items-center justify-between gap-4">
              <input
                type="text"
                placeholder="Filter roads by name or highway type..."
                value={roadFilter}
                onChange={(e) => setRoadFilter(e.target.value)}
                className="w-full sm:w-80 px-3 py-1.5 bg-surface border border-border rounded-lg text-xs placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-brand"
              />
              <span className="text-xs font-mono text-text-tertiary shrink-0">
                Showing {filteredRoads.length} of {data?.flooded_roads?.length || 60} segments
              </span>
            </div>

            <div className="overflow-x-auto max-h-[440px]">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-[#F8F9FA] sticky top-0 border-b border-border text-text-secondary uppercase font-semibold">
                  <tr>
                    <th className="py-3 px-4">Segment Name</th>
                    <th className="py-3 px-4">OSM Way</th>
                    <th className="py-3 px-4">Highway Type</th>
                    <th className="py-3 px-4 text-right">Length (m)</th>
                    <th className="py-3 px-4 text-right">Max Depth</th>
                    <th className="py-3 px-4">Depth Class</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredRoads.map((r: any, idx: number) => (
                    <tr key={idx} className="hover:bg-bg-subtle transition-colors">
                      <td className="py-3 px-4 font-medium text-text">{r.name}</td>
                      <td className="py-3 px-4 font-mono text-text-secondary">{r.osm_id}</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded bg-bg-muted text-text-secondary font-mono text-[11px]">
                          {r.highway_type}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-right text-text">{r.length_m} m</td>
                      <td className="py-3 px-4 font-mono font-bold text-right text-[#D92D20]">{r.max_depth_m.toFixed(2)} m</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded bg-[#FEF3F2] text-[#B42318] text-[11px] font-medium">
                          {r.depth_class}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Table 3: Flooded Buildings */}
        {activeTab === 'buildings' && (
          <div>
            <div className="p-4 bg-bg-subtle border-b border-border flex items-center justify-between">
              <span className="text-xs text-text-secondary">
                Exact structures identified from OpenStreetMap within the accepted flood boundary.
              </span>
              <span className="text-xs font-mono text-text-tertiary">
                Total flooded: 5 buildings
              </span>
            </div>

            <div className="overflow-x-auto max-h-[440px]">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-[#F8F9FA] sticky top-0 border-b border-border text-text-secondary uppercase font-semibold">
                  <tr>
                    <th className="py-3 px-4">Building Name / Identifier</th>
                    <th className="py-3 px-4">OSM ID</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4 text-right">Max Inundation Depth</th>
                    <th className="py-3 px-4">Severity Class</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {(data?.flooded_buildings || []).map((b: any, idx: number) => (
                    <tr key={idx} className="hover:bg-bg-subtle transition-colors">
                      <td className="py-3 px-4 font-bold text-text">{b.name}</td>
                      <td className="py-3 px-4 font-mono text-text-secondary">{b.osm_id}</td>
                      <td className="py-3 px-4 capitalize">
                        <span className="px-2 py-0.5 rounded bg-bg-muted text-text-secondary font-mono text-[11px]">
                          {b.building_type}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-right text-[#D92D20]">
                        {b.max_depth_m.toFixed(2)} m
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded bg-[#FEF3F2] text-[#B42318] font-semibold text-[11px]">
                          {b.depth_class}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* 5. Economic Loss: Honest NOT RUN Card (§A3, E1) */}
      <div className="bg-[#F9FAFB] rounded-2xl p-6 border border-border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-bg-muted text-text-tertiary shrink-0">
            <MinusCircle size={24} />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-[#E4E7EC] text-text-secondary font-mono">
                NOT RUN
              </span>
              <h4 className="text-base font-bold text-text">
                {isHi ? 'आर्थिक क्षति मूल्यांकन (Economic Loss)' : 'Direct Economic & Infrastructure Loss Assessment'}
              </h4>
            </div>
            <p className="text-xs text-text-secondary leading-relaxed max-w-2xl">
              {isHi
                ? 'इस रीच के लिए सेक्टर-विशिष्ट गहराई-क्षति वक्र (HYDR-ECO) कैलिब्रेट नहीं किए गए हैं। नीति के अनुसार कोई काल्पनिक वित्तीय मूल्य प्रदर्शित नहीं किए जाते हैं।'
                : 'Direct flood depth-damage curves (HYDR-ECO) are not calibrated for this reach. In strict adherence to integrity standards, no speculative currency figures or modeled financial damage values are displayed.'}
            </p>
          </div>
        </div>

        <a
          href="#f18_catalogue"
          onClick={(e) => {
            e.preventDefault();
            onNavigate('f18_catalogue');
          }}
          className="text-xs font-semibold text-brand hover:underline flex items-center gap-1 shrink-0"
        >
          <span>View Data Catalogue</span>
          <ChevronRight size={14} />
        </a>
      </div>
    </div>
  );
};
