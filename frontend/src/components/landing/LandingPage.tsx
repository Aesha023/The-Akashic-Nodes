import React, { useEffect } from 'react';
import { 
  ArrowRight, 
  ShieldCheck, 
  Layers, 
  Activity, 
  Award, 
  ChevronRight, 
  ExternalLink,
  MapPin,
  Info
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import Lenis from 'lenis';
import { Badge } from '../common/Badge';
import { CountUp } from '../common/CountUp';
import { FlowingWaterBg } from './FlowingWaterBg';
import { ScrollStoryMap } from './ScrollStoryMap';
import { DamDotGrid } from './DamDotGrid';
import { RitterAnimatedPlot } from './RitterAnimatedPlot';
import { FeatureId } from '../../types';

const GangaMap = React.lazy(() => import('../map/GangaMap').then(m => ({ default: m.GangaMap })));

interface LandingPageProps {
  onNavigate: (feature: FeatureId) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  const { t, i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  // Initialize Lenis smooth scroll respecting prefers-reduced-motion (§B, §D)
  useEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const lenis = new Lenis({
      duration: 1.1,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      gestureOrientation: 'vertical',
      smoothWheel: true,
    });

    let rafId: number;
    function raf(time: number) {
      lenis.raf(time);
      rafId = requestAnimationFrame(raf);
    }
    rafId = requestAnimationFrame(raf);

    return () => {
      cancelAnimationFrame(rafId);
      lenis.destroy();
    };
  }, []);

  return (
    <div className="w-full min-h-screen bg-bg text-text font-sans overflow-x-hidden selection:bg-brand-soft selection:text-brand">
      
      {/* 1. Hero Section with Subtle Animated Flowing-Contour Background */}
      <section className="relative pt-12 pb-20 md:pt-24 md:pb-32 px-4 sm:px-6 lg:px-8 max-w-[1240px] mx-auto overflow-hidden">
        {/* Animated Water Contours Background */}
        <FlowingWaterBg />

        <div className="relative z-10 text-center max-w-4xl mx-auto space-y-6">
          {/* Scientific honesty badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-pill bg-white/90 backdrop-blur-md border border-border shadow-xs text-xs text-text-secondary font-medium">
            <span className="w-2 h-2 rounded-full bg-brand animate-pulse"></span>
            <span>SIH 2026 · PS 26161 · Hydrodynamic Disaster Intelligence</span>
          </div>

          {/* Plain English question answering landing requirement */}
          <div className="text-xs font-mono font-bold uppercase tracking-wider text-brand">
            {isHi ? 'बाढ़ सिमुलेशन और जोखिम मूल्यांकन' : 'Multi-Tier Dam-Break Inundation Screening'}
          </div>
          <h1 className="text-4xl sm:text-6xl lg:text-[72px] font-bold tracking-tight text-text leading-[1.05]">
            {isHi 
              ? 'यदि कोई बांध टूटता है तो बाढ़ का पानी कहाँ जाएगा?' 
              : 'Where will flood water go if a dam breaches?'}
          </h1>

          {/* Subhead with 16px min body */}
          <p className="text-lg sm:text-xl text-text-secondary max-w-2xl mx-auto leading-relaxed">
            {isHi
              ? 'मल्टी-टियर जलप्लावन मॉडलिंग, तीव्र स्थैतिक स्क्रीनिंग, और भौतिकी-आधारित सिमुलेशन। पूर्ण वैज्ञानिक प्रामाणिकता और पारदर्शी सत्यापन के साथ निर्मित।'
              : 'Multi-tier dam-break inundation screening, rapid static terrain analysis, and hydrodynamic routing. Built with scientific honesty and verified data provenance.'}
          </p>

          {/* Two primary CTAs */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-3">
            <button
              onClick={() => onNavigate('signin')}
              className="py-4 px-8 rounded-xl bg-brand hover:bg-brand-hover active:scale-[0.98] text-white font-bold text-lg transition-all flex items-center gap-2.5 shadow-md group"
            >
              <span>{isHi ? 'मिशन नियंत्रण खोलें' : 'Open Mission Control'}</span>
              <ArrowRight size={20} className="stroke-[2.5] group-hover:translate-x-0.5 transition-transform" />
            </button>
            <button
              onClick={() => onNavigate('f19_benchmarks')}
              className="py-4 px-8 rounded-xl bg-surface hover:bg-bg-subtle active:scale-[0.98] text-text font-bold text-lg border border-border-strong transition-all flex items-center gap-2.5 shadow-xs"
            >
              <Award size={20} className="text-brand stroke-[2.2]" />
              <span>{isHi ? 'वैज्ञानिक सत्यापन देखें' : 'See the Validation'}</span>
            </button>
          </div>
        </div>

        {/* Real Ganga Interactive Map Card with Live API/Fixture Geometry */}
        <div className="relative z-10 mt-14 md:mt-20 bg-surface/95 backdrop-blur-md rounded-2xl p-4 sm:p-6 border border-border shadow-xl">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-3.5 mb-3.5 border-b border-border gap-2">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-brand-soft text-brand flex items-center justify-center">
                <MapPin size={18} />
              </div>
              <div>
                <h3 className="text-base font-bold text-text">
                  {isHi ? 'गंगा नदी स्क्रीनिंग (ऋषिकेश, उत्तराखण्ड)' : 'Ganga Reach Screening (near Rishikesh, Uttarakhand)'}
                </h3>
                <p className="text-xs text-text-tertiary font-mono">
                  AOI: 78.30°E – 78.35°E, 30.10°N – 30.15°N · EPSG:32644 (UTM 44N)
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge status="RUN AND PASSED" size="sm" />
              <span className="text-xs font-mono font-semibold bg-bg-muted text-text-tertiary px-2.5 py-1 rounded">
                Tier-0 HAND
              </span>
            </div>
          </div>

          {/* Live MapLibre Map Component with Real Ganga Extent */}
          <div className="rounded-xl overflow-hidden border border-border">
            <React.Suspense fallback={
              <div className="w-full h-[480px] bg-bg-muted flex items-center justify-center text-text-tertiary text-xs font-mono animate-pulse">
                Rendering Ganga hydrodynamic envelope...
              </div>
            }>
              <GangaMap height="480px" interactive={true} showControls={true} />
            </React.Suspense>
          </div>

          {/* Verified KPI Grid with Count-Up Animations & Required Fix F.4 Labels */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5 mt-4">
            <div className="bg-bg-subtle rounded-xl p-4 border border-border flex flex-col justify-between">
              <div>
                <p className="text-xs font-bold text-text-tertiary uppercase tracking-wider mb-1">
                  {isHi ? 'अनुमानित प्रवाह दर (इनपुट)' : 'Assumed breach inflow (scenario input)'}
                </p>
                <div className="flex items-baseline gap-1 my-1">
                  <span className="text-3xl font-bold text-text font-mono">
                    <CountUp target={5000} duration={1200} />
                  </span>
                  <span className="text-xs font-semibold text-text-secondary">m³/s</span>
                </div>
                <p className="text-xs text-text-secondary mt-1">Froehlich (2008) hydrograph</p>
              </div>
              <p className="text-[11px] font-mono text-text-tertiary pt-2 border-t border-border mt-3">
                Source: VALIDATION §11.1
              </p>
            </div>

            <div className="bg-bg-subtle rounded-xl p-4 border border-border flex flex-col justify-between">
              <div>
                <p className="text-xs font-bold text-text-tertiary uppercase tracking-wider mb-1">
                  {isHi ? 'जलप्लावन क्षेत्र' : 'Inundation Area'}
                </p>
                <div className="flex items-baseline gap-1 my-1">
                  <span className="text-3xl font-bold text-text font-mono">
                    <CountUp target={1.72} decimals={2} duration={1400} />
                  </span>
                  <span className="text-xs font-semibold text-text-secondary">km²</span>
                </div>
                <p className="text-xs text-text-secondary mt-1">1,918 wet 30m terrain cells</p>
              </div>
              <p className="text-[11px] font-mono text-text-tertiary pt-2 border-t border-border mt-3">
                Source: VALIDATION §11.1
              </p>
            </div>

            <div className="bg-bg-subtle rounded-xl p-4 border border-border flex flex-col justify-between">
              <div>
                <p className="text-xs font-bold text-text-tertiary uppercase tracking-wider mb-1">
                  {isHi ? 'अधिकतम जल गहराई' : 'Max Flood Depth'}
                </p>
                <div className="flex items-baseline gap-1 my-1">
                  <span className="text-3xl font-bold text-text font-mono">
                    <CountUp target={7.73} decimals={2} duration={1600} />
                  </span>
                  <span className="text-xs font-semibold text-text-secondary">m</span>
                </div>
                {/* Fix F.4: Depth above DEM water surface; true channel depth is greater */}
                <p className="text-xs text-text-secondary mt-1">
                  Depth above DEM water surface; true channel depth is greater.
                </p>
              </div>
              <p className="text-[11px] font-mono text-text-tertiary pt-2 border-t border-border mt-3">
                Source: Copernicus GLO-30 DEM
              </p>
            </div>

            <div className="bg-bg-subtle rounded-xl p-4 border border-border flex flex-col justify-between">
              <div>
                <p className="text-xs font-bold text-text-tertiary uppercase tracking-wider mb-1">
                  {isHi ? 'प्रभावित आबादी' : 'Exposed Population'}
                </p>
                <div className="flex items-baseline gap-1 my-1">
                  <span className="text-3xl font-bold text-text font-mono">
                    <CountUp target={2696} duration={1800} />
                  </span>
                  <span className="text-xs font-semibold text-text-secondary">people</span>
                </div>
                <p className="text-xs text-text-secondary mt-1">Intersected census blocks</p>
              </div>
              <p className="text-[11px] font-mono text-text-tertiary pt-2 border-t border-border mt-3">
                Source: WorldPop 2020 BSGM
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 2. Apple-Style Scroll Storytelling Section (§B) */}
      <ScrollStoryMap />

      {/* 3. The Preparedness Gap: Animated 6,598 Dot Grid (§B, Fix F.5) */}
      <DamDotGrid />

      {/* 4. Three-Tier Computational Architecture Cards with Animated Diagrams (§B) */}
      <section className="py-20 md:py-28 px-4 sm:px-6 lg:px-8 max-w-[1240px] mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
          <p className="text-xs font-bold text-brand uppercase tracking-wider">
            Multi-Fidelity Solvers
          </p>
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-text">
            {t('landing.tiersTitle')}
          </h2>
          <p className="text-base sm:text-lg text-text-secondary">
            {t('landing.tiersSubhead')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          {/* Tier-0 Card with Hover Lift & Animated Diagram (seconds) */}
          <div className="bg-surface rounded-2xl p-7 border border-border shadow-sm flex flex-col justify-between hover:-translate-y-2 hover:shadow-xl transition-all duration-300 group">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-md bg-bg-muted text-text-secondary">
                  TIER-0
                </span>
                <Badge status="RUN AND PASSED" size="sm" />
              </div>

              {/* Animated SVG Diagram for Tier-0: Gravity equilibrium in ~2 seconds */}
              <div className="w-full h-32 rounded-xl bg-bg-subtle border border-border flex items-center justify-center p-3 overflow-hidden relative">
                <svg className="w-full h-full" viewBox="0 0 200 80" fill="none">
                  <path d="M10 60 Q 60 70, 100 50 T 190 65" stroke="#94A3B8" strokeWidth="2" strokeDasharray="3 3" />
                  <rect x="75" y="20" width="10" height="40" fill="#475467" rx="2" />
                  <path d="M10 50 L 75 50 L 75 60 L 10 60 Z" fill="#93C5FD" opacity="0.6" />
                  {/* Flow arrow animates across */}
                  <path d="M85 45 Q 120 40, 180 58" stroke="#0071E3" strokeWidth="3" strokeLinecap="round" className="animate-pulse" />
                  <circle cx="180" cy="58" r="4" fill="#0071E3" />
                </svg>
                <span className="absolute bottom-2 right-2 text-[10px] font-mono bg-white/90 px-1.5 py-0.5 rounded text-brand font-semibold shadow-2xs">
                  t = 2.1s
                </span>
              </div>

              <div>
                <h3 className="text-2xl font-bold text-text">
                  {t('landing.tier0Title')}
                </h3>
                <p className="text-xs font-bold text-brand mt-1">
                  HAND + Synthetic Manning · ~2 seconds
                </p>
              </div>

              <p className="text-sm text-text-secondary leading-relaxed">
                {t('landing.tier0Desc')}
              </p>

              <div className="space-y-2 pt-3 border-t border-border text-xs text-text-secondary">
                <div className="flex justify-between">
                  <span>Terrain Grid:</span>
                  <span className="font-mono font-semibold text-text">Copernicus 30m</span>
                </div>
                <div className="flex justify-between">
                  <span>Solver Type:</span>
                  <span className="font-semibold text-text">Equilibrium Height Field</span>
                </div>
              </div>
            </div>

            <div className="pt-6">
              <button
                onClick={() => onNavigate('f05_results_explorer')}
                className="w-full py-3 px-4 rounded-xl border border-border-strong text-text font-bold text-sm hover:bg-bg-subtle active:scale-[0.98] transition-all flex items-center justify-between"
              >
                <span>Inspect Tier-0 Results</span>
                <ChevronRight size={16} />
              </button>
            </div>
          </div>

          {/* Tier-1 Card with Hover Lift & Animated Diagram (minutes) */}
          <div className="bg-surface rounded-2xl p-7 border border-border shadow-sm flex flex-col justify-between hover:-translate-y-2 hover:shadow-xl transition-all duration-300 group">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-md bg-bg-muted text-text-secondary">
                  TIER-1 (target)
                </span>
                <Badge status="PENDING" size="sm" />
              </div>

              {/* Animated SVG Diagram for Tier-1: Flexible Mesh 2D shallow water waves */}
              <div className="w-full h-32 rounded-xl bg-bg-subtle border border-border flex items-center justify-center p-3 overflow-hidden relative">
                <svg className="w-full h-full" viewBox="0 0 200 80" fill="none">
                  {/* Unstructured mesh grid */}
                  <polygon points="20,60 50,40 50,70" stroke="#CBD5E1" strokeWidth="1" />
                  <polygon points="50,40 90,35 90,65" stroke="#CBD5E1" strokeWidth="1" />
                  <polygon points="90,35 140,45 130,70" stroke="#CBD5E1" strokeWidth="1" />
                  <polygon points="140,45 185,55 170,75" stroke="#CBD5E1" strokeWidth="1" />
                  {/* Water surface wave propagation */}
                  <path d="M20 50 Q 70 30, 110 48 T 185 52" stroke="#0071E3" strokeWidth="2.5" fill="none" />
                  {/* Velocity vector arrows */}
                  <line x1="60" y1="45" x2="80" y2="44" stroke="#0369A1" strokeWidth="2" markerEnd="url(#arrow)" />
                  <line x1="110" y1="48" x2="135" y2="52" stroke="#0369A1" strokeWidth="2" markerEnd="url(#arrow)" />
                </svg>
                <span className="absolute bottom-2 right-2 text-[10px] font-mono bg-white/90 px-1.5 py-0.5 rounded text-brand font-semibold shadow-2xs">
                  t = 10 mins
                </span>
              </div>

              <div>
                <h3 className="text-2xl font-bold text-text">
                  {t('landing.tier1Title')}
                </h3>
                <p className="text-xs font-bold text-brand mt-1">
                  Delft3D Flexible Mesh · ~10 mins (CPU)
                </p>
              </div>

              <p className="text-sm text-text-secondary leading-relaxed">
                {t('landing.tier1Desc')}
              </p>

              <div className="space-y-2 pt-3 border-t border-border text-xs text-text-secondary">
                <div className="flex justify-between">
                  <span>Mesh Resolution:</span>
                  <span className="font-mono font-semibold text-text">Δx = 25m (11,827 cells)</span>
                </div>
                <div className="flex justify-between">
                  <span>Mass Balance:</span>
                  <span className="font-semibold text-status-pass">Exact (0 m³ residual)</span>
                </div>
              </div>
            </div>

            <div className="pt-6">
              <button
                onClick={() => onNavigate('f06_engine_comparison')}
                className="w-full py-3 px-4 rounded-xl border border-border-strong text-text font-bold text-sm hover:bg-bg-subtle active:scale-[0.98] transition-all flex items-center justify-between"
              >
                <span>View Mesh Specifications</span>
                <ChevronRight size={16} />
              </button>
            </div>
          </div>

          {/* Tier-2 Card with Fix F.6: "RUN · not yet validated" */}
          <div className="bg-surface rounded-2xl p-7 border border-border shadow-sm flex flex-col justify-between hover:-translate-y-2 hover:shadow-xl transition-all duration-300 group">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-md bg-bg-muted text-text-secondary">
                  TIER-2 (target)
                </span>
                {/* Fix F.6: Tier-2 badge -> "RUN · not yet validated" */}
                <Badge status="RUN · not yet validated" size="sm" />
              </div>

              {/* Animated SVG Diagram for Tier-2: Near-field 3D SPH particles bursting against structure */}
              <div className="w-full h-32 rounded-xl bg-bg-subtle border border-border flex items-center justify-center p-3 overflow-hidden relative">
                <svg className="w-full h-full" viewBox="0 0 200 80" fill="none">
                  {/* Concrete structure block */}
                  <rect x="135" y="25" width="18" height="45" fill="#475467" rx="1.5" />
                  {/* SPH particle cloud splash */}
                  <circle cx="30" cy="55" r="3" fill="#0071E3" />
                  <circle cx="50" cy="52" r="3.5" fill="#0071E3" />
                  <circle cx="70" cy="48" r="4" fill="#0071E3" />
                  <circle cx="95" cy="46" r="3.5" fill="#0284C7" />
                  <circle cx="120" cy="42" r="3.5" fill="#38BDF8" />
                  {/* Vertical splash along pillar */}
                  <circle cx="132" cy="30" r="3" fill="#38BDF8" />
                  <circle cx="130" cy="20" r="2.5" fill="#BAE6FD" />
                  <circle cx="138" cy="15" r="2" fill="#BAE6FD" />
                  <circle cx="158" cy="45" r="2.5" fill="#38BDF8" />
                </svg>
                <span className="absolute bottom-2 right-2 text-[10px] font-mono bg-white/90 px-1.5 py-0.5 rounded text-text-tertiary font-semibold shadow-2xs">
                  Near-Field 3D
                </span>
              </div>

              <div>
                <h3 className="text-2xl font-bold text-text">
                  {t('landing.tier2Title')}
                </h3>
                <p className="text-xs font-bold text-brand mt-1">
                  DualSPHysics SPH · GPU Accelerated
                </p>
              </div>

              <p className="text-sm text-text-secondary leading-relaxed">
                {t('landing.tier2Desc')}
              </p>

              <div className="space-y-2 pt-3 border-t border-border text-xs text-text-secondary">
                <div className="flex justify-between">
                  <span>Particle Count:</span>
                  <span className="font-mono font-semibold text-text">314,801 particles</span>
                </div>
                <div className="flex justify-between">
                  <span>Benchmark Status:</span>
                  <span className="font-semibold text-text-tertiary">NOT VERIFIED (paywalled source)</span>
                </div>
              </div>
            </div>

            <div className="pt-6">
              <button
                onClick={() => onNavigate('f19_benchmarks')}
                className="w-full py-3 px-4 rounded-xl border border-border-strong text-text font-bold text-sm hover:bg-bg-subtle active:scale-[0.98] transition-all flex items-center justify-between"
              >
                <span>Review SPH Logs</span>
                <ChevronRight size={16} />
              </button>
            </div>
          </div>

        </div>
      </section>

      {/* 5. Proof, Not Promises Section: Interactive Ritter Animated Plot (§B) */}
      <section className="py-20 md:py-28 bg-bg-subtle border-y border-border">
        <div className="max-w-[1240px] mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <p className="text-xs font-bold text-brand uppercase tracking-wider">
              Analytical Verification
            </p>
            <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-text">
              {t('landing.proofTitle')}
            </h2>
            <p className="text-base sm:text-lg text-text-secondary">
              {t('landing.proofSubhead')}
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            {/* Ritter Animated Draw-On Plot Component */}
            <RitterAnimatedPlot />

            {/* Operational Engine Verification Matrix Table */}
            <div className="bg-surface p-6 rounded-2xl border border-border shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-border">
                <h4 className="text-base font-bold text-text">
                  Operational Engine Verification Matrix
                </h4>
                <Badge status="RUN AND PASSED" size="sm" />
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-border bg-bg-muted text-text-tertiary">
                      <th className="py-3 px-3 font-bold">Engine / Solver</th>
                      <th className="py-3 px-3 font-bold">Benchmark Target</th>
                      <th className="py-3 px-3 font-bold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    <tr>
                      <td className="py-3 px-3 font-semibold text-text">Tier-0 HAND</td>
                      <td className="py-3 px-3 text-text-secondary">Ganga Reach Screening (5x5 km)</td>
                      <td className="py-3 px-3"><Badge status="RUN AND PASSED" size="sm" /></td>
                    </tr>
                    <tr>
                      <td className="py-3 px-3 font-semibold text-text">Delft3D Flexible Mesh</td>
                      <td className="py-3 px-3 text-text-secondary">Deltares c019 Smoke Test</td>
                      <td className="py-3 px-3"><Badge status="RUN AND PASSED" size="sm" /></td>
                    </tr>
                    <tr>
                      <td className="py-3 px-3 font-semibold text-text">Delft3D Flexible Mesh</td>
                      <td className="py-3 px-3 text-text-secondary">Ritter (1892) Dry Bed Analytical</td>
                      <td className="py-3 px-3"><Badge status="RUN AND PASSED" size="sm" /></td>
                    </tr>
                    <tr>
                      <td className="py-3 px-3 font-semibold text-text">Delft3D FM (Ganga 2D)</td>
                      <td className="py-3 px-3 text-text-secondary">Tier-1 vs Tier-0 Intercomparison</td>
                      <td className="py-3 px-3"><Badge status="PENDING" size="sm" /></td>
                    </tr>
                    <tr>
                      <td className="py-3 px-3 font-semibold text-text">DualSPHysics SPH</td>
                      <td className="py-3 px-3 text-text-secondary">3D Water Column Collapse Run</td>
                      <td className="py-3 px-3"><Badge status="RUN · not yet validated" size="sm" /></td>
                    </tr>
                    <tr>
                      <td className="py-3 px-3 font-semibold text-text">Sentinel-1 SAR GEE</td>
                      <td className="py-3 px-3 text-text-secondary">Kuttanad 2018 Flood Mapping</td>
                      <td className="py-3 px-3"><Badge status="RUN AND PASSED" size="sm" /></td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="pt-3 border-t border-border flex justify-between items-center text-xs">
                <span className="text-text-tertiary">Raw simulation output verified in CI</span>
                <button
                  onClick={() => onNavigate('f19_benchmarks')}
                  className="text-brand hover:underline font-bold"
                >
                  Inspect Full Audit Matrix →
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 6. Built For Emergency Command Section */}
      <section className="py-20 md:py-28 px-4 sm:px-6 lg:px-8 max-w-[1240px] mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
          <p className="text-xs font-bold text-brand uppercase tracking-wider">
            Operational Target Audience
          </p>
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-text">
            {t('landing.builtForTitle')}
          </h2>
          <p className="text-base sm:text-lg text-text-secondary">
            {t('landing.builtForSubhead')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-surface p-7 rounded-2xl border border-border shadow-sm space-y-3">
            <div className="w-12 h-12 rounded-xl bg-brand-soft text-brand flex items-center justify-center">
              <ShieldCheck size={26} />
            </div>
            <h3 className="text-xl font-bold text-text">
              {t('landing.audience1Title')}
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              {t('landing.audience1Desc')}
            </p>
          </div>

          <div className="bg-surface p-7 rounded-2xl border border-border shadow-sm space-y-3">
            <div className="w-12 h-12 rounded-xl bg-brand-soft text-brand flex items-center justify-center">
              <Layers size={26} />
            </div>
            <h3 className="text-xl font-bold text-text">
              {t('landing.audience2Title')}
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              {t('landing.audience2Desc')}
            </p>
          </div>

          <div className="bg-surface p-7 rounded-2xl border border-border shadow-sm space-y-3">
            <div className="w-12 h-12 rounded-xl bg-brand-soft text-brand flex items-center justify-center">
              <Activity size={26} />
            </div>
            <h3 className="text-xl font-bold text-text">
              {t('landing.audience3Title')}
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              {t('landing.audience3Desc')}
            </p>
          </div>
        </div>

        {/* Disclaimer about endorsements */}
        <div className="mt-12 p-4 rounded-xl bg-bg-muted border border-border text-center text-xs text-text-tertiary max-w-2xl mx-auto flex items-center justify-center gap-2">
          <Info size={16} className="text-text-secondary shrink-0" />
          <span>
            PravahX is built for emergency command teams as audience; this platform does not claim or imply official endorsement, accreditation, or certifications from government bodies.
          </span>
        </div>
      </section>

      {/* 7. Footer Section */}
      <footer className="py-12 bg-bg-subtle border-t border-border">
        <div className="max-w-[1240px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="space-y-1 text-center md:text-left">
              <p className="text-base font-bold text-text">
                PravahX Hydrodynamic Flood Intelligence Platform
              </p>
              <p className="text-xs text-text-tertiary">
                {t('landing.footerNotice')}
              </p>
            </div>

            {/* Authentic Data Attributions */}
            <div className="flex flex-wrap items-center justify-center gap-3 text-xs text-text-tertiary">
              <span>{t('landing.osmAttribution')}</span>
              <span>·</span>
              <span>{t('landing.worldpopAttribution')}</span>
              <span>·</span>
              <span>{t('landing.copernicusAttribution')}</span>
            </div>

            <div>
              <a
                href="https://github.com/Aesha023/The-Akashic-Nodes"
                target="_blank"
                rel="noreferrer"
                className="text-xs font-bold text-brand hover:underline inline-flex items-center gap-1.5"
              >
                <span>GitHub Repository</span>
                <ExternalLink size={13} />
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
