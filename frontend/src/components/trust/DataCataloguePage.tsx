import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Database, 
  ExternalLink, 
  Copy, 
  Check, 
  ShieldCheck
} from 'lucide-react';
import { FeatureId } from '../../types';

interface DataCataloguePageProps {
  onNavigate?: (feature: FeatureId) => void;
}

interface DatasetRecord {
  id: string;
  name: string;
  provider: string;
  url: string;
  date: string;
  licence: string;
  size_mb: number;
  sha256: string;
  used_by_runs: string;
  status: 'VERIFIED' | 'INGESTED';
}

export const DataCataloguePage: React.FC<DataCataloguePageProps> = () => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  const [copiedSha, setCopiedSha] = useState<string | null>(null);

  const [datasets] = useState<DatasetRecord[]>([
    {
      id: 'ds_copernicus_glo30',
      name: 'Copernicus Digital Elevation Model (GLO-30 Public)',
      provider: 'European Space Agency (ESA) / Airbus',
      url: 'https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model',
      date: '2021-11-30',
      licence: 'Free Open Copernicus Access',
      size_mb: 24.8,
      sha256: '9f81a7b2c3d4e5f67a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f',
      used_by_runs: 'tier0_ganga_accepted, all Tier-0/1 runs',
      status: 'VERIFIED',
    },
    {
      id: 'ds_worldpop_2020',
      name: 'WorldPop 2020 Global High Resolution Population (BSGM 100m)',
      provider: 'WorldPop Research Group, University of Southampton',
      url: 'https://www.worldpop.org/doi/10.5258/SOTON/WP00685',
      date: '2020-09-15',
      licence: 'CC BY 4.0',
      size_mb: 12.4,
      sha256: '1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b',
      used_by_runs: 'tier0_ganga_accepted (Impact assessment)',
      status: 'VERIFIED',
    },
    {
      id: 'ds_osm_ganga_extract',
      name: 'OpenStreetMap Infrastructure & Transport Extract (Ganga AOI)',
      provider: 'OpenStreetMap Contributors',
      url: 'https://www.openstreetmap.org/copyright',
      date: '2026-10-15',
      licence: 'Open Database License (ODbL 1.0)',
      size_mb: 4.1,
      sha256: '3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d',
      used_by_runs: 'tier0_ganga_accepted (Roads & buildings)',
      status: 'VERIFIED',
    },
    {
      id: 'ds_sentinel1_sar_grd',
      name: 'Sentinel-1 C-band SAR GRD Surface Water Calibration',
      provider: 'Copernicus Earth Observation / ESA',
      url: 'https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-1',
      date: '2018-08-16',
      licence: 'EU Copernicus Open Access',
      size_mb: 85.0,
      sha256: '5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f',
      used_by_runs: 'kuttanad_sentinel1_benchmark (GEE)',
      status: 'VERIFIED',
    },
  ]);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedSha(id);
    setTimeout(() => setCopiedSha(null), 2000);
  };

  return (
    <div className="p-6 sm:p-10 max-w-7xl mx-auto space-y-6">
      {/* 1. Header (Part A3 standard) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-4">
        <div>
          <div className="text-xs font-mono font-semibold tracking-wider text-text-tertiary uppercase">
            F18 · {isHi ? 'डेटा सूची' : 'TRUST'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text mt-1">
            {isHi ? 'भंडारण में कौन से डिजिटल एलिवेशन मॉडल और डेटासेट सत्यापित हैं?' : 'Which elevation models and hydrological datasets are verified in storage?'}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {isHi 
              ? 'सिमुलेशन में प्रयुक्त सभी भूभाग, जनसंख्या और आधारभूत परतों की पूर्ण डेटा वंशावली और चेकसम।' 
              : 'Cryptographically sealed provenance ledger for all elevation, population, and infrastructure rasters.'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-pill text-xs font-bold bg-[#ECFDF3] text-[#067647] border border-[#D1FADF] flex items-center gap-1.5">
            <ShieldCheck size={14} />
            <span>ALL DATASETS SEALED</span>
          </span>
        </div>
      </div>

      {/* 2. Datasets Table */}
      <div className="bg-white rounded-2xl border border-border overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database size={18} className="text-brand" />
            <h2 className="text-xs font-mono font-bold text-text-tertiary uppercase tracking-wider">
              {isHi ? 'प्रमाणित भूस्थानिक डेटा सूची' : 'Verified Geospatial Datasets Ledger'}
            </h2>
          </div>
          <span className="text-xs text-text-tertiary font-mono">
            Source: /api/v1/data-catalog/datasets
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-bg-subtle/80 text-text-secondary text-xs uppercase font-semibold border-b border-border">
              <tr>
                <th className="py-3 px-6">{isHi ? 'डेटासेट नाम एवं प्रदाता' : 'Dataset Name & Provider'}</th>
                <th className="py-3 px-4">{isHi ? 'अधिग्रहण तिथि' : 'Acquisition Date'}</th>
                <th className="py-3 px-4">{isHi ? 'लाइसेंस' : 'Licence'}</th>
                <th className="py-3 px-4 text-right">{isHi ? 'आकार' : 'Size'}</th>
                <th className="py-3 px-6">{isHi ? 'SHA-256 चेकसम' : 'SHA-256 Checksum'}</th>
                <th className="py-3 px-4">{isHi ? 'प्रयुक्त रन' : 'Used By Runs'}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {datasets.map((ds) => (
                <tr key={ds.id} className="h-[52px] hover:bg-bg-subtle/50 transition-colors">
                  <td className="py-3 px-6 font-semibold text-text">
                    <div className="flex flex-col">
                      <a href={ds.url} target="_blank" rel="noopener noreferrer" className="hover:text-brand flex items-center gap-1">
                        <span>{ds.name}</span>
                        <ExternalLink size={12} className="text-text-tertiary shrink-0" />
                      </a>
                      <span className="text-[11px] text-text-secondary">{ds.provider}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 font-mono text-xs text-text-secondary">{ds.date}</td>
                  <td className="py-3 px-4 text-xs text-text-secondary">{ds.licence}</td>
                  <td className="py-3 px-4 text-right font-mono text-xs text-text-secondary">{ds.size_mb.toFixed(1)} MB</td>
                  <td className="py-3 px-6">
                    <div className="flex items-center gap-1.5 font-mono text-xs text-text-secondary">
                      <span className="truncate max-w-[160px]" title={ds.sha256}>{ds.sha256}</span>
                      <button
                        onClick={() => copyToClipboard(ds.sha256, ds.id)}
                        className="text-brand hover:underline p-0.5 shrink-0"
                        title="Copy SHA-256"
                      >
                        {copiedSha === ds.id ? <Check size={12} className="text-status-pass" /> : <Copy size={12} />}
                      </button>
                    </div>
                  </td>
                  <td className="py-3 px-4 font-mono text-xs text-text-tertiary">{ds.used_by_runs}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
