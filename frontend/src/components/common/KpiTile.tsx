import React from 'react';

interface KpiTileProps {
  label: string;
  value: string | number;
  unit?: string;
  source: string;
  subtext?: string;
  className?: string;
  trend?: {
    text: string;
    positive?: boolean;
  };
}

export const KpiTile: React.FC<KpiTileProps> = ({
  label,
  value,
  unit,
  source,
  subtext,
  className = '',
  trend,
}) => {
  return (
    <div
      className={`bg-surface rounded-lg p-5 border border-border shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow ${className}`}
    >
      <div>
        <p className="text-[12px] font-semibold text-text-tertiary uppercase tracking-wider mb-1">
          {label}
        </p>
        <div className="flex items-baseline gap-1.5 my-1">
          <span className="text-3xl sm:text-4xl font-semibold text-text tabular-nums tracking-tight">
            {value}
          </span>
          {unit && (
            <span className="text-sm font-medium text-text-secondary">
              {unit}
            </span>
          )}
        </div>
        {subtext && (
          <p className="text-xs text-text-secondary mt-1">{subtext}</p>
        )}
        {trend && (
          <div className="mt-2 flex items-center gap-1 text-xs">
            <span
              className={`font-medium ${
                trend.positive ? 'text-status-pass' : 'text-status-fail'
              }`}
            >
              {trend.text}
            </span>
          </div>
        )}
      </div>

      {/* Mandatory source attribution line */}
      <div className="mt-4 pt-2.5 border-t border-border/60">
        <p className="text-[11px] text-text-tertiary flex items-center gap-1 font-mono">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-brand/50"></span>
          <span>{source}</span>
        </p>
      </div>
    </div>
  );
};
