import React, { useState } from 'react';
import { Info } from 'lucide-react';

export interface TooltipProps {
  term: string;
  explanation?: string;
  definition?: string;
  children?: React.ReactNode;
  className?: string;
}

export const Tooltip: React.FC<TooltipProps> = ({
  term,
  explanation,
  definition,
  children,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const text = explanation || definition || '';

  return (
    <span className={`relative inline-flex items-center gap-1 group ${className}`}>
      {children || <span className="font-medium text-text">{term}</span>}
      <button
        type="button"
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        onFocus={() => setIsOpen(true)}
        onBlur={() => setIsOpen(false)}
        aria-label={`Explanation for ${term}`}
        className="w-4 h-4 rounded-full bg-bg-muted hover:bg-brand-soft text-text-tertiary hover:text-brand flex items-center justify-center transition-colors focus-visible:ring-2 focus-visible:ring-brand shrink-0 cursor-help"
      >
        <Info size={11} className="stroke-[2.2]" />
      </button>

      {isOpen && (
        <div
          role="tooltip"
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-surface rounded-lg shadow-lg border border-border text-xs text-text z-50 pointer-events-none animate-in fade-in duration-150"
        >
          <p className="font-semibold text-brand text-[11px] uppercase tracking-wider mb-1">
            {term}
          </p>
          <p className="text-text-secondary leading-normal text-[12px]">
            {text}
          </p>
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-surface" />
        </div>
      )}
    </span>
  );
};
