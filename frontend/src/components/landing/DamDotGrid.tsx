import React, { useEffect, useRef } from 'react';
import { ExternalLink, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { CountUp } from '../common/CountUp';

export const DamDotGrid: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const totalDams = 6598;
  const eapDams = 735;
  const percentage = ((eapDams / totalDams) * 100).toFixed(1);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const cols = Math.floor(rect.width / 10);
    const dotRadius = 2.4;

    ctx.clearRect(0, 0, rect.width, rect.height);

    for (let i = 0; i < totalDams; i++) {
      const col = i % cols;
      const row = Math.floor(i / cols);
      const x = col * 10 + 5;
      const y = row * 10 + 5;

      ctx.beginPath();
      ctx.arc(x, y, dotRadius, 0, Math.PI * 2);

      if (i < eapDams) {
        // Highlighted dams with EAP (Brand Blue)
        ctx.fillStyle = '#0A66FF';
      } else {
        // Dams lacking Emergency Action Plan (Soft muted gray)
        ctx.fillStyle = '#E4E7EC';
      }
      ctx.fill();
    }
  }, []);

  return (
    <div className="w-full bg-white rounded-2xl p-6 sm:p-10 border border-border shadow-md">
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 pb-6 border-b border-border">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-pill bg-[#FEF3F2] border border-[#FECDCA] text-[#B42318] text-xs font-semibold uppercase tracking-wider mb-2">
            <ShieldAlert size={14} />
            <span>National Dam Safety Gap</span>
          </div>
          <h3 className="text-3xl sm:text-4xl font-bold tracking-tight text-text">
            <CountUp target={eapDams} /> of <CountUp target={totalDams} /> specified dams have an Emergency Action Plan
          </h3>
          <p className="text-base text-text-secondary mt-2 max-w-2xl leading-relaxed">
            Only <strong className="text-brand font-semibold">{percentage}%</strong> of India's completed and operational specified dams have a prepared or updated Emergency Action Plan (EAP). Over 5,800 dams operate without verified downstream evacuation mapping.
          </p>
        </div>

        {/* Legend */}
        <div className="flex sm:flex-col gap-3 text-xs shrink-0 bg-bg-subtle p-4 rounded-xl border border-border">
          <div className="flex items-center gap-2">
            <span className="w-3.5 h-3.5 rounded-full bg-brand shrink-0"></span>
            <span className="font-semibold text-text">735 with EAP ({percentage}%)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3.5 h-3.5 rounded-full bg-[#E4E7EC] border border-border-strong shrink-0"></span>
            <span className="text-text-secondary">5,863 Pending / No EAP (88.9%)</span>
          </div>
        </div>
      </div>

      {/* Visual Dot Matrix (6,598 dots) */}
      <div className="mt-8 pt-2">
        <div className="flex items-center justify-between text-xs text-text-tertiary mb-3 font-mono">
          <span>High-Density Specified Dam Registry (1 dot = 1 large dam)</span>
          <span className="text-brand font-semibold">6,598 Total Specified Dams</span>
        </div>
        <div className="w-full h-44 sm:h-52 bg-bg-subtle rounded-xl p-3 border border-border/80 overflow-hidden">
          <canvas
            ref={canvasRef}
            className="w-full h-full block"
            style={{ width: '100%', height: '100%' }}
          />
        </div>
      </div>

      {/* Verified Government Source Citation (Requirement F5) */}
      <div className="mt-6 pt-4 border-t border-border flex flex-col sm:flex-row items-start sm:items-center justify-between text-xs gap-3">
        <div className="flex items-start gap-2 text-text-secondary leading-snug">
          <CheckCircle2 size={16} className="text-status-pass shrink-0 mt-0.5" />
          <span>
            <strong>Official Source:</strong> Parliament of India, Rajya Sabha Session 265, written reply by Minister of Jal Shakti on August 3, 2026. Quoting NDSA DHARMA portal tracking data (status as of July 30, 2026).
          </span>
        </div>
        <a
          href="https://sansad.in/rs"
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 font-semibold text-brand hover:underline shrink-0 text-xs"
        >
          <span>sansad.in/rs Official Record</span>
          <ExternalLink size={13} />
        </a>
      </div>
    </div>
  );
};
