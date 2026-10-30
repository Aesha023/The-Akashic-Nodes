import React, { useState } from 'react';
import { Sparkles, ArrowLeft } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { TopBar } from './TopBar';
import { Sidebar } from './Sidebar';
import { CommandPalette } from '../common/CommandPalette';
import { HypotheticalBanner } from '../common/HypotheticalBanner';
import { DemoBadge } from '../common/DemoBadge';
import { LandingPage } from '../landing/LandingPage';
import { SignInPage } from '../auth/SignInPage';
import { useDemoMode } from '../../context/DemoModeContext';
import { FeatureId } from '../../types';

export const AppShell: React.FC = () => {
  const { t } = useTranslation();
  const { isPresentationMode } = useDemoMode();
  const [activeFeature, setActiveFeature] = useState<FeatureId>(() => {
    const hash = window.location.hash.replace('#', '') as FeatureId;
    if (hash && (hash === 'signin' || hash === 'landing' || hash.startsWith('f'))) {
      return hash;
    }
    return 'landing';
  });
  const [isCommandOpen, setIsCommandOpen] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  React.useEffect(() => {
    const onHashChange = () => {
      const hash = window.location.hash.replace('#', '') as FeatureId;
      if (hash && (hash === 'signin' || hash === 'landing' || hash.startsWith('f'))) {
        setActiveFeature(hash);
      }
    };
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  const handleNavigate = (feature: FeatureId) => {
    setActiveFeature(feature);
    window.location.hash = feature;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const renderContent = () => {
    if (activeFeature === 'landing') {
      return <LandingPage onNavigate={handleNavigate} />;
    }

    if (activeFeature === 'signin') {
      return <SignInPage onSuccess={handleNavigate} />;
    }

    // Generic feature placeholder panel with design system polish for initial C1 shell
    return (
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Scenario Banner for Ganga run */}
        <HypotheticalBanner />

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-border gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-bg-muted text-text-tertiary uppercase">
                {activeFeature}
              </span>
              {activeFeature.includes('cascade') ||
              activeFeature.includes('engine_comparison') ||
              activeFeature.includes('live_flood') ||
              activeFeature.includes('lake_watch') ? (
                <DemoBadge />
              ) : null}
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text">
              {t(`nav.${activeFeature}` as any, activeFeature.replace(/_/g, ' ').toUpperCase())}
            </h1>
          </div>

          <button
            onClick={() => handleNavigate('landing')}
            className="flex items-center gap-1.5 text-xs text-brand hover:underline font-medium"
          >
            <ArrowLeft size={14} />
            <span>Return to Landing Page</span>
          </button>
        </div>

        {/* Content card */}
        <div className="bg-surface rounded-xl p-8 border border-border shadow-sm text-center py-16 space-y-4">
          <div className="w-12 h-12 rounded-full bg-brand-soft text-brand flex items-center justify-center mx-auto">
            <Sparkles size={24} />
          </div>
          <h3 className="text-lg font-bold text-text">
            Feature Module: {activeFeature.toUpperCase()}
          </h3>
          <p className="text-sm text-text-secondary max-w-lg mx-auto">
            Design tokens, full-stack endpoints, and contracts aligned. Interactive views for this module are staged in Checkpoints C2, C3, and C4.
          </p>
          <div className="pt-2">
            <button
              onClick={() => handleNavigate('f05_results_explorer')}
              className="text-xs font-semibold text-brand hover:underline"
            >
              Inspect Real Ganga Results Explorer (C2 Target) →
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-bg text-text font-sans antialiased">
      {/* 1. Presentation Mode Global Notification Banner (§1.d) */}
      {isPresentationMode && (
        <aside
          role="status"
          aria-label="Presentation Mode Notification"
          className="w-full bg-[#F4F3FF] border-b border-[#D9D6FE] px-4 py-1.5 text-[#6941C6] text-xs font-medium flex items-center justify-center gap-2 select-none shadow-2xs"
        >
          <Sparkles size={13} className="shrink-0 stroke-[2.2]" aria-hidden="true" />
          <span>{t('topbar.presentationBanner')}</span>
        </aside>
      )}

      {/* 2. Top Bar (Glass panel, 64px) */}
      <TopBar
        onOpenSearch={() => setIsCommandOpen(true)}
        onNavigate={handleNavigate}
        activeFeature={activeFeature}
        onToggleMobileMenu={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
      />

      {/* 3. Main Body: Sidebar + Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar (248px / 72px) */}
        {activeFeature !== 'landing' && (
          <Sidebar
            activeFeature={activeFeature}
            onSelectFeature={handleNavigate}
            isMobileOpen={isMobileSidebarOpen}
            onCloseMobile={() => setIsMobileSidebarOpen(false)}
          />
        )}

        {/* Main Content Area */}
        <main
          id="main-content"
          tabIndex={-1}
          className="flex-1 overflow-y-auto bg-bg focus:outline-none"
        >
          {renderContent()}
        </main>
      </div>

      {/* Command Palette Overlay (⌘K) */}
      <CommandPalette
        isOpen={isCommandOpen}
        onClose={() => setIsCommandOpen(false)}
        onSelectFeature={handleNavigate}
      />
    </div>
  );
};
