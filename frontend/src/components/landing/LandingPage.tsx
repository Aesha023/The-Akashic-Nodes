import React from 'react';
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
import { GangaMap } from '../map/GangaMap';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { KpiTile } from '../common/KpiTile';
import { FeatureId } from '../../types';

interface LandingPageProps {
  onNavigate: (feature: FeatureId) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  const { t } = useTranslation();

  return (
    <div className="w-full min-h-screen bg-bg text-text font-sans">
      {/* 1. Hero Section */}
      <section className="relative pt-12 pb-20 md:pt-20 md:pb-28 px-4 sm:px-6 lg:px-8 max-w-[1240px] mx-auto">
        <div className="text-center max-w-4xl mx-auto space-y-6">
          {/* Scientific honesty badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-pill bg-bg-muted border border-border text-xs text-text-secondary font-medium shadow-2xs">
            <span className="w-2 h-2 rounded-full bg-brand animate-pulse"></span>
            <span>SIH 2026 · PS 26161 · Scientific Hydrodynamic Intelligence</span>
          </div>

          {/* Huge headline */}
          <h1 className="text-4xl sm:text-6xl lg:text-[72px] font-bold tracking-tight text-text leading-[1.08]">
            {t('landing.heroHeadline')}
          </h1>

          {/* Subhead */}
          <p className="text-lg sm:text-xl text-text-secondary max-w-2xl mx-auto leading-relaxed">
            {t('landing.heroSubhead')}
          </p>

          {/* Two primary CTAs */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <Button
              size="lg"
              variant="primary"
              onClick={() => onNavigate('f01_mission_control')}
              icon={<ArrowRight size={18} />}
              iconPosition="right"
              className="shadow-md"
            >
              {t('landing.openConsole')}
            </Button>
            <Button
              size="lg"
              variant="secondary"
              onClick={() => onNavigate('f19_benchmarks')}
              icon={<Award size={18} />}
            >
              {t('landing.seeValidation')}
            </Button>
          </div>
        </div>

        {/* Real Ganga Interactive Map Card */}
        <div className="mt-12 md:mt-16 bg-surface rounded-2xl p-3 sm:p-5 border border-border shadow-lg">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-3 mb-3 border-b border-border gap-2">
            <div className="flex items-center gap-2">
              <MapPin size={16} className="text-brand shrink-0" />
              <div>
                <h3 className="text-sm font-semibold text-text">
                  Ganga Reach Screening (near Rishikesh, Uttarakhand)
                </h3>
                <p className="text-[11px] text-text-tertiary font-mono">
                  AOI: 78.30°E – 78.35°E, 30.10°N – 30.15°N · EPSG:32644 (UTM 44N)
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge status="RUN AND PASSED" size="sm" />
              <span className="text-[11px] font-mono bg-bg-muted text-text-tertiary px-2 py-0.5 rounded">
                Tier-0 HAND
              </span>
            </div>
          </div>

          {/* Live MapLibre Map Component */}
          <GangaMap height="460px" interactive={true} showControls={true} />

          {/* Verified KPI Grid below Map */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
            <KpiTile
              label="Peak Inflow"
              value="5,000.0"
              unit="m³/s"
              source="Froehlich (2008) · VALIDATION §11.1"
            />
            <KpiTile
              label="Inundation Area"
              value="1.72"
              unit="km²"
              source="1,918 wet 30m cells · VALIDATION §11.1"
            />
            <KpiTile
              label="Max Depth"
              value="7.73"
              unit="m"
              source="Copernicus DEM GLO-30 · VALIDATION §11.1"
            />
            <KpiTile
              label="Exposed Population"
              value="2,696"
              unit="people"
              source="WorldPop 2020 BSGM · VALIDATION §11.2"
            />
          </div>
        </div>
      </section>

      {/* 2. The Problem Section (Big Number Band) */}
      <section className="py-16 md:py-24 bg-bg-subtle border-y border-border">
        <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <p className="text-xs font-semibold text-brand uppercase tracking-wider mb-2">
              The Critical Preparedness Gap
            </p>
            <div className="flex flex-col sm:flex-row items-baseline gap-3 my-2">
              <span className="text-5xl sm:text-7xl font-bold tracking-tight text-text tabular-nums">
                {t('landing.problemNumber')}
              </span>
              <span className="text-xl sm:text-2xl font-semibold text-text-secondary">
                {t('landing.problemTitle')}
              </span>
            </div>
            <p className="text-sm font-medium text-text-tertiary mt-2">
              {t('landing.problemSource')}
            </p>
            <p className="text-base text-text-secondary mt-4 leading-relaxed">
              {t('landing.problemDescription')}
            </p>
          </div>
        </div>
      </section>

      {/* 3. Three Tiers Section */}
      <section className="py-20 md:py-28 px-4 sm:px-6 lg:px-8 max-w-[1200px] mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
          <p className="text-xs font-semibold text-brand uppercase tracking-wider">
            Multi-Fidelity Solvers
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-text">
            {t('landing.tiersTitle')}
          </h2>
          <p className="text-base text-text-secondary">
            {t('landing.tiersSubhead')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Tier-0 Card */}
          <div className="bg-surface rounded-xl p-6 border border-border shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-mono font-semibold px-2 py-1 rounded bg-bg-muted text-text-secondary">
                  TIER-0
                </span>
                <Badge status="RUN AND PASSED" size="sm" />
              </div>
              <h3 className="text-xl font-bold text-text mb-1">
                {t('landing.tier0Title')}
              </h3>
              <p className="text-xs font-semibold text-brand mb-3">
                {t('landing.tier0Engine')} · {t('landing.tier0Time')}
              </p>
              <p className="text-sm text-text-secondary leading-relaxed">
                {t('landing.tier0Desc')}
              </p>

              <div className="mt-5 space-y-2 pt-4 border-t border-border/60 text-xs text-text-secondary">
                <div className="flex justify-between">
                  <span>Terrain Resolution:</span>
                  <span className="font-mono text-text">30 m (GLO-30)</span>
                </div>
                <div className="flex justify-between">
                  <span>Routing Dynamics:</span>
                  <span className="text-text">Static equilibrium</span>
                </div>
                <div className="flex justify-between">
                  <span>Arrival Times:</span>
                  <span className="text-text-tertiary">Not simulated in T0</span>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-border">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onNavigate('f05_results_explorer')}
                icon={<ChevronRight size={14} />}
                iconPosition="right"
                className="w-full justify-between"
              >
                Inspect Tier-0 Output
              </Button>
            </div>
          </div>

          {/* Tier-1 Card */}
          <div className="bg-surface rounded-xl p-6 border border-border shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-mono font-semibold px-2 py-1 rounded bg-bg-muted text-text-secondary">
                  TIER-1 (target)
                </span>
                <Badge status="PENDING" size="sm" />
              </div>
              <h3 className="text-xl font-bold text-text mb-1">
                {t('landing.tier1Title')}
              </h3>
              <p className="text-xs font-semibold text-brand mb-3">
                {t('landing.tier1Engine')} · {t('landing.tier1Time')}
              </p>
              <p className="text-sm text-text-secondary leading-relaxed">
                {t('landing.tier1Desc')}
              </p>

              <div className="mt-5 space-y-2 pt-4 border-t border-border/60 text-xs text-text-secondary">
                <div className="flex justify-between">
                  <span>Mesh Resolution:</span>
                  <span className="font-mono text-text">Δx = 25 m (11,827 cells)</span>
                </div>
                <div className="flex justify-between">
                  <span>Mass Balance:</span>
                  <span className="text-status-pass font-medium">Exact (0 m³ residual)</span>
                </div>
                <div className="flex justify-between">
                  <span>Comparison Status:</span>
                  <span className="text-status-pending font-medium">Pending warm-up equilibrium</span>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-border">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onNavigate('f06_engine_comparison')}
                icon={<ChevronRight size={14} />}
                iconPosition="right"
                className="w-full justify-between"
              >
                View Intercomparison Gates
              </Button>
            </div>
          </div>

          {/* Tier-2 Card */}
          <div className="bg-surface rounded-xl p-6 border border-border shadow-sm flex flex-col justify-between hover:shadow-md transition-shadow">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-mono font-semibold px-2 py-1 rounded bg-bg-muted text-text-secondary">
                  TIER-2 (target)
                </span>
                <Badge status="RUN AND PASSED" size="sm" />
              </div>
              <h3 className="text-xl font-bold text-text mb-1">
                {t('landing.tier2Title')}
              </h3>
              <p className="text-xs font-semibold text-brand mb-3">
                {t('landing.tier2Engine')} · {t('landing.tier2Time')}
              </p>
              <p className="text-sm text-text-secondary leading-relaxed">
                {t('landing.tier2Desc')}
              </p>

              <div className="mt-5 space-y-2 pt-4 border-t border-border/60 text-xs text-text-secondary">
                <div className="flex justify-between">
                  <span>Particle Count:</span>
                  <span className="font-mono text-text">314,801 total particles</span>
                </div>
                <div className="flex justify-between">
                  <span>Hardware Run:</span>
                  <span className="text-text">Tesla T4 GPU (389s wall)</span>
                </div>
                <div className="flex justify-between">
                  <span>Benchmark Status:</span>
                  <span className="text-status-unverified font-medium">NOT VERIFIED (paywalled source)</span>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-border">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onNavigate('f19_benchmarks')}
                icon={<ChevronRight size={14} />}
                iconPosition="right"
                className="w-full justify-between"
              >
                Review SPH Logs
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Proof, Not Promises Section */}
      <section className="py-20 md:py-28 bg-bg-subtle border-y border-border">
        <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <p className="text-xs font-semibold text-brand uppercase tracking-wider">
              Analytical Verification
            </p>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-text">
              {t('landing.proofTitle')}
            </h2>
            <p className="text-base text-text-secondary">
              {t('landing.proofSubhead')}
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
            {/* Real Ritter 1892 benchmark plot */}
            <div className="bg-surface p-4 sm:p-6 rounded-xl border border-border shadow-sm">
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-border">
                <div>
                  <h4 className="text-sm font-semibold text-text">
                    Analytical Dam-Break Benchmark: Ritter (1892)
                  </h4>
                  <p className="text-[11px] text-text-tertiary">
                    Delft3D Flexible Mesh vs Exact Dry-Bed Solution (t = 30s)
                  </p>
                </div>
                <Badge status="RUN AND PASSED" size="sm" />
              </div>

              {/* Verified Ritter plot image */}
              <div className="relative rounded-lg overflow-hidden border border-border/80 bg-white p-2">
                <img
                  src="/docs/img/ritter_t30.png"
                  alt="Analytical Dam Break Ritter 1892 Benchmark Comparison Plot at t=30s"
                  className="w-full h-auto object-contain max-h-[340px] mx-auto"
                  onError={(e) => {
                    // Fallback visual illustration if static path not mounted
                    (e.target as HTMLElement).style.display = 'none';
                  }}
                />
              </div>

              <p className="text-xs text-text-secondary mt-3 leading-relaxed">
                {t('landing.ritterDesc')}
              </p>
              <div className="mt-3 flex items-center justify-between text-[11px] font-mono text-text-tertiary pt-2 border-t border-border/60">
                <span>Mass Conservation: 500,000 → 500,000 m³</span>
                <span>Depth RMSE: 0.042 m (Pass &lt; 0.5m)</span>
              </div>
            </div>

            {/* Engine Validation Matrix Table */}
            <div className="bg-surface p-4 sm:p-6 rounded-xl border border-border shadow-sm">
              <h4 className="text-sm font-semibold text-text mb-4">
                Operational Engine Verification Matrix
              </h4>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-border bg-bg-muted text-text-tertiary">
                      <th className="py-2.5 px-3 font-semibold">Engine / Setup</th>
                      <th className="py-2.5 px-3 font-semibold">Benchmark Target</th>
                      <th className="py-2.5 px-3 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-text">
                        Tier-0 HAND
                      </td>
                      <td className="py-2.5 px-3 text-text-secondary">
                        Ganga Reach Screening (5x5 km)
                      </td>
                      <td className="py-2.5 px-3">
                        <Badge status="RUN AND PASSED" size="sm" />
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-text">
                        Delft3D Flexible Mesh
                      </td>
                      <td className="py-2.5 px-3 text-text-secondary">
                        Deltares c019 Smoke Test
                      </td>
                      <td className="py-2.5 px-3">
                        <Badge status="RUN AND PASSED" size="sm" />
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-text">
                        Delft3D Flexible Mesh
                      </td>
                      <td className="py-2.5 px-3 text-text-secondary">
                        Ritter (1892) Dry Bed
                      </td>
                      <td className="py-2.5 px-3">
                        <Badge status="RUN AND PASSED" size="sm" />
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-text">
                        Delft3D FM (Ganga 2D)
                      </td>
                      <td className="py-2.5 px-3 text-text-secondary">
                        Tier-1 vs Tier-0 Intercomparison
                      </td>
                      <td className="py-2.5 px-3">
                        <Badge status="PENDING" size="sm" />
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-text">
                        DualSPHysics SPH
                      </td>
                      <td className="py-2.5 px-3 text-text-secondary">
                        3D Water Column Collapse Run
                      </td>
                      <td className="py-2.5 px-3">
                        <Badge status="RUN AND PASSED" size="sm" />
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2.5 px-3 font-medium text-text">
                        Sentinel-1 SAR GEE
                      </td>
                      <td className="py-2.5 px-3 text-text-secondary">
                        Kuttanad 2018 Flood Mapping
                      </td>
                      <td className="py-2.5 px-3">
                        <Badge status="RUN AND PASSED" size="sm" />
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="mt-4 pt-3 border-t border-border flex justify-between items-center text-xs">
                <span className="text-text-tertiary">
                  Raw logs verified in CI &amp; Colab sessions
                </span>
                <button
                  onClick={() => onNavigate('f19_benchmarks')}
                  className="text-brand hover:underline font-semibold"
                >
                  View Full Verification Report →
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Built For Section */}
      <section className="py-20 md:py-28 px-4 sm:px-6 lg:px-8 max-w-[1200px] mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
          <p className="text-xs font-semibold text-brand uppercase tracking-wider">
            Operational Purpose
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-text">
            {t('landing.builtForTitle')}
          </h2>
          <p className="text-base text-text-secondary">
            {t('landing.builtForSubhead')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-surface p-6 rounded-xl border border-border shadow-sm">
            <div className="w-10 h-10 rounded-lg bg-brand-soft text-brand flex items-center justify-center mb-4">
              <ShieldCheck size={22} />
            </div>
            <h3 className="text-lg font-bold text-text mb-2">
              {t('landing.audience1Title')}
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              {t('landing.audience1Desc')}
            </p>
          </div>

          <div className="bg-surface p-6 rounded-xl border border-border shadow-sm">
            <div className="w-10 h-10 rounded-lg bg-brand-soft text-brand flex items-center justify-center mb-4">
              <Layers size={22} />
            </div>
            <h3 className="text-lg font-bold text-text mb-2">
              {t('landing.audience2Title')}
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              {t('landing.audience2Desc')}
            </p>
          </div>

          <div className="bg-surface p-6 rounded-xl border border-border shadow-sm">
            <div className="w-10 h-10 rounded-lg bg-brand-soft text-brand flex items-center justify-center mb-4">
              <Activity size={22} />
            </div>
            <h3 className="text-lg font-bold text-text mb-2">
              {t('landing.audience3Title')}
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed">
              {t('landing.audience3Desc')}
            </p>
          </div>
        </div>

        {/* Disclaimer about endorsements */}
        <div className="mt-10 p-4 rounded-xl bg-bg-muted border border-border text-center text-xs text-text-tertiary max-w-2xl mx-auto">
          <Info size={14} className="inline mr-1 text-text-secondary -mt-0.5" />
          <span>
            PravahX is built for emergency command teams as audience; this system does not claim or imply official endorsement, accreditation, or certifications from government bodies.
          </span>
        </div>
      </section>

      {/* 6. Footer Section */}
      <footer className="py-12 bg-bg-subtle border-t border-border">
        <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="space-y-1 text-center md:text-left">
              <p className="text-sm font-semibold text-text">
                PravahX Hydrodynamic Flood Intelligence Platform
              </p>
              <p className="text-xs text-text-tertiary">
                {t('landing.footerNotice')}
              </p>
            </div>

            {/* Authentic Data Attributions */}
            <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-text-tertiary">
              <span>{t('landing.osmAttribution')}</span>
              <span>·</span>
              <span>{t('landing.worldpopAttribution')}</span>
              <span>·</span>
              <span>{t('landing.copernicusAttribution')}</span>
            </div>

            <div className="flex items-center gap-3">
              <a
                href="https://github.com/Aesha023/The-Akashic-Nodes"
                target="_blank"
                rel="noreferrer"
                className="text-xs font-medium text-brand hover:underline inline-flex items-center gap-1"
              >
                <span>GitHub Repository</span>
                <ExternalLink size={12} />
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
