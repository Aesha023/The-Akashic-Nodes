import React, { useState } from 'react';
import { 
  Search, 
  Sparkles, 
  Globe, 
  LogOut, 
  LogIn, 
  Waves,
  Menu,
  Bell,
  ChevronRight,
  ShieldCheck,
  Key,
  User as UserIcon,
  X
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useDemoMode } from '../../context/DemoModeContext';
import { useAuth } from '../../context/AuthContext';
import { FeatureId } from '../../types';

interface TopBarProps {
  onOpenSearch: () => void;
  onNavigate: (feature: FeatureId) => void;
  activeFeature: FeatureId;
  onToggleMobileMenu?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ 
  onOpenSearch, 
  onNavigate,
  activeFeature,
  onToggleMobileMenu
}) => {
  const { i18n } = useTranslation();
  const { isPresentationMode, togglePresentationMode } = useDemoMode();
  const { user, isAuthenticated, logout } = useAuth();

  const [isAlertsDrawerOpen, setIsAlertsDrawerOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  const toggleLanguage = () => {
    const nextLang = i18n.language === 'en' ? 'hi' : 'en';
    i18n.changeLanguage(nextLang);
  };

  // Derive breadcrumbs based on active feature
  const getBreadcrumbs = () => {
    if (activeFeature === 'landing') return null;
    if (activeFeature === 'home') return [{ label: 'Console', id: 'home' as FeatureId }];

    const map: Record<string, { group: string; name: string }> = {
      f01_mission_control: { group: 'Overview', name: 'Mission Control' },
      f02_new_scenario: { group: 'Scenarios', name: 'New Scenario' },
      f14_library: { group: 'Scenarios', name: 'Scenario Library' },
      f15_batch: { group: 'Scenarios', name: 'Batch Processing' },
      f05_results_explorer: { group: 'Results', name: 'Results Explorer' },
      f09_impact: { group: 'Results', name: 'Impact Assessment' },
      f10_evacuation: { group: 'Results', name: 'Evacuation Router' },
      f06_engine_comparison: { group: 'Results', name: 'Engine Comparison' },
      f07_satellite_validation: { group: 'Results', name: 'Satellite Validation' },
      f04_run_monitor: { group: 'Monitoring', name: 'Run Monitor' },
      f08_live_flood: { group: 'Monitoring', name: 'Live Flood Monitor' },
      f16_lake_watch: { group: 'Monitoring', name: 'Lake Watch (GLOF)' },
      f11_cascade: { group: 'Monitoring', name: 'Cascade Modeling' },
      f17_alerts: { group: 'Monitoring', name: 'Alert Rules' },
      f19_benchmarks: { group: 'Trust', name: 'Validation & Benchmarks' },
      f18_catalogue: { group: 'Trust', name: 'Data Catalogue' },
      f21_audit: { group: 'Trust', name: 'Audit Log' },
      f22_admin: { group: 'Admin', name: 'Users & Roles' },
      f20_health: { group: 'Admin', name: 'System Health' },
    };

    const item = map[activeFeature];
    if (!item) return null;
    return [
      { label: item.group, id: null },
      { label: item.name, id: activeFeature },
    ];
  };

  const breadcrumbs = getBreadcrumbs();

  return (
    <header className="sticky top-0 z-40 w-full h-16 bg-white/80 backdrop-blur-md border-b border-border flex items-center justify-between px-4 sm:px-6 select-none">
      {/* Left: Brand Logo & Breadcrumbs (§B) */}
      <div className="flex items-center gap-3">
        {activeFeature !== 'landing' && onToggleMobileMenu && (
          <button
            onClick={onToggleMobileMenu}
            className="p-1.5 text-text-secondary hover:text-text rounded-md md:hidden"
            title="Toggle Menu"
          >
            <Menu size={20} />
          </button>
        )}

        <button
          onClick={() => onNavigate('landing')}
          className="flex items-center gap-2.5 text-left group focus-visible:ring-2 focus-visible:ring-brand rounded-md p-1"
          title="Return to PravahX Overview"
        >
          <div className="w-8 h-8 rounded-lg bg-brand flex items-center justify-center text-white shadow-sm group-hover:bg-brand-hover transition-colors">
            <Waves size={18} className="stroke-[2.5]" />
          </div>
          <span className="text-lg font-bold tracking-tight text-text">PravahX</span>
        </button>

        {/* Breadcrumbs (§B, §A4) */}
        {breadcrumbs && (
          <nav aria-label="Breadcrumb" className="hidden lg:flex items-center gap-1.5 text-xs text-text-tertiary ml-2 pl-3 border-l border-border">
            <button
              onClick={() => onNavigate('home')}
              className="hover:text-text transition-colors"
            >
              Home
            </button>
            {breadcrumbs.map((bc, idx) => (
              <React.Fragment key={idx}>
                <ChevronRight size={12} className="text-text-tertiary" />
                <span className={idx === breadcrumbs.length - 1 ? 'font-semibold text-text' : ''}>
                  {bc.label}
                </span>
              </React.Fragment>
            ))}
          </nav>
        )}
      </div>

      {/* Center: Command Search Bar (⌘K) (§B) */}
      <div className="flex-1 max-w-md mx-4 hidden md:block">
        <button
          id="command-palette-trigger"
          onClick={onOpenSearch}
          className="w-full flex items-center justify-between px-3.5 py-1.5 text-xs text-text-tertiary bg-bg-subtle hover:bg-bg-muted border border-border rounded-xl transition-colors shadow-2xs group"
        >
          <div className="flex items-center gap-2">
            <Search size={14} className="text-text-tertiary group-hover:text-text transition-colors" />
            <span>Search scenarios, runs, datasets, actions (⌘K)...</span>
          </div>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-mono text-text-tertiary bg-white border border-border rounded shadow-2xs">
            <span className="text-xs">⌘</span>K
          </kbd>
        </button>
      </div>

      {/* Right Controls: Demo Switch, Language Switcher, Alerts Bell, User Menu (§B) */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Global Demo Content Mode Switch (persisted per user) (§B) */}
        <div
          className={`flex items-center gap-2 px-2.5 py-1 rounded-xl border text-xs transition-colors ${
            isPresentationMode
              ? 'bg-[#F4F3FF] border-[#D9D6FE] text-[#6941C6]'
              : 'bg-bg-subtle border-border text-text-secondary'
          }`}
          title={
            isPresentationMode
              ? 'Presentation Mode: Shows all 20+ modules including full product vision demo widgets'
              : 'Operational Mode: Strictly real endpoints and verified runs'
          }
        >
          <Sparkles size={13} className={isPresentationMode ? 'text-[#6941C6]' : 'text-text-tertiary'} />
          <span className="font-semibold text-[11px] hidden sm:inline">
            {isPresentationMode ? 'Presentation' : 'Operational'}
          </span>

          {/* Toggle switch */}
          <button
            id="demo-mode-toggle"
            onClick={togglePresentationMode}
            type="button"
            role="switch"
            aria-checked={isPresentationMode}
            className={`relative inline-flex h-4 w-7 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand ${
              isPresentationMode ? 'bg-[#6941C6]' : 'bg-[#D0D5DD]'
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-3 w-3 transform rounded-full bg-white shadow-2xs ring-0 transition duration-200 ease-in-out ${
                isPresentationMode ? 'translate-x-3' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Language Switcher (EN / हिन्दी) (§B, §A4) */}
        <button
          id="lang-toggle-btn"
          onClick={toggleLanguage}
          className="flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-text-secondary hover:text-text bg-bg-subtle hover:bg-bg-muted border border-border rounded-xl transition-colors"
          title="Switch Language / भाषा बदलें"
        >
          <Globe size={13} className="text-text-tertiary" />
          <span>{i18n.language === 'en' ? 'हिन्दी' : 'English'}</span>
        </button>

        {/* Alerts Bell (Drawer trigger) (§B) */}
        <button
          id="alerts-bell-btn"
          onClick={() => setIsAlertsDrawerOpen(true)}
          className="relative p-1.5 text-text-secondary hover:text-text hover:bg-bg-subtle rounded-xl border border-transparent hover:border-border transition-colors"
          title="View Alerts Drawer"
        >
          <Bell size={18} />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-status-fail" />
        </button>

        {/* User Menu / Profile Dropdown (§B) */}
        <div className="relative">
          {isAuthenticated && user ? (
            <button
              id="user-menu-btn"
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center gap-2 p-1 hover:bg-bg-subtle rounded-xl border border-transparent hover:border-border transition-colors text-left"
            >
              <div className="w-7 h-7 rounded-full bg-brand-soft text-brand font-bold text-xs flex items-center justify-center border border-brand/20">
                {user.username.charAt(0).toUpperCase()}
              </div>
              <div className="hidden lg:flex flex-col">
                <span className="text-xs font-bold text-text leading-tight">{user.username}</span>
                <span className="text-[10px] text-text-tertiary uppercase leading-none">{user.role}</span>
              </div>
            </button>
          ) : (
            <button
              onClick={() => onNavigate('signin')}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-white bg-brand hover:bg-brand-hover rounded-xl shadow-xs transition-colors"
            >
              <LogIn size={13} />
              <span>Sign In</span>
            </button>
          )}

          {/* User Menu Dropdown */}
          {isUserMenuOpen && user && (
            <div 
              id="user-profile-menu"
              className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl border border-border p-2 z-50 animate-in fade-in zoom-in-95 duration-150 space-y-1 text-xs"
            >
              <div className="px-3 py-2 border-b border-border">
                <p className="font-bold text-text">{user.username}</p>
                <p className="text-[11px] text-text-tertiary">{user.email || 'user@pravahx.gov.in'}</p>
                <div className="mt-1 flex items-center gap-1.5">
                  <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-bg-muted text-text-secondary uppercase">
                    Role: {user.role}
                  </span>
                </div>
              </div>

              <button
                onClick={() => {
                  setIsUserMenuOpen(false);
                  onNavigate('f22_admin');
                }}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-left hover:bg-bg-subtle text-text transition-colors"
              >
                <UserIcon size={14} className="text-text-tertiary" />
                <span>Officer Profile</span>
              </button>

              <div className="flex items-center justify-between px-3 py-2 text-text-secondary">
                <div className="flex items-center gap-2">
                  <ShieldCheck size={14} className="text-status-pass" />
                  <span>MFA Enforced</span>
                </div>
                <span className="text-[10px] font-bold text-status-pass">ACTIVE</span>
              </div>

              <button
                onClick={() => {
                  setIsUserMenuOpen(false);
                  onNavigate('f22_admin');
                }}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-left hover:bg-bg-subtle text-text transition-colors"
              >
                <Key size={14} className="text-text-tertiary" />
                <span>API Keys</span>
              </button>

              <div className="pt-1 border-t border-border">
                <button
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    logout();
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-left text-status-fail hover:bg-[#FEF3F2] font-semibold transition-colors"
                >
                  <LogOut size={14} />
                  <span>Sign out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Alerts Bell Slide-out Drawer (§B) */}
      {isAlertsDrawerOpen && (
        <div className="fixed inset-0 z-50 bg-[#0B1220]/40 backdrop-blur-xs flex justify-end animate-in fade-in duration-200">
          <div className="w-full max-w-sm bg-white h-full shadow-2xl border-l border-border flex flex-col animate-in slide-in-from-right duration-200">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bell size={18} className="text-brand" />
                <h3 className="font-bold text-text text-sm">System Alerts & Notifications</h3>
              </div>
              <button
                onClick={() => setIsAlertsDrawerOpen(false)}
                className="p-1 text-text-tertiary hover:text-text rounded-md"
              >
                <X size={18} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3 text-xs">
              <div className="p-3 rounded-2xl bg-[#FEF3F2] border border-[#FECDCA] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#B42318]">Breach Hydrograph Inflow</span>
                  <span className="text-[10px] text-text-tertiary font-mono">10m ago</span>
                </div>
                <p className="text-text-secondary leading-tight">
                  Tier-0 simulation run tier0_ganga_accepted exceeded 5,000 m³/s threshold.
                </p>
              </div>

              <div className="p-3 rounded-2xl bg-[#FFFAEB] border border-[#FEDF89] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#B54708]">Road Network Severance</span>
                  <span className="text-[10px] text-text-tertiary font-mono">2h ago</span>
                </div>
                <p className="text-text-secondary leading-tight">
                  17.34 km of roadway inundated across Rishikesh corridor.
                </p>
              </div>

              <div className="p-3 rounded-2xl bg-[#ECFDF3] border border-[#D1FADF] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#067647]">Audit Chain Verification</span>
                  <span className="text-[10px] text-text-tertiary font-mono">5h ago</span>
                </div>
                <p className="text-text-secondary leading-tight">
                  SHA-256 state ledger validated across 1,024 blocks.
                </p>
              </div>
            </div>

            <div className="p-4 border-t border-border">
              <button
                onClick={() => {
                  setIsAlertsDrawerOpen(false);
                  onNavigate('f17_alerts');
                }}
                className="w-full py-2 px-3 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-colors"
              >
                Open Full Alerts Engine →
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
