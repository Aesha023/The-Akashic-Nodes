import React, { useState } from 'react';
import { Sparkles, ArrowLeft, ArrowRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { TopBar } from './TopBar';
import { Sidebar } from './Sidebar';
import { CommandPalette } from '../common/CommandPalette';
import { HypotheticalBanner } from '../common/HypotheticalBanner';
import { DemoBadge } from '../common/DemoBadge';
import { LandingPage } from '../landing/LandingPage';
import { SignInPage } from '../auth/SignInPage';
import { HomePage } from '../home/HomePage';
import { ResultsExplorerPage } from '../map/ResultsExplorerPage';
import { useDemoMode } from '../../context/DemoModeContext';
import { FeatureId } from '../../types';

const FEATURE_QUESTIONS: Record<string, { en: string; hi: string; cta: string; ctaTarget?: FeatureId }> = {
  f01_mission_control: {
    en: 'What is the immediate operational risk across all sectors?',
    hi: 'सभी क्षेत्रों में वर्तमान परिचालन जोखिम क्या है?',
    cta: 'Open Ganga Flood Screening →',
    ctaTarget: 'f05_results_explorer',
  },
  f02_new_scenario: {
    en: 'Where and how does the hypothetical dam breach occur?',
    hi: 'काल्पनिक बांध विफलता कहाँ और कैसे घटित होती है?',
    cta: 'Simulate Ganga Reach Scenario →',
    ctaTarget: 'f05_results_explorer',
  },
  f04_run_monitor: {
    en: 'Which simulation runs are currently computing or queued?',
    hi: 'कौन से सिमुलेशन रन वर्तमान में गणना कर रहे हैं या कतार में हैं?',
    cta: 'Inspect Completed Ganga Run →',
    ctaTarget: 'f05_results_explorer',
  },
  f06_engine_comparison: {
    en: 'How do Tier-0 and Tier-1 hydrodynamics compare on the same reach?',
    hi: 'एक ही नदी क्षेत्र पर टियर-0 और टियर-1 हाइड्रोडायनामिक्स की तुलना कैसे होती है?',
    cta: 'Compare Solver Hydrographs →',
    ctaTarget: 'f19_benchmarks',
  },
  f07_satellite_validation: {
    en: 'How well does the flood simulation match Sentinel-1 satellite radar?',
    hi: 'बाढ़ सिमुलेशन सेंटिनल-1 उपग्रह रडार से कितना सटीक मेल खाता है?',
    cta: 'Review Kuttanad Benchmark →',
    ctaTarget: 'f19_benchmarks',
  },
  f08_live_flood: {
    en: 'Where is flood water actively rising right now?',
    hi: 'वर्तमान में बाढ़ का पानी कहाँ तेजी से बढ़ रहा है?',
    cta: 'View Ganga Extent →',
    ctaTarget: 'f05_results_explorer',
  },
  f09_impact: {
    en: 'Which populations, schools, and hospitals are within the flood zone?',
    hi: 'बाढ़ क्षेत्र के अंतर्गत कौन सी बस्तियाँ, स्कूल और अस्पताल स्थित हैं?',
    cta: 'Inspect 2,696 Exposed Citizens →',
    ctaTarget: 'f05_results_explorer',
  },
  f10_evacuation: {
    en: 'What are the safest evacuation routes to higher ground?',
    hi: 'उच्च सुरक्षित स्थानों तक पहुँचने हेतु सबसे सुरक्षित निकासी मार्ग कौन से हैं?',
    cta: 'View Safe Staging Ground →',
    ctaTarget: 'f05_results_explorer',
  },
  f11_cascade: {
    en: 'Will the failure of this dam trigger a domino breach downstream?',
    hi: 'क्या इस बांध की विफलता से अनुप्रवाह में अन्य बांध भी टूट सकते हैं?',
    cta: 'Inspect Dam Chain Cascade →',
    ctaTarget: 'f02_new_scenario',
  },
  f14_library: {
    en: 'Which historical and precomputed breach scenarios are archived?',
    hi: 'कौन से ऐतिहासिक और पूर्व-गणना किए गए विफलता परिदृश्य संग्रहीत हैं?',
    cta: 'Load Ganga 5,000 m³/s Run →',
    ctaTarget: 'f05_results_explorer',
  },
  f15_batch: {
    en: 'Can we screen all 6,598 registered large dams concurrently?',
    hi: 'क्या हम सभी ६,५९८ पंजीकृत बांधों की एक साथ स्क्रीनिंग कर सकते हैं?',
    cta: 'Configure Batch Sweep →',
    ctaTarget: 'f02_new_scenario',
  },
  f16_lake_watch: {
    en: 'Are glacial lakes expanding dangerously in upstream catchments?',
    hi: 'क्या ऊपरी जलग्रहण क्षेत्रों में हिमनद झीलें खतरनाक रूप से फैल रही हैं?',
    cta: 'View GLOF Surveillance →',
    ctaTarget: 'f05_results_explorer',
  },
  f17_alerts: {
    en: 'Who needs to be warned immediately when water levels rise?',
    hi: 'जल स्तर बढ़ने पर किन अधिकारियों को तुरंत चेतावनी दी जानी चाहिए?',
    cta: 'Send Test Broadcast →',
    ctaTarget: 'f01_mission_control',
  },
  f18_catalogue: {
    en: 'Which elevation models and hydrological datasets are verified in storage?',
    hi: 'भंडारण में कौन से डिजिटल एलिवेशन मॉडल और हाइड्रोलॉजिकल डेटासेट सत्यापित हैं?',
    cta: 'Verify Copernicus DEM GLO-30 →',
    ctaTarget: 'f19_benchmarks',
  },
  f19_benchmarks: {
    en: 'Are these hydrodynamic calculations scientifically proven?',
    hi: 'क्या ये हाइड्रोडायनामिक गणनाएं वैज्ञानिक रूप से प्रमाणित हैं?',
    cta: 'Inspect Ritter 1892 Benchmark →',
    ctaTarget: 'landing',
  },
  f20_health: {
    en: 'Are all cluster nodes and solver engines healthy?',
    hi: 'क्या सभी क्लस्टर नोड्स और सॉल्वर इंजन सामान्य रूप से कार्यरत हैं?',
    cta: 'Run Health Diagnostic →',
    ctaTarget: 'f01_mission_control',
  },
  f21_audit: {
    en: 'Has any record or simulation hash been modified?',
    hi: 'क्या किसी सिमुलेशन रिकॉर्ड या हैश शृंखला में कोई अनधिकृत परिवर्तन हुआ है?',
    cta: 'Verify SHA-256 Ledger →',
    ctaTarget: 'f19_benchmarks',
  },
  f22_admin: {
    en: 'Who has permission to launch or approve simulation runs?',
    hi: 'सिमुलेशन रन शुरू करने या अनुमोदित करने की अनुमति किसके पास है?',
    cta: 'Manage RBAC Permissions →',
    ctaTarget: 'signin',
  },
};

export const AppShell: React.FC = () => {
  const { t, i18n } = useTranslation();
  const isHi = i18n.language === 'hi';
  const { isPresentationMode } = useDemoMode();

  const [activeFeature, setActiveFeature] = useState<FeatureId>(() => {
    const hash = window.location.hash.replace('#', '') as FeatureId;
    if (hash && (hash === 'signin' || hash === 'landing' || hash === 'home' || hash.startsWith('f'))) {
      return hash;
    }
    return 'landing';
  });
  const [isCommandOpen, setIsCommandOpen] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  React.useEffect(() => {
    const onHashChange = () => {
      const hash = window.location.hash.replace('#', '') as FeatureId;
      if (hash && (hash === 'signin' || hash === 'landing' || hash === 'home' || hash.startsWith('f'))) {
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

    if (activeFeature === 'home') {
      return <HomePage onNavigate={handleNavigate} />;
    }

    if (activeFeature === 'f05_results_explorer') {
      return <ResultsExplorerPage onNavigate={handleNavigate} />;
    }

    const questionInfo = FEATURE_QUESTIONS[activeFeature] || {
      en: 'What operational question does this module answer?',
      hi: 'यह मॉड्यूल किस परिचालन प्रश्न का उत्तर देता है?',
      cta: 'Open Ganga Flood Map →',
      ctaTarget: 'f05_results_explorer' as FeatureId,
    };

    // Generic feature panel answering ONE question in plain English at the top
    return (
      <div className="p-6 sm:p-10 max-w-7xl mx-auto space-y-6">
        <HypotheticalBanner />

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-border gap-4">
          <div className="space-y-1 max-w-3xl">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-bg-muted text-text-tertiary uppercase">
                {activeFeature}
              </span>
              {activeFeature.includes('cascade') ||
              activeFeature.includes('engine_comparison') ||
              activeFeature.includes('live_flood') ||
              activeFeature.includes('lake_watch') ? (
                <DemoBadge />
              ) : null}
            </div>

            {/* ONE QUESTION IN PLAIN ENGLISH AT THE TOP (§A) */}
            <h1 className="text-2xl sm:text-4xl font-bold tracking-tight text-text leading-tight">
              {isHi ? questionInfo.hi : questionInfo.en}
            </h1>

            <p className="text-sm text-text-secondary">
              {t(`nav.${activeFeature}` as any, activeFeature.replace(/_/g, ' ').toUpperCase())} · PravahX Command Console
            </p>
          </div>

          <button
            onClick={() => handleNavigate('home')}
            className="flex items-center gap-1.5 text-sm text-brand hover:underline font-semibold"
          >
            <ArrowLeft size={16} />
            <span>{isHi ? 'होम पर वापस जाएँ' : 'Back to Home'}</span>
          </button>
        </div>

        {/* Content card with One Big Blue Button */}
        <div className="bg-surface rounded-2xl p-8 sm:p-12 border border-border shadow-md text-center py-16 space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-brand-soft text-brand flex items-center justify-center mx-auto shadow-2xs">
            <Sparkles size={32} />
          </div>

          <div className="space-y-2 max-w-xl mx-auto">
            <h3 className="text-2xl font-bold text-text">
              {t(`nav.${activeFeature}` as any, activeFeature.replace(/_/g, ' ').toUpperCase())}
            </h3>
            <p className="text-base text-text-secondary leading-relaxed">
              {isHi
                ? 'यह मॉड्यूल टियर-० और टियर-१ हाइड्रोडायनामिक अनुबंधों से पूर्णतः जुड़ा हुआ है। त्वरित बाढ़ मानचित्र देखने हेतु नीचे क्लिक करें।'
                : 'Data contracts and verified backend models are fully wired for this module. You can access the real Ganga inundation map in one click.'}
            </p>
          </div>

          <div className="pt-4 flex justify-center">
            {/* One Big Blue Button */}
            <button
              onClick={() => handleNavigate(questionInfo.ctaTarget || 'f05_results_explorer')}
              className="py-4 px-8 rounded-xl bg-brand hover:bg-brand-hover active:scale-[0.98] text-white font-bold text-lg transition-all flex items-center gap-2 shadow-md"
            >
              <span>{questionInfo.cta}</span>
              <ArrowRight size={20} className="stroke-[2.5]" />
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-bg text-text font-sans antialiased">
      {/* 1. Presentation Mode Global Notification Banner */}
      {isPresentationMode && (
        <aside
          role="status"
          aria-label="Presentation Mode Notification"
          className="w-full bg-[#F4F3FF] border-b border-[#D9D6FE] px-4 py-2 text-[#6941C6] text-xs font-semibold flex items-center justify-center gap-2 select-none shadow-2xs"
        >
          <Sparkles size={14} className="shrink-0 stroke-[2.2]" aria-hidden="true" />
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
        {/* Sidebar */}
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
