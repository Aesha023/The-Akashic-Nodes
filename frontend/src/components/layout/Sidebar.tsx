import React, { useState } from 'react';
import { 
  Compass, 
  PlusCircle, 
  Activity, 
  Map, 
  GitCompare, 
  Satellite, 
  Radio, 
  Users, 
  Navigation, 
  Layers, 
  Bookmark, 
  Boxes, 
  Mountain, 
  BellRing, 
  Database, 
  Award, 
  Cpu, 
  FileCheck2, 
  ShieldAlert, 
  ChevronLeft, 
  ChevronRight,
  LucideIcon
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useDemoMode } from '../../context/DemoModeContext';
import { FeatureId } from '../../types';

interface SidebarProps {
  activeFeature: FeatureId;
  onSelectFeature: (feature: FeatureId) => void;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

interface NavItem {
  id: FeatureId;
  labelKey: string;
  icon: LucideIcon;
  isDemo?: boolean;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  activeFeature, 
  onSelectFeature,
  isMobileOpen = false,
  onCloseMobile
}) => {
  const { t } = useTranslation();
  const { isPresentationMode } = useDemoMode();
  const [collapsed, setCollapsed] = useState(false);

  const sections: NavSection[] = [
    {
      title: 'Tactical Command',
      items: [
        { id: 'home', labelKey: 'nav.home', icon: Compass },
        { id: 'f01_mission_control', labelKey: 'nav.missionControl', icon: Activity },
        { id: 'f05_results_explorer', labelKey: 'nav.resultsExplorer', icon: Map },
        { id: 'f04_run_monitor', labelKey: 'nav.runMonitor', icon: Activity },
      ],
    },
    {
      title: 'Simulation & Modeling',
      items: [
        { id: 'f02_new_scenario', labelKey: 'nav.newScenario', icon: PlusCircle },
        { id: 'f06_engine_comparison', labelKey: 'nav.engineComparison', icon: GitCompare, isDemo: true },
        { id: 'f11_cascade', labelKey: 'nav.cascadeModeling', icon: Layers, isDemo: true },
        { id: 'f15_batch', labelKey: 'nav.batchProcessing', icon: Boxes },
      ],
    },
    {
      title: 'Disaster & Evacuation',
      items: [
        { id: 'f09_impact', labelKey: 'nav.impactAssessment', icon: Users },
        { id: 'f10_evacuation', labelKey: 'nav.evacuationRouter', icon: Navigation },
        { id: 'f07_satellite_validation', labelKey: 'nav.satelliteValidation', icon: Satellite },
        { id: 'f08_live_flood', labelKey: 'nav.liveFloodMonitor', icon: Radio, isDemo: true },
        { id: 'f16_lake_watch', labelKey: 'nav.lakeWatch', icon: Mountain, isDemo: true },
        { id: 'f17_alerts', labelKey: 'nav.alertsDrawer', icon: BellRing },
      ],
    },
    {
      title: 'Evidence & Infrastructure',
      items: [
        { id: 'f14_library', labelKey: 'nav.scenarioLibrary', icon: Bookmark },
        { id: 'f18_catalogue', labelKey: 'nav.dataCatalogue', icon: Database },
        { id: 'f19_benchmarks', labelKey: 'nav.benchmarks', icon: Award },
        { id: 'f20_health', labelKey: 'nav.systemHealth', icon: Cpu },
        { id: 'f21_audit', labelKey: 'nav.auditLog', icon: FileCheck2 },
        { id: 'f22_admin', labelKey: 'nav.adminSecurity', icon: ShieldAlert },
      ],
    },
  ];

  const handleItemClick = (id: FeatureId) => {
    onSelectFeature(id);
    if (onCloseMobile) {
      onCloseMobile();
    }
  };

  return (
    <>
      {/* Mobile Drawer Backdrop */}
      {isMobileOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 bg-[#0B1220]/40 backdrop-blur-xs z-40 md:hidden"
        />
      )}

      <aside
        className={`fixed md:relative inset-y-0 left-0 z-40 md:z-30 flex flex-col bg-bg-subtle border-r border-border transition-all duration-200 select-none ${
          isMobileOpen ? 'translate-x-0 w-[260px]' : '-translate-x-full md:translate-x-0'
        } ${collapsed ? 'md:w-[72px]' : 'md:w-[248px]'}`}
      >
        {/* Navigation list */}
        <div className="flex-1 overflow-y-auto py-3 px-2 space-y-4">
        {sections.map((section, secIdx) => {
          // If operational mode (isPresentationMode === false), filter out items that are pure demo if desired,
          // or mark them clearly. Per spec: in Operational mode demo widgets are hidden or disabled.
          const visibleItems = section.items.filter((item) => {
            if (!isPresentationMode && item.isDemo) {
              return false; // hide demo-only pages in Operational mode
            }
            return true;
          });

          if (visibleItems.length === 0) return null;

          return (
            <div key={secIdx} className="space-y-1">
              {!collapsed && (
                <p className="px-3 text-[11px] font-semibold text-text-tertiary uppercase tracking-wider mb-1">
                  {section.title}
                </p>
              )}
              {visibleItems.map((item) => {
                const Icon = item.icon;
                const isSelected = activeFeature === item.id;

                return (
                  <button
                    key={item.id}
                    onClick={() => handleItemClick(item.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-colors text-left relative group ${
                      isSelected
                        ? 'bg-brand-soft text-brand font-semibold shadow-2xs'
                        : 'text-text-secondary hover:bg-bg-muted hover:text-text'
                    }`}
                    title={collapsed ? t(item.labelKey) : undefined}
                  >
                    <Icon
                      size={18}
                      className={`shrink-0 ${
                        isSelected ? 'text-brand stroke-[2.2]' : 'text-text-tertiary group-hover:text-text'
                      }`}
                    />
                    {!collapsed && (
                      <span className="truncate flex-1">
                        {t(item.labelKey)}
                      </span>
                    )}

                    {!collapsed && item.isDemo && (
                      <span
                        className="text-[9px] font-semibold px-1.5 py-0.2 rounded-pill bg-[#F4F3FF] text-[#6941C6] border border-[#D9D6FE] uppercase shrink-0"
                        title="DEMO feature with synthetic fixtures"
                      >
                        Demo
                      </span>
                    )}

                    {collapsed && (
                      <div className="absolute left-full ml-2 px-2.5 py-1 bg-text text-white text-xs rounded-md shadow-md opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                        {t(item.labelKey)}
                        {item.isDemo && ' (DEMO)'}
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          );
        })}
      </div>

      {/* Collapse/Expand footer toggle */}
      <div className="p-2 border-t border-border flex items-center justify-between">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center p-2 text-text-tertiary hover:text-text hover:bg-bg-muted rounded-md transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={18} /> : (
            <div className="flex items-center gap-2 text-xs font-medium text-text-tertiary w-full justify-start px-2">
              <ChevronLeft size={16} />
              <span>Collapse sidebar</span>
            </div>
          )}
        </button>
      </div>
    </aside>
    </>
  );
};
