import React from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  MinusCircle, 
  Clock, 
  HelpCircle, 
  FlaskConical, 
  Database,
  Sparkles
} from 'lucide-react';
import { StatusType } from '../../types';

interface BadgeProps {
  status: StatusType | string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  showIcon?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({ 
  status, 
  size = 'md', 
  className = '',
  showIcon = true 
}) => {
  const norm = status.toUpperCase().trim();

  let text = status;
  let bgClass = 'bg-[#F2F4F7] text-[#475467] border-[#EAECF0]';
  let IconComponent = MinusCircle;

  if (norm.includes('PASSED')) {
    bgClass = 'bg-[#ECFDF3] text-[#067647] border-[#D1FADF]';
    IconComponent = CheckCircle2;
  } else if (norm.includes('FAILED')) {
    bgClass = 'bg-[#FEF3F2] text-[#B42318] border-[#FECDCA]';
    IconComponent = XCircle;
  } else if (norm.includes('NOT RUN')) {
    bgClass = 'bg-[#F2F4F7] text-[#475467] border-[#EAECF0]';
    IconComponent = MinusCircle;
  } else if (norm.includes('PENDING')) {
    bgClass = 'bg-[#FFFAEB] text-[#B54708] border-[#FEDF89]';
    IconComponent = Clock;
  } else if (norm.includes('UNVERIFIED')) {
    bgClass = 'bg-[#F4F3FF] text-[#6941C6] border-[#D9D6FE]';
    IconComponent = HelpCircle;
  } else if (norm.includes('TESTED')) {
    bgClass = 'bg-[#EFF8FF] text-[#175CD3] border-[#B2DDFF]';
    IconComponent = FlaskConical;
  } else if (norm.includes('PRECOMPUTED')) {
    bgClass = 'bg-[#FFFAEB] text-[#B54708] border-[#FEDF89]';
    IconComponent = Database;
  } else if (norm.includes('NOT YET VALIDATED')) {
    bgClass = 'bg-[#FFFAEB] text-[#B54708] border-[#FEDF89]';
    IconComponent = Clock;
    text = 'RUN · not yet validated';
  } else if (norm.includes('DEMO')) {
    bgClass = 'bg-[#F4F3FF] text-[#6941C6] border-[#D9D6FE]';
    IconComponent = Sparkles;
    text = 'DEMO · illustrative data';
  }

  const sizeClasses = {
    sm: 'text-[11px] px-2 py-0.5 gap-1',
    md: 'text-[12px] px-2.5 py-1 gap-1.5',
    lg: 'text-[13px] px-3 py-1.5 gap-2',
  }[size];

  const iconSize = {
    sm: 12,
    md: 14,
    lg: 16,
  }[size];

  return (
    <span
      className={`inline-flex items-center font-medium rounded-pill border tracking-wide uppercase font-sans ${bgClass} ${sizeClasses} ${className}`}
    >
      {showIcon && <IconComponent size={iconSize} className="shrink-0 stroke-[2.2]" />}
      <span>{text}</span>
    </span>
  );
};
