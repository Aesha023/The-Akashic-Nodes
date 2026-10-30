import React from 'react';
import { Sparkles } from 'lucide-react';

interface DemoBadgeProps {
  className?: string;
  size?: 'sm' | 'md';
}

export const DemoBadge: React.FC<DemoBadgeProps> = ({ className = '', size = 'md' }) => {
  const sizeClasses = size === 'sm' 
    ? 'text-[11px] px-2 py-0.5 gap-1' 
    : 'text-[12px] px-2.5 py-1 gap-1.5';

  return (
    <span
      className={`inline-flex items-center font-medium rounded-pill border bg-[#F4F3FF] text-[#6941C6] border-[#D9D6FE] font-sans tracking-wide uppercase shadow-sm ${sizeClasses} ${className}`}
      title="This component renders illustrative demonstration data"
    >
      <Sparkles size={size === 'sm' ? 12 : 14} className="shrink-0 stroke-[2.2]" />
      <span>DEMO · illustrative data</span>
    </span>
  );
};
