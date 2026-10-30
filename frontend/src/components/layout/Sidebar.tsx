import React, { useState } from 'react';
import { 
  Compass, 
  Activity, 
  PlusCircle, 
  Bookmark, 
  Boxes, 
  Map, 
  Users, 
  Navigation, 
  GitCompare, 
  Satellite, 
  Radio, 
  Mountain, 
  Layers, 
  BellRing, 
  Award, 
  Database, 
  FileCheck2, 
  ShieldAlert, 
  Cpu, 
  ChevronLeft, 
  ChevronRight,
  LucideIcon
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useDemoMode } from '../../context/DemoModeContext';
import { useAuth } from '../../context/AuthContext';
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
  minRole?: 'viewer' | 'analyst' | 'admin';
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
  const { user } = useAuth();
  const userRole = user?.role || 'analyst'; // default analyst if anonymous in dev
  const [collapsed, setCollapsed] = useState(false);

  // Strict groupings per Part B:
  // Overview: Home, Mission Control
  // Scenarios: New Scenario, Library, Batch
  // Results: Results Explorer, Impact, Evacuation, Engine Comparison, Satellite Validation
  // Monitoring: Run Monitor, Live Flood Monitor, Lake Watch, Cascade, Alerts
  // Trust: Validation & Benchmarks, Data Catalogue, Audit Log
  // Admin: Users & Roles, System Health
  const sections: NavSection[] = [
    {
      title: 'Overview',
      items: [
        { id: 'home', labelKey: 'nav.home', icon: Compass },
        { id: 'f01_mission_control', labelKey: 'nav.missionControl', icon: Activity },
      ],
    },
    {
      title: 'Scenarios',
      items: [
        { id: 'f02_new_scenario', labelKey: 'nav.newScenario', icon: PlusCircle, minRole: 'analyst' },
        { id: 'f14_library', labelKey: 'nav.scenarioLibrary', icon: Bookmark },
        { id: 'f15_batch', labelKey: 'nav.batchProcessing', icon: Boxes, minRole: 'analyst' },
      ],
    },
    {
      title: 'Results',
      items: [
        { id: 'f05_results_explorer', labelKey: 'nav.resultsExplorer', icon: Map },
        { id: 'f09_impact', labelKey: 'nav.impactAssessment', icon: Users },
        { id: 'f10_evacuation', labelKey: 'nav.evacuationRouter', icon: Navigation },
        { id: 'f06_engine_comparison', labelKey: 'nav.engineComparison', icon: GitCompare, isDemo: true },
        { id: 'f07_satellite_validation', labelKey: 'nav.satelliteValidation', icon: Satellite },
      ],
    },
    {
      title: 'Monitoring',
      items: [
        { id: 'f04_run_monitor', labelKey: 'nav.runMonitor', icon: Activity },
        { id: 'f08_live_flood', labelKey: 'nav.liveFloodMonitor', icon: Radio, isDemo: true },
        { id: 'f16_lake_watch', labelKey: 'nav.lakeWatch', icon: Mountain, isDemo: true },
        { id: 'f11_cascade', labelKey: 'nav.cascadeModeling', icon: Layers, isDemo: true },
        { id: 'f17_alerts', labelKey: 'nav.alertsDrawer', icon: BellRing },
      ],
    },
    {
      title: 'Trust',
      items: [
        { id: 'f19_benchmarks', labelKey: 'nav.benchmarks', icon: Award },
        { id: 'f18_catalogue', labelKey: 'nav.dataCatalogue', icon: Database },
        { id: 'f21_audit', labelKey: 'nav.auditLog', icon: FileCheck2 },
      ],
    },
    {
      title: 'Admin',
      items: [
        { id: 'f22_admin', labelKey: 'nav.adminSecurity', icon: ShieldAlert, minRole: 'admin' },
        { id: 'f20_health', labelKey: 'nav.systemHealth', icon: Cpu, minRole: 'admin' },
      ],
    },
  ];

  const handleItemClick = (id: FeatureId) => {
    onSelectFeature(id);
    if (onCloseMobile) {
      onCloseMobile();
    }
  };

  // Check RBAC role permission level
  const roleLevels = { viewer: 1, analyst: 2, admin: 3 };
  const currentLevel = roleLevels[userRole as keyof typeof roleLevels] || 2;

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
            // Filter: DEMO items hidden in Operational mode; RBAC: hide items role cannot do
            const visibleItems = section.items.filter((item) => {
              if (!isPresentationMode && item.isDemo) {
                return false;
              }
              if (item.minRole) {
                const requiredLevel = roleLevels[item.minRole];
                if (currentLevel < requiredLevel) {
                  return false;
                }
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
                      className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-colors text-left relative group ${
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

                      {/* Small purple dot on DEMO items in Presentation mode (§B) */}
                      {!collapsed && item.isDemo && isPresentationMode && (
                        <span
                          className="w-2 h-2 rounded-full bg-[#6941C6] shrink-0"
                          title="DEMO item (fictional / illustrative)"
                        />
                      )}

                      {collapsed && (
                        <div className="absolute left-full ml-2 px-2.5 py-1 bg-text text-white text-xs rounded-md shadow-md opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50 flex items-center gap-1.5">
                          <span>{t(item.labelKey)}</span>
                          {item.isDemo && <span className="w-1.5 h-1.5 rounded-full bg-[#D9D6FE]" />}
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
            className="w-full flex items-center justify-center p-2 text-text-tertiary hover:text-text hover:bg-bg-muted rounded-xl transition-colors"
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
