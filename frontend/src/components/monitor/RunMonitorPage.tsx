import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Play, 
  CheckCircle2, 
  Terminal, 
  Pause, 
  Layers, 
  ArrowRight
} from 'lucide-react';
import { FeatureId } from '../../types';
import { DemoBadge } from '../common/DemoBadge';

interface RunMonitorPageProps {
  onNavigate: (feature: FeatureId) => void;
}

interface RunStage {
  id: string;
  name: string;
  status: 'completed' | 'running' | 'pending';
  duration: string;
}

export const RunMonitorPage: React.FC<RunMonitorPageProps> = ({ onNavigate }) => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  const [selectedRunId, setSelectedRunId] = useState('tier0_ganga_accepted');
  const [runsList, setRunsList] = useState<any[]>([]);
  const [progress, setProgress] = useState(100.0);
  const [currentStage, setCurrentStage] = useState('completed');
  const [runStatus, setRunStatus] = useState('succeeded');
  const [autoScroll, setAutoScroll] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const [logs, setLogs] = useState<string[]>([
    '[00:00:00.120] INFO pravahx.pipeline: Initializing simulation pipeline for Ganga Rishikesh Reach',
    '[00:00:00.450] INFO pravahx.dem: Ingesting Copernicus GLO-30 elevation model (EPSG:32644)',
    '[00:00:01.020] INFO pravahx.hydrology: Breach hydrograph loaded: Q_peak = 5,000 m3/s, T_f = 1.2 hrs (Froehlich 2008)',
    '[00:00:01.890] INFO pravahx.hydrodynamics: Tier-0 flood wave screening engine active',
    '[00:00:03.410] INFO pravahx.hydrodynamics: Maximum water depth matrix computed across 1,840 grid cells',
    '[00:00:04.100] INFO pravahx.impact: Loading WorldPop 2020 100m population raster',
    '[00:00:04.850] INFO pravahx.impact: Computed exposed population = 2,696 citizens across 21 settlements',
    '[00:00:05.210] INFO pravahx.transport: Ingesting OpenStreetMap highway network: 17.34 km severed (>0.30m cutoff)',
    '[00:00:05.900] INFO pravahx.artifacts: Generating Cloud-Optimized GeoTIFF (COG), GeoJSON extent, and brief PDF',
    '[00:00:06.400] INFO pravahx.crypto: SHA-256 integrity hashes computed and sealed in tamper-evident manifest',
    '[00:00:06.520] SUCCESS pravahx.pipeline: Run tier0_ganga_accepted completed in 6.52s. Status: SUCCEEDED',
  ]);

  const logContainerRef = useRef<HTMLDivElement>(null);

  const [recordedLabel, setRecordedLabel] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/v1/runs')
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data?.items) {
          setRunsList(data.items);
        }
      })
      .catch(console.error);
  }, []);

  // Fetch run logs and recorded manifest metadata
  useEffect(() => {
    if (!selectedRunId) return;

    fetch(`/api/v1/runs/${selectedRunId}/logs`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data?.logs && Array.isArray(data.logs)) {
          setLogs(data.logs);
        }
        if (data?.label) {
          setRecordedLabel(data.label);
        } else {
          setRecordedLabel(null);
        }
      })
      .catch(() => {
        setRecordedLabel(null);
      });

    // Handle imported runs vs live runs
    if (selectedRunId === 'delft3d_ganga_dx25') {
      setProgress(100.0);
      setRunStatus('calibrated_pending_gates');
      setCurrentStage('Simulation Complete · Output Indexed');
    } else if (selectedRunId === 'dualsphysics_column_collapse') {
      setProgress(100.0);
      setRunStatus('completed_unvalidated');
      setCurrentStage('Particle Dispatch Complete');
    } else if (selectedRunId === 'tier0_ganga_accepted') {
      setProgress(100.0);
      setRunStatus('succeeded');
      setCurrentStage('completed');
    } else {
      // Check worker availability for newly queued runs
      fetch('/api/v1/workers/status')
        .then(r => r.ok ? r.json() : null)
        .then(wdata => {
          const selected = runsList.find(r => r.id === selectedRunId);
          const engine = selected?.engine || 'tier0';
          if (engine !== 'tier0' && (!wdata?.counts?.[engine] || wdata.counts[engine] === 0)) {
            setProgress(0);
            setRunStatus('waiting_worker');
            setCurrentStage('Waiting for compute worker');
          }
        })
        .catch(console.error);
    }
  }, [selectedRunId, runsList]);

  // Connect SSE or polling for selected run
  useEffect(() => {
    if (!selectedRunId) return;

    const eventSource = new EventSource(`/api/v1/runs/${selectedRunId}/progress`);
    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.progress_percent !== undefined) {
          setProgress(payload.progress_percent);
        }
        if (payload.status) {
          setRunStatus(payload.status);
        }
        if (payload.stage) {
          setCurrentStage(payload.stage);
        }
        if (payload.message) {
          setLogs(prev => [...prev, payload.message]);
        }
      } catch (err) {
        // Ping or non-json message
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [selectedRunId]);

  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const stages: RunStage[] = [
    { id: 'stage_1', name: 'Task Queued & Environment Check', status: 'completed', duration: '0.12s' },
    { id: 'stage_2', name: 'DEM Reprojection & Hydrology Setup', status: 'completed', duration: '0.90s' },
    { id: 'stage_3', name: 'Tier-0 Hydrodynamic Inundation Solver', status: 'completed', duration: '2.39s' },
    { id: 'stage_4', name: 'Impact, OSM Roads & WorldPop Exposure', status: 'completed', duration: '1.80s' },
    { id: 'stage_5', name: 'Artifact Generation & SHA-256 Manifest', status: 'completed', duration: '1.31s' },
  ];

  return (
    <div className="p-6 sm:p-8 max-w-7xl mx-auto space-y-6">
      {/* 1. Header (Part A3 standard) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <div className="text-xs font-mono font-semibold tracking-wider text-text-tertiary uppercase">
            F04 · {isHi ? 'सिमुलेशन रन मॉनिटर' : 'SIMULATION EXECUTION MONITOR'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text mt-1">
            {isHi ? 'क्या मेरा सिमुलेशन रन प्रगति पर है?' : 'Is my run progressing?'}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {isHi
              ? 'हाइड्रोडायनामिक पाइपलाइन निष्पादन स्थिति, सर्वर-सेंट इवेंट्स (SSE) टेलीमेट्री और लॉग स्ट्रीम।'
              : 'Real-time pipeline execution, stage progression, and live execution telemetry.'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('f02_new_scenario')}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-border bg-surface text-text hover:bg-bg-muted font-medium text-sm transition-all shadow-2xs"
          >
            <span>{isHi ? 'नया परिदृश्य बनाएं' : 'New Scenario'}</span>
          </button>
          <button
            onClick={() => onNavigate('f05_results_explorer')}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand hover:bg-brand-hover text-white font-semibold text-sm transition-all shadow-sm active:scale-[0.98]"
          >
            <span>{isHi ? 'परिणाम मानचित्र खोलें' : 'Open Result Map'}</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </div>

      {/* 2. Run Selector & Progress Overview Card */}
      <div className="bg-surface rounded-2xl border border-border p-6 shadow-2xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-4">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
              Selected Run:
            </span>
            <select
              value={selectedRunId}
              onChange={(e) => setSelectedRunId(e.target.value)}
              className="bg-bg-subtle border border-border rounded-xl text-xs font-mono font-bold py-1.5 px-3 focus:outline-none focus:ring-2 focus:ring-brand"
            >
              {runsList.length > 0 ? (
                runsList.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.id} ({r.status})
                  </option>
                ))
              ) : (
                <option value="tier0_ganga_accepted">tier0_ganga_accepted (succeeded)</option>
              )}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold font-mono bg-[#ECFDF3] text-[#027A48] border border-[#A6F4C5]">
              <CheckCircle2 size={13} />
              <span>{runStatus.toUpperCase()} · {currentStage}</span>
            </span>
            <span className="text-xs font-mono text-text-tertiary">
              Elapsed: 6.52s
            </span>
          </div>
        </div>

        {/* Progress Bar & Stage Indicator */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-text">Overall Pipeline Completion</span>
            <span className="font-mono text-brand text-sm">{progress.toFixed(0)}%</span>
          </div>
          <div className="h-3 w-full bg-bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-brand transition-all duration-500 rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* 5-Stage Checklist */}
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 pt-2">
          {stages.map((st, idx) => (
            <div
              key={st.id}
              className="p-3 rounded-xl bg-bg-subtle border border-border space-y-1.5"
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono font-bold text-text-tertiary">
                  STEP 0{idx + 1}
                </span>
                <CheckCircle2 size={14} className="text-[#12B76A]" />
              </div>
              <div className="text-xs font-semibold text-text leading-snug">
                {st.name}
              </div>
              <div className="text-[11px] font-mono text-text-tertiary">
                {st.duration}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 3. Multi-Tier Hydrodynamic Pipeline (§E4 DEMO badge) */}
      <div className="bg-surface rounded-2xl border border-border p-6 shadow-2xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers size={18} className="text-brand" />
            <h3 className="text-sm font-bold text-text">
              Multi-Tier Solver Resolution Hierarchy
            </h3>
          </div>
          <span className="text-xs text-text-secondary">
            Computational Fidelity Continuum
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Tier 0 Card - Active & Passed */}
          <div className="p-4 rounded-xl border-2 border-brand bg-[#F0F6FF] space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-brand uppercase">
                Tier-0 Screening
              </span>
              <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-[#D6F0FF] text-[#0A66FF]">
                Active Solver
              </span>
            </div>
            <h4 className="text-sm font-bold text-text">DEM-Based Diffusion Wave</h4>
            <p className="text-xs text-text-secondary leading-relaxed">
              Sub-minute hydrodynamic screening. Fully computes maximum flood depths and exposure metrics.
            </p>
            <div className="pt-2 text-[11px] font-mono text-brand font-semibold">
              Execution Time: ~6.5 seconds
            </div>
          </div>

          {/* Tier 1 Card - Dimmed DEMO */}
          <div className="p-4 rounded-xl border border-border bg-bg-subtle opacity-70 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-text-secondary uppercase">
                Tier-1 Detailed
              </span>
              <DemoBadge />
            </div>
            <h4 className="text-sm font-bold text-text">2D Shallow Water Equations</h4>
            <p className="text-xs text-text-secondary leading-relaxed">
              Finite volume solver with Riemann flux computation. High-precision unsteady hydrographs.
            </p>
            <div className="pt-2 text-[11px] font-mono text-text-tertiary">
              Requires HPC / Dedicated GPU Cluster
            </div>
          </div>

          {/* Tier 2 Card - Dimmed DEMO */}
          <div className="p-4 rounded-xl border border-border bg-bg-subtle opacity-70 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-text-secondary uppercase">
                Tier-2 Research
              </span>
              <DemoBadge />
            </div>
            <h4 className="text-sm font-bold text-text">3D Smoothed Particle Hydrodynamics</h4>
            <p className="text-xs text-text-secondary leading-relaxed">
              DualSPHysics Lagrangian meshfree solver for direct structural impact forces and turbulence.
            </p>
            <div className="pt-2 text-[11px] font-mono text-text-tertiary">
              Multi-GPU Cluster Research Model
            </div>
          </div>
        </div>
      </div>

      {/* 4. Live Terminal / Execution Logs */}
      <div className="bg-[#0B1220] rounded-2xl border border-[#1E293B] shadow-md overflow-hidden flex flex-col h-[340px]">
        <div className="px-4 py-3 bg-[#0F172A] border-b border-[#1E293B] flex items-center justify-between text-xs">
          <div className="flex items-center gap-3 text-[#94A3B8]">
            <Terminal size={15} />
            <span className="font-mono font-semibold">Telemetry Log Stream ({selectedRunId})</span>
            {recordedLabel && (
              <span className="px-2.5 py-0.5 rounded-full bg-brand/20 text-[#60A5FA] text-[11px] font-mono border border-brand/30">
                {recordedLabel}
              </span>
            )}
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
            <label className="flex items-center gap-1.5 text-[#94A3B8] cursor-pointer">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                className="rounded border-[#334155] text-brand"
              />
              <span>Auto-scroll</span>
            </label>
            <button
              onClick={() => setIsPaused(!isPaused)}
              className="text-[#94A3B8] hover:text-white flex items-center gap-1"
            >
              {isPaused ? <Play size={13} /> : <Pause size={13} />}
              <span>{isPaused ? 'Resume' : 'Pause'}</span>
            </button>
          </div>
        </div>

        <div
          ref={logContainerRef}
          className="flex-1 p-4 overflow-y-auto font-mono text-xs text-[#E2E8F0] space-y-1.5 selection:bg-brand selection:text-white"
        >
          {logs.map((line, idx) => (
            <div
              key={idx}
              className={`leading-relaxed ${
                line.includes('SUCCESS')
                  ? 'text-[#4ADE80] font-bold'
                  : line.includes('INFO')
                  ? 'text-[#94A3B8]'
                  : 'text-white'
              }`}
            >
              {line}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
