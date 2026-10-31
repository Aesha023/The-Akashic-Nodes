import React, { useEffect, useState, useId } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  MinusCircle, 
  RefreshCw, 
  ChevronDown, 
  ChevronUp, 
  ExternalLink,
  BookOpen
} from 'lucide-react';
import { FeatureId } from '../../types';

interface ValidationBenchmarksPageProps {
  onNavigate?: (feature: FeatureId) => void;
}

interface BenchmarkMetric {
  label: string;
  value: string;
}

interface ChartPoint {
  x: number;
  h_theory: number;
  h_sim: number;
}

interface BenchmarkItem {
  id: string;
  badge: string;
  title: string;
  subtitle: string;
  status: 'RUN AND PASSED' | 'PENDING / RUN AND FAILED' | 'RUN · NOT YET VALIDATED' | 'NOT RUN';
  status_variant: 'pass' | 'warning' | 'neutral' | 'muted';
  citation: string;
  description: string;
  reason?: string;
  notes?: string;
  metrics: BenchmarkMetric[];
  chart?: {
    domain: [number, number];
    t_seconds: number;
    dam_x: number;
    x_tail: number;
    x_front: number;
    points: ChartPoint[];
  };
}

interface ApiResponse {
  title: string;
  provenance_standard: string;
  benchmarks: BenchmarkItem[];
}

export const ValidationBenchmarksPage: React.FC<ValidationBenchmarksPageProps> = () => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ApiResponse | null>(null);
  const [showTechnicalError, setShowTechnicalError] = useState(false);
  const [hoveredPoint, setHoveredPoint] = useState<ChartPoint | null>(null);

  const filterId = useId();

  const fetchBenchmarks = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/validation/benchmarks');
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: Failed to fetch validation benchmarks`);
      }
      const json: ApiResponse = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err?.message || 'Network error fetching scientific validation benchmarks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBenchmarks();
  }, []);

  const getStatusBadge = (status: BenchmarkItem['status']) => {
    switch (status) {
      case 'RUN AND PASSED':
        return (
          <span className="px-2.5 py-1 rounded-pill text-xs font-bold bg-[#ECFDF3] text-[#067647] border border-[#D1FADF] inline-flex items-center gap-1.5 shadow-2xs">
            <CheckCircle2 size={13} className="text-[#067647]" />
            <span>{status}</span>
          </span>
        );
      case 'PENDING / RUN AND FAILED':
        return (
          <span className="px-2.5 py-1 rounded-pill text-xs font-bold bg-[#FFFAEB] text-[#B54708] border border-[#FEDF89] inline-flex items-center gap-1.5 shadow-2xs">
            <AlertCircle size={13} className="text-[#B54708]" />
            <span>{status}</span>
          </span>
        );
      case 'RUN · NOT YET VALIDATED':
        return (
          <span className="px-2.5 py-1 rounded-pill text-xs font-bold bg-[#F2F4F7] text-[#475467] border border-[#D0D5DD] inline-flex items-center gap-1.5 shadow-2xs">
            <Clock size={13} className="text-[#475467]" />
            <span>{status}</span>
          </span>
        );
      case 'NOT RUN':
      default:
        return (
          <span className="px-2.5 py-1 rounded-pill text-xs font-bold bg-[#F2F4F7] text-[#667085] border border-[#E4E7EC] inline-flex items-center gap-1.5 shadow-2xs">
            <MinusCircle size={13} className="text-[#667085]" />
            <span>{status}</span>
          </span>
        );
    }
  };

  // SVG Chart Dimensions for Ritter 1892
  const svgWidth = 680;
  const svgHeight = 220;
  const padLeft = 46;
  const padRight = 24;
  const padTop = 20;
  const padBottom = 34;

  const renderRitterChart = (chart: NonNullable<BenchmarkItem['chart']>) => {
    const xMin = chart.domain[0];
    const xMax = chart.domain[1];
    const hMax = 11.0;

    const toSvgX = (x: number) =>
      padLeft + ((x - xMin) / (xMax - xMin)) * (svgWidth - padLeft - padRight);
    const toSvgY = (h: number) =>
      svgHeight - padBottom - (h / hMax) * (svgHeight - padTop - padBottom);

    const theoryPath = chart.points
      .map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${toSvgX(p.x).toFixed(1)} ${toSvgY(p.h_theory).toFixed(1)}`)
      .join(' ');

    const simPath = chart.points
      .map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${toSvgX(p.x).toFixed(1)} ${toSvgY(p.h_sim).toFixed(1)}`)
      .join(' ');

    return (
      <div className="mt-4 p-4 rounded-xl bg-bg-subtle border border-border space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-2 pb-2 border-b border-border/60">
          <div className="flex items-center gap-3">
            <span className="font-semibold text-text">
              Centerline Water Depth Profile (t = {chart.t_seconds.toFixed(1)} s)
            </span>
            <span className="font-mono text-text-tertiary">Δx = 2.5 m</span>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="flex items-center gap-1.5">
              <span className="w-3.5 h-0.5 bg-[#0B1220] inline-block border-t border-[#0B1220]" />
              <span className="text-text-secondary">Analytical Ritter</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3.5 h-0.5 bg-[#0A66FF] inline-block" />
              <span className="text-[#0A66FF] font-medium">Delft3D FM Simulation</span>
            </div>
          </div>
        </div>

        <div className="relative w-full overflow-x-auto">
          <svg
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            className="w-full h-auto max-h-[220px] select-none"
            onMouseLeave={() => setHoveredPoint(null)}
          >
            {/* Grid Lines */}
            {[0, 2, 4, 6, 8, 10].map((hVal) => {
              const yPos = toSvgY(hVal);
              return (
                <g key={`y-${hVal}`}>
                  <line
                    x1={padLeft}
                    y1={yPos}
                    x2={svgWidth - padRight}
                    y2={yPos}
                    stroke="#E4E7EC"
                    strokeDasharray={hVal === 0 ? 'none' : '3 3'}
                  />
                  <text
                    x={padLeft - 8}
                    y={yPos + 4}
                    fontSize={10}
                    textAnchor="end"
                    fill="#667085"
                    fontFamily="monospace"
                  >
                    {hVal}m
                  </text>
                </g>
              );
            })}

            {[600, 800, 1000, 1200, 1400, 1600, 1800].map((xVal) => {
              const xPos = toSvgX(xVal);
              return (
                <g key={`x-${xVal}`}>
                  <line
                    x1={xPos}
                    y1={padTop}
                    x2={xPos}
                    y2={svgHeight - padBottom}
                    stroke="#F2F4F7"
                  />
                  <text
                    x={xPos}
                    y={svgHeight - padBottom + 16}
                    fontSize={10}
                    textAnchor="middle"
                    fill="#667085"
                    fontFamily="monospace"
                  >
                    {xVal}m
                  </text>
                </g>
              );
            })}

            {/* Gate Line Marker at x = 1000m */}
            <line
              x1={toSvgX(chart.dam_x)}
              y1={padTop}
              x2={toSvgX(chart.dam_x)}
              y2={svgHeight - padBottom}
              stroke="#B54708"
              strokeDasharray="4 4"
              strokeWidth={1.5}
            />
            <text
              x={toSvgX(chart.dam_x) + 4}
              y={padTop + 14}
              fontSize={10}
              fill="#B54708"
              fontFamily="monospace"
              fontWeight="bold"
            >
              Gate (x=1000m)
            </text>

            {/* Theoretical Wave Front Marker at x = 1594.3m */}
            <line
              x1={toSvgX(chart.x_front)}
              y1={padTop}
              x2={toSvgX(chart.x_front)}
              y2={svgHeight - padBottom}
              stroke="#667085"
              strokeDasharray="3 3"
              strokeWidth={1.2}
            />
            <text
              x={toSvgX(chart.x_front) - 4}
              y={padTop + 14}
              fontSize={10}
              fill="#667085"
              fontFamily="monospace"
              textAnchor="end"
            >
              Front (~1594m)
            </text>

            {/* Analytical Solution Curve */}
            <path
              d={theoryPath}
              fill="none"
              stroke="#0B1220"
              strokeWidth={2.2}
              strokeLinecap="round"
            />

            {/* Simulated Curve (Delft3D FM) */}
            <path
              d={simPath}
              fill="none"
              stroke="#0A66FF"
              strokeWidth={2.0}
              strokeLinecap="round"
            />

            {/* Interactive Points / Hover Targets */}
            {chart.points.map((p, idx) => {
              const cx = toSvgX(p.x);
              const cySim = toSvgY(p.h_sim);
              return (
                <g key={`pt-${idx}`}>
                  <circle
                    cx={cx}
                    cy={cySim}
                    r={hoveredPoint?.x === p.x ? 4.5 : 2}
                    fill={hoveredPoint?.x === p.x ? '#0A66FF' : 'rgba(10, 102, 255, 0.4)'}
                    stroke="#FFFFFF"
                    strokeWidth={1}
                  />
                  {/* Invisible wide capture rect */}
                  <rect
                    x={cx - 5}
                    y={padTop}
                    width={10}
                    height={svgHeight - padTop - padBottom}
                    fill="transparent"
                    className="cursor-crosshair"
                    onMouseEnter={() => setHoveredPoint(p)}
                  />
                </g>
              );
            })}

            {/* Hover Tooltip Overlay */}
            {hoveredPoint && (
              <g transform={`translate(${Math.min(toSvgX(hoveredPoint.x), svgWidth - 160)}, ${padTop + 10})`}>
                <rect
                  width={150}
                  height={56}
                  rx={6}
                  fill="#0B1220"
                  fillOpacity={0.92}
                  filter={`url(#${filterId})`}
                />
                <text x={8} y={16} fill="#FFFFFF" fontSize={10} fontFamily="monospace" fontWeight="bold">
                  x = {hoveredPoint.x.toFixed(1)} m
                </text>
                <text x={8} y={32} fill="#94A3B8" fontSize={9} fontFamily="monospace">
                  Analytical: <tspan fill="#FFFFFF">{hoveredPoint.h_theory.toFixed(2)} m</tspan>
                </text>
                <text x={8} y={46} fill="#60A5FA" fontSize={9} fontFamily="monospace">
                  Delft3D FM: <tspan fill="#FFFFFF">{hoveredPoint.h_sim.toFixed(2)} m</tspan>
                </text>
              </g>
            )}

            <defs>
              <filter id={filterId} x="0" y="0" width="200%" height="200%">
                <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.25" />
              </filter>
            </defs>
          </svg>
        </div>
      </div>
    );
  };

  return (
    <div className="p-6 sm:p-10 max-w-7xl mx-auto space-y-8">
      {/* 1. Header (Part A3 standard) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-4">
        <div>
          <div className="text-xs font-mono font-semibold tracking-wider text-text-tertiary uppercase">
            F19 · {isHi ? 'सत्यापन एवं मानक' : 'TRUST & VERIFICATION'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text mt-1">
            {isHi ? 'क्या ये हाइड्रोडायनामिक गणनाएं वैज्ञानिक रूप से प्रमाणित हैं?' : 'Are these hydrodynamic calculations scientifically proven?'}
          </h1>
          <p className="text-sm text-text-secondary mt-1 max-w-2xl">
            {isHi 
              ? 'विश्लेषणात्मक समीकरणों, उपग्रह प्रेक्षणों और सिमुलेशन मानकों के विरुद्ध कठोर वैज्ञानिक सत्यापन लेखाजोखा।' 
              : 'Empirical proof ledger: analytical exact solutions, satellite radar mappings, and benchmark convergence.'}
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="px-3 py-1 rounded-pill text-xs font-bold bg-[#ECFDF3] text-[#067647] border border-[#D1FADF] flex items-center gap-1.5 shadow-2xs">
            <CheckCircle2 size={14} />
            <span>REAL EVIDENCE ONLY · NO DEMO</span>
          </span>
          <button
            onClick={fetchBenchmarks}
            disabled={loading}
            className="p-1.5 rounded-lg border border-border hover:bg-bg-subtle text-text-secondary hover:text-text transition-colors disabled:opacity-50"
            title="Refresh Benchmarks"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* 2. Error State */}
      {error && (
        <div className="p-6 rounded-2xl bg-[#FEF3F2] border border-[#FECDCA] space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-bold text-[#B42318]">
              <AlertCircle size={18} />
              <span>Failed to load scientific validation benchmarks</span>
            </div>
            <button
              onClick={fetchBenchmarks}
              className="px-3 py-1 rounded-lg text-xs font-bold bg-[#B42318] text-white hover:bg-[#912018] transition-colors"
            >
              Try again
            </button>
          </div>
          <p className="text-xs text-[#912018]">
            Could not retrieve empirical benchmark records from the backend API.
          </p>
          <div>
            <button
              onClick={() => setShowTechnicalError(!showTechnicalError)}
              className="flex items-center gap-1 text-xs text-[#B42318] font-mono hover:underline"
            >
              <span>{showTechnicalError ? 'Hide technical details' : 'Show technical details'}</span>
              {showTechnicalError ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </button>
            {showTechnicalError && (
              <pre className="mt-2 p-3 rounded-lg bg-white/80 border border-[#FECDCA] text-xs font-mono text-text overflow-x-auto">
                {error}
              </pre>
            )}
          </div>
        </div>
      )}

      {/* 3. Loading Skeleton State */}
      {loading && !data && (
        <div className="space-y-4 animate-pulse">
          {[1, 2, 3, 4, 5].map((idx) => (
            <div key={idx} className="bg-white rounded-2xl border border-border p-6 sm:p-8 space-y-4">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-bg-muted" />
                  <div className="space-y-1.5">
                    <div className="w-48 h-4 bg-bg-muted rounded" />
                    <div className="w-64 h-3 bg-bg-muted rounded" />
                  </div>
                </div>
                <div className="w-28 h-6 bg-bg-muted rounded-pill" />
              </div>
              <div className="w-full h-12 bg-bg-muted rounded" />
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="h-14 bg-bg-muted rounded-xl" />
                <div className="h-14 bg-bg-muted rounded-xl" />
                <div className="h-14 bg-bg-muted rounded-xl" />
                <div className="h-14 bg-bg-muted rounded-xl" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 4. Benchmarks Cards List */}
      {data && (
        <div className="space-y-6">
          {data.benchmarks.map((benchmark) => {
            const isNotRun = benchmark.status === 'NOT RUN';

            return (
              <div
                key={benchmark.id}
                className={`rounded-2xl border border-border p-6 sm:p-8 space-y-4 shadow-xs transition-shadow ${
                  isNotRun ? 'bg-[#FAFAFA]' : 'bg-white'
                }`}
              >
                {/* Header row */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm select-none ${
                        benchmark.status_variant === 'pass'
                          ? 'bg-status-pass-soft text-status-pass'
                          : benchmark.status_variant === 'warning'
                          ? 'bg-[#FEF0C7] text-[#B54708]'
                          : 'bg-bg-subtle text-text-secondary'
                      }`}
                    >
                      {benchmark.badge}
                    </div>
                    <div>
                      <h2 className="text-base sm:text-lg font-bold text-text">
                        {benchmark.title}
                      </h2>
                      <div className="text-xs font-mono text-text-tertiary">
                        {benchmark.subtitle}
                      </div>
                    </div>
                  </div>

                  <div className="self-start sm:self-auto">
                    {getStatusBadge(benchmark.status)}
                  </div>
                </div>

                {/* Description */}
                <p className="text-xs sm:text-sm text-text-secondary leading-relaxed max-w-4xl">
                  {benchmark.description}
                </p>

                {/* Reason Callout for failed / pending / not run */}
                {benchmark.reason && (
                  <div className="p-3.5 rounded-xl bg-bg-subtle border border-border/80 flex items-start gap-2.5 text-xs text-text-secondary">
                    <AlertCircle size={15} className="text-[#B54708] mt-0.5 shrink-0" />
                    <div>
                      <strong className="text-text font-semibold">Reason recorded: </strong>
                      <span>{benchmark.reason}</span>
                    </div>
                  </div>
                )}

                {/* Interactive Chart (Ritter 1892) */}
                {benchmark.chart && renderRitterChart(benchmark.chart)}

                {/* Structured Metrics Grid */}
                {benchmark.metrics && benchmark.metrics.length > 0 && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-xl bg-bg-subtle border border-border text-xs font-mono">
                    {benchmark.metrics.map((metric, mIdx) => (
                      <div key={mIdx}>
                        <span className="text-text-tertiary uppercase text-[10px] tracking-wider block">
                          {metric.label}
                        </span>
                        <div className="font-bold text-text mt-0.5 tabular-nums text-xs sm:text-sm">
                          {metric.value}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Documentation Link & Citation */}
                <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-text-tertiary gap-2">
                  <div className="flex items-center gap-1.5 font-semibold text-brand">
                    <BookOpen size={13} />
                    <span>Documentation: </span>
                    <a
                      href={`docs/VALIDATION.md`}
                      className="hover:underline flex items-center gap-1"
                    >
                      <span>{benchmark.citation}</span>
                      <ExternalLink size={11} />
                    </a>
                  </div>
                  <div className="font-mono text-[11px] text-text-tertiary">
                    Traceable verbatim to docs/VALIDATION.md
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
