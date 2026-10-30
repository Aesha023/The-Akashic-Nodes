import React from 'react';
import { AlertTriangle, Info } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface HypotheticalBannerProps {
  className?: string;
  showDepthNotice?: boolean;
}

export const HypotheticalBanner: React.FC<HypotheticalBannerProps> = ({
  className = '',
  showDepthNotice = true,
}) => {
  const { t } = useTranslation();

  return (
    <aside
      role="note"
      aria-label="Scenario Disclaimer"
      className={`w-full bg-[#FFFAEB] border-y border-[#FEDF89] px-4 py-2.5 text-[#B54708] font-sans text-xs sm:text-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-2 shadow-xs ${className}`}
    >
      <div className="flex items-center gap-2">
        <AlertTriangle size={16} className="text-[#B54708] shrink-0 stroke-[2.2]" aria-hidden="true" />
        <span className="font-semibold tracking-tight">
          {t('banner.hypotheticalScenario')}
        </span>
      </div>
      {showDepthNotice && (
        <div className="flex items-center gap-1.5 text-xs text-[#7A2E0E] bg-[#FEF0C7] px-2.5 py-1 rounded-md border border-[#FEE4E2]">
          <Info size={13} className="shrink-0" aria-hidden="true" />
          <span>{t('banner.demWaterSurfaceNotice')}</span>
        </div>
      )}
    </aside>
  );
};
