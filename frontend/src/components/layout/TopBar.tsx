import React from 'react';
import { 
  Search, 
  Sparkles, 
  Globe, 
  LogOut, 
  LogIn, 
  Waves,
  Menu
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
  const { t, i18n } = useTranslation();
  const { isPresentationMode, togglePresentationMode } = useDemoMode();
  const { user, isAuthenticated, logout } = useAuth();

  const toggleLanguage = () => {
    const nextLang = i18n.language === 'en' ? 'hi' : 'en';
    i18n.changeLanguage(nextLang);
  };

  return (
    <header className="sticky top-0 z-40 w-full h-16 glass-panel border-b border-border flex items-center justify-between px-4 sm:px-6 transition-all duration-200">
      {/* Left: Brand Logo & Mode Indicator */}
      <div className="flex items-center gap-2 sm:gap-4">
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
          <div className="flex flex-col">
            <span className="text-lg font-bold tracking-tight text-text flex items-center gap-1.5">
              <span>PravahX</span>
              <span className="text-[10px] font-mono font-medium px-1.5 py-0.2 bg-bg-muted text-text-tertiary rounded">
                v1.0
              </span>
            </span>
            <span className="text-[10px] font-medium text-text-tertiary -mt-1 hidden sm:block">
              {t('tagline')}
            </span>
          </div>
        </button>

        {activeFeature !== 'landing' && (
          <button
            onClick={() => onNavigate('landing')}
            className="text-xs text-brand hover:underline font-medium ml-2 hidden md:inline-block"
          >
            ← {t('nav.landing')}
          </button>
        )}
      </div>

      {/* Center: Command Search Bar (⌘K) */}
      <div className="flex-1 max-w-md mx-4 hidden md:block">
        <button
          onClick={onOpenSearch}
          className="w-full flex items-center justify-between px-3.5 py-2 text-xs text-text-tertiary bg-bg-subtle hover:bg-bg-muted border border-border rounded-lg transition-colors shadow-xs group"
        >
          <div className="flex items-center gap-2">
            <Search size={14} className="text-text-tertiary group-hover:text-text transition-colors" />
            <span>{t('topbar.searchPlaceholder')}</span>
          </div>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-mono text-text-tertiary bg-white border border-border rounded shadow-2xs">
            <span className="text-xs">⌘</span>K
          </kbd>
        </button>
      </div>

      {/* Right Controls: Demo Switch, Language Switcher, User & Auth */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Mobile search trigger */}
        <button
          onClick={onOpenSearch}
          className="p-2 text-text-secondary hover:text-text rounded-md md:hidden"
          title="Search"
        >
          <Search size={18} />
        </button>

        {/* Global Demo Content Mode Switch */}
        <div
          className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg border text-xs transition-colors ${
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
          <Sparkles
            size={14}
            className={isPresentationMode ? 'text-[#6941C6]' : 'text-text-tertiary'}
          />
          <span className="font-medium hidden sm:inline">
            {isPresentationMode ? t('topbar.presentationMode') : t('topbar.operationalMode')}
          </span>

          {/* Toggle pill */}
          <button
            onClick={togglePresentationMode}
            type="button"
            role="switch"
            aria-checked={isPresentationMode}
            aria-label="Toggle Presentation Demo Mode"
            className={`relative inline-flex h-4 w-7 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand ${
              isPresentationMode ? 'bg-[#6941C6]' : 'bg-[#D0D5DD]'
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-3 w-3 transform rounded-full bg-white shadow-xs ring-0 transition duration-200 ease-in-out ${
                isPresentationMode ? 'translate-x-3' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Language Switcher (EN / हिन्दी) */}
        <button
          onClick={toggleLanguage}
          className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-text-secondary hover:text-text bg-bg-subtle hover:bg-bg-muted border border-border rounded-lg transition-colors"
          title="Switch Language / भाषा बदलें"
        >
          <Globe size={13} className="text-text-tertiary" />
          <span className="font-sans">{i18n.language === 'en' ? 'हिन्दी' : 'English'}</span>
        </button>

        {/* User Session Profile / Auth */}
        {isAuthenticated && user ? (
          <div className="flex items-center gap-2 pl-1">
            <button
              onClick={() => onNavigate('f22_admin')}
              className="flex items-center gap-2 p-1 hover:bg-bg-subtle rounded-lg transition-colors text-left"
              title={`Logged in as ${user.username} (${user.role})`}
            >
              <div className="w-7 h-7 rounded-full bg-brand-soft text-brand font-semibold text-xs flex items-center justify-center border border-brand/20">
                {user.username.charAt(0).toUpperCase()}
              </div>
              <div className="hidden lg:flex flex-col">
                <span className="text-xs font-semibold text-text leading-tight">
                  {user.username}
                </span>
                <span className="text-[10px] text-text-tertiary uppercase leading-none">
                  {user.role}
                </span>
              </div>
            </button>
            <button
              onClick={logout}
              className="p-1.5 text-text-tertiary hover:text-status-fail hover:bg-[#FEF3F2] rounded-md transition-colors"
              title={t('topbar.signOut')}
            >
              <LogOut size={16} />
            </button>
          </div>
        ) : (
          <button
            onClick={() => onNavigate('signin')}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-brand hover:bg-brand-hover rounded-lg shadow-xs transition-colors"
          >
            <LogIn size={13} />
            <span>{t('topbar.signIn')}</span>
          </button>
        )}
      </div>
    </header>
  );
};
