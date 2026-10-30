import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Upload, 
  CheckCircle2, 
  Clock
} from 'lucide-react';
import { FeatureId } from '../../types';
import { DemoBadge } from '../common/DemoBadge';

interface BatchRunsPageProps {
  onNavigate?: (feature: FeatureId) => void;
}

interface BatchItem {
  id: string;
  dam_name: string;
  state: string;
  inflow_m3s: number;
  status: 'completed' | 'running' | 'queued' | 'failed';
  duration_s?: number;
  max_depth_m?: number;
}

export const BatchRunsPage: React.FC<BatchRunsPageProps> = () => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  const [batchItems] = useState<BatchItem[]>([
    { id: 'batch_01', dam_name: 'Ganga Valley Reach #1', state: 'Uttarakhand', inflow_m3s: 5000, status: 'completed', duration_s: 2.1, max_depth_m: 7.73 },
    { id: 'batch_02', dam_name: 'Peninsular Basin Weir #4', state: 'Maharashtra', inflow_m3s: 3400, status: 'completed', duration_s: 1.9, max_depth_m: 4.12 },
    { id: 'batch_03', dam_name: 'Western Catchment Embankment', state: 'Karnataka', inflow_m3s: 4800, status: 'running' },
    { id: 'batch_04', dam_name: 'Eastern Sub-Basin Sluice', state: 'Odisha', inflow_m3s: 2900, status: 'queued' },
    { id: 'batch_05', dam_name: 'Northern Tributary Check-Dam', state: 'Himachal Pradesh', inflow_m3s: 1800, status: 'queued' },
  ]);

  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const handleSimulateUpload = () => {
    setIsUploading(true);
    setTimeout(() => {
      setIsUploading(false);
      setUploadSuccess(true);
      setTimeout(() => setUploadSuccess(false), 3000);
    }, 1000);
  };

  return (
    <div className="p-6 sm:p-10 max-w-7xl mx-auto space-y-6">
      {/* 1. Header (Part A3 standard) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-4">
        <div>
          <div className="text-xs font-mono font-semibold tracking-wider text-text-tertiary uppercase">
            F15 · {isHi ? 'बैच प्रसंस्करण' : 'BATCH PROCESSING'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text mt-1">
            {isHi ? 'क्या हम सभी ६,५९८ पंजीकृत बांधों की एक साथ स्क्रीनिंग कर सकते हैं?' : 'Can we screen all 6,598 registered large dams concurrently?'}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {isHi 
              ? 'CSV पैरामीटर फ़ाइल अपलोड करें अथवा राष्ट्रीय बड़े बांध रजिस्टर का स्वचालित बैच रन निष्पादित करें।' 
              : 'Queue concurrent Tier-0 screening sweeps across national dam inventories via asynchronous workers.'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="py-2.5 px-4 rounded-xl border border-border text-text font-medium text-sm hover:bg-bg-subtle active:scale-[0.98] transition-all flex items-center gap-2 cursor-pointer">
            <Upload size={16} />
            <span>{isUploading ? (isHi ? 'अपलोड हो रहा है...' : 'Uploading...') : (isHi ? 'CSV बैच अपलोड करें' : 'Upload Batch CSV')}</span>
            <input type="file" accept=".csv" onChange={handleSimulateUpload} className="hidden" />
          </label>
        </div>
      </div>

      {uploadSuccess && (
        <div className="p-4 rounded-xl bg-[#ECFDF3] border border-[#D1FADF] text-[#067647] text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 size={16} />
          <span>{isHi ? 'बैच कार्य कतार में सफलतापूर्वक जोड़ा गया (5 नए कार्य)' : 'Batch jobs submitted to Celery queue (5 items scheduled)'}</span>
        </div>
      )}

      {/* 2. KPI Summary Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl border border-border p-5 space-y-1 shadow-xs">
          <div className="text-[11px] font-mono text-text-tertiary uppercase">Total in Sweep</div>
          <div className="text-2xl font-bold text-text">6,598</div>
          <div className="text-[10px] text-text-secondary">NRLD Monitored Structures</div>
        </div>

        <div className="bg-white rounded-2xl border border-border p-5 space-y-1 shadow-xs">
          <div className="text-[11px] font-mono text-text-tertiary uppercase">Completed Runs</div>
          <div className="text-2xl font-bold text-status-pass">2</div>
          <div className="text-[10px] text-text-secondary">Avg runtime: 2.0s per dam</div>
        </div>

        <div className="bg-white rounded-2xl border border-border p-5 space-y-1 shadow-xs">
          <div className="text-[11px] font-mono text-text-tertiary uppercase">In Progress</div>
          <div className="text-2xl font-bold text-brand">1</div>
          <div className="text-[10px] text-text-secondary">Worker pool: 4 concurrency</div>
        </div>

        <div className="bg-white rounded-2xl border border-border p-5 space-y-1 shadow-xs">
          <div className="text-[11px] font-mono text-text-tertiary uppercase">Queued Tasks</div>
          <div className="text-2xl font-bold text-text-secondary">2</div>
          <div className="text-[10px] text-text-secondary">Redis broker / Celery</div>
        </div>
      </div>

      {/* 3. Batch Queue Table */}
      <div className="bg-white rounded-2xl border border-border overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold text-text-tertiary uppercase tracking-wider">
              {isHi ? 'सक्रिय बैच कतार' : 'Active Batch Execution Queue'}
            </span>
            <DemoBadge />
          </div>
          <span className="text-xs text-text-tertiary font-mono">
            Source: /api/v1/batches
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-bg-subtle/80 text-text-secondary text-xs uppercase font-semibold border-b border-border sticky top-0">
              <tr>
                <th className="py-3 px-6">{isHi ? 'कार्य आईडी एवं संरचना' : 'Job ID & Structure'}</th>
                <th className="py-3 px-4">{isHi ? 'राज्य / क्षेत्र' : 'State / Region'}</th>
                <th className="py-3 px-4 text-right">{isHi ? 'चरम प्रवाह' : 'Peak Inflow'}</th>
                <th className="py-3 px-4">{isHi ? 'स्थिति' : 'Execution Status'}</th>
                <th className="py-3 px-4 text-right">{isHi ? 'गणना समय' : 'Compute Time'}</th>
                <th className="py-3 px-4 text-right">{isHi ? 'चरम गहराई' : 'Max Depth'}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {batchItems.map((item) => (
                <tr key={item.id} className="h-[52px] hover:bg-bg-subtle/50 transition-colors">
                  <td className="py-3 px-6 font-semibold text-text">
                    <div className="flex flex-col">
                      <span>{item.dam_name}</span>
                      <span className="text-[11px] font-mono text-text-tertiary">{item.id}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-text-secondary">{item.state}</td>
                  <td className="py-3 px-4 text-right font-mono font-semibold text-brand">
                    {item.inflow_m3s.toLocaleString()} m³/s
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2.5 py-0.5 rounded-pill text-[11px] font-bold border inline-flex items-center gap-1 ${
                      item.status === 'completed'
                        ? 'bg-[#ECFDF3] text-[#067647] border-[#D1FADF]'
                        : item.status === 'running'
                        ? 'bg-[#EFF8FF] text-[#175CD3] border-[#B2DDFF]'
                        : 'bg-[#F2F4F7] text-[#475467] border-[#D0D5DD]'
                    }`}>
                      {item.status === 'completed' && <CheckCircle2 size={12} />}
                      {item.status === 'running' && <span className="w-1.5 h-1.5 rounded-full bg-brand animate-ping" />}
                      {item.status === 'queued' && <Clock size={12} />}
                      <span className="uppercase">{item.status}</span>
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-text-secondary">
                    {item.duration_s ? `${item.duration_s.toFixed(1)}s` : '—'}
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-bold text-text">
                    {item.max_depth_m ? `${item.max_depth_m.toFixed(2)} m` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
