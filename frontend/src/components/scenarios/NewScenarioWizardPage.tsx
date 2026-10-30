import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  ArrowRight, 
  ArrowLeft, 
  Play, 
  Save, 
  Info, 
  MapPin, 
  Gauge, 
  Cpu, 
  CheckCircle2
} from 'lucide-react';
import { FeatureId } from '../../types';
import { Tooltip } from '../common/Tooltip';

interface NewScenarioWizardPageProps {
  onNavigate: (feature: FeatureId) => void;
}

export const NewScenarioWizardPage: React.FC<NewScenarioWizardPageProps> = ({ onNavigate }) => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(1);

  // Form State
  const [selectedDam, setSelectedDam] = useState('ganga_rishikesh');

  // Breach assumptions
  const [peakInflow, setPeakInflow] = useState(5000); // m3/s
  const [breachWidth, setBreachWidth] = useState(120); // m
  const [timeToFailure, setTimeToFailure] = useState(1.2); // hrs
  const [useFroehlich, setUseFroehlich] = useState(true);

  // Tier Choice
  const [selectedTier, setSelectedTier] = useState<'tier0' | 'tier1' | 'tier2'>('tier0');

  // Submit / Run state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [draftSaved, setDraftSaved] = useState(false);

  const handleRunScenario = async () => {
    setIsSubmitting(true);
    try {
      const payload = {
        name: `Hypothetical Run: ${selectedDam === 'ganga_rishikesh' ? 'Ganga Reach' : 'Custom AOI'} (${peakInflow} m³/s)`,
        dam_id: selectedDam,
        peak_inflow_m3s: peakInflow,
        breach_width_m: breachWidth,
        formation_time_hr: timeToFailure,
        froehlich_auto: useFroehlich,
        tier: selectedTier,
      };

      await fetch('/api/v1/scenarios', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      // Transition to Run Monitor
      setTimeout(() => {
        setIsSubmitting(false);
        onNavigate('f04_run_monitor');
      }, 600);
    } catch {
      setIsSubmitting(false);
      onNavigate('f04_run_monitor');
    }
  };

  const handleSaveDraft = () => {
    setDraftSaved(true);
    setTimeout(() => setDraftSaved(false), 2500);
  };

  return (
    <div className="p-6 sm:p-10 max-w-5xl mx-auto space-y-8">
      {/* 1. Header (Part A3 standard) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-4">
        <div>
          <div className="text-xs font-mono font-semibold tracking-wider text-text-tertiary uppercase">
            F02 · {isHi ? 'परिदृश्य विज़ार्ड' : 'NEW SCENARIO'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text mt-1">
            {isHi ? 'काल्पनिक बांध विफलता कहाँ और कैसे घटित होती है?' : 'Where and how does the hypothetical dam breach occur?'}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {isHi 
              ? 'स्थान चुनें, विफलता पैरामीटर दर्ज करें और हाइड्रोडायनामिक स्तर का चयन करें।' 
              : 'Select target reach, configure breach hydrodynamics, and choose solver tier.'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleSaveDraft}
            className="py-2.5 px-4 rounded-xl border border-border text-text font-medium text-sm hover:bg-bg-subtle active:scale-[0.98] transition-all flex items-center gap-2"
          >
            <Save size={16} />
            <span>{draftSaved ? (isHi ? 'सहेजा गया!' : 'Draft Saved!') : (isHi ? 'ड्राफ्ट सहेजें' : 'Save Draft')}</span>
          </button>
        </div>
      </div>

      {/* 2. Step Progress Indicator */}
      <div className="grid grid-cols-4 gap-2 sm:gap-4 text-xs font-medium">
        {[
          { num: 1, title: isHi ? '1. क्षेत्र चयन' : '1. Area & Dam' },
          { num: 2, title: isHi ? '2. विफलता प्रवाह' : '2. Breach Inflow' },
          { num: 3, title: isHi ? '3. टियर चयन' : '3. Solver Tier' },
          { num: 4, title: isHi ? '4. समीक्षा एवं रन' : '4. Review & Run' },
        ].map((s) => (
          <div
            key={s.num}
            onClick={() => s.num <= currentStep && setCurrentStep(s.num as any)}
            className={`py-3 px-3 rounded-xl border transition-all cursor-pointer flex items-center gap-2 ${
              currentStep === s.num
                ? 'bg-brand/5 border-brand text-brand font-semibold'
                : currentStep > s.num
                ? 'bg-bg-subtle border-border text-text'
                : 'bg-white border-border/60 text-text-tertiary cursor-not-allowed'
            }`}
          >
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-bold ${
              currentStep === s.num
                ? 'bg-brand text-white'
                : currentStep > s.num
                ? 'bg-status-pass text-white'
                : 'bg-bg-muted text-text-tertiary'
            }`}>
              {currentStep > s.num ? '✓' : s.num}
            </span>
            <span className="truncate">{s.title}</span>
          </div>
        ))}
      </div>

      {/* 3. Step Panels */}
      <div className="bg-white rounded-2xl border border-border p-6 sm:p-8 space-y-6 shadow-xs">
        {/* STEP 1: Area & Dam */}
        {currentStep === 1 && (
          <div className="space-y-6 animate-in fade-in duration-200">
            <div>
              <h2 className="text-lg font-bold text-text flex items-center gap-2">
                <MapPin size={20} className="text-brand" />
                <span>{isHi ? 'स्थान अथवा बांध संरचना का चयन करें' : 'Select Target Reach or Structure'}</span>
              </h2>
              <p className="text-xs text-text-secondary mt-1">
                {isHi 
                  ? 'राष्ट्रीय बड़े बांध रजिस्टर (NRLD) से संरचना चुनें अथवा कस्टम क्षेत्र परिभाषित करें।' 
                  : 'Select an indexed structure from the National Register of Large Dams (NRLD) or specify an AOI.'}
              </p>
            </div>

            <div className="space-y-4">
              <label className="block text-xs font-semibold text-text uppercase tracking-wider">
                {isHi ? 'मानक संरचना सूची' : 'Indexed Dam / Valley Reach'}
              </label>
              <select
                value={selectedDam}
                onChange={(e) => setSelectedDam(e.target.value)}
                className="w-full py-3 px-4 rounded-lg border border-border bg-white text-text font-medium text-sm focus:outline-hidden focus:ring-3 focus:ring-brand/35 transition-all"
              >
                <option value="ganga_rishikesh">Ganga Reach near Rishikesh (Benchmark AOI 5×5 km · Verified Copernicus GLO-30)</option>
                <option value="nrld_dam_0042">NRLD-0042 · Western Ghats Masonry Gravity Dam (Screening Ready)</option>
                <option value="nrld_dam_0118">NRLD-0118 · Himalayan Sub-Basin Earthfill Embankment (Screening Ready)</option>
                <option value="nrld_dam_0891">NRLD-0891 · Central Peninsular Composite Structure (Screening Ready)</option>
              </select>
            </div>

            <div className="p-4 rounded-xl bg-bg-subtle border border-border flex items-start gap-3">
              <Info size={18} className="text-brand shrink-0 mt-0.5" />
              <div className="text-xs text-text-secondary space-y-1">
                <span className="font-semibold text-text">{isHi ? 'सत्यापित भूभाग डेटा:' : 'Verified Elevation Model:'}</span>
                <p>
                  Copernicus GLO-30 30m Digital Elevation Model (DEM) and OpenStreetMap network pre-cached for selected reach.
                </p>
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button
                onClick={() => setCurrentStep(2)}
                className="py-3 px-6 rounded-xl bg-brand text-white font-semibold text-sm hover:bg-brand/90 active:scale-[0.98] transition-all flex items-center gap-2"
              >
                <span>{isHi ? 'अगला: विफलता प्रवाह' : 'Next: Breach Inflow'}</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: Breach Assumptions */}
        {currentStep === 2 && (
          <div className="space-y-6 animate-in fade-in duration-200">
            <div>
              <h2 className="text-lg font-bold text-text flex items-center gap-2">
                <Gauge size={20} className="text-brand" />
                <span>{isHi ? 'विफलता एवं प्रवाह दर पैरामीटर' : 'Breach Hydrograph & Hydraulic Assumptions'}</span>
              </h2>
              <p className="text-xs text-text-secondary mt-1">
                {isHi 
                  ? 'अनुभवजन्य समीकरणों द्वारा चरम निर्वहन और विफलता समय निर्धारित करें।' 
                  : 'Define peak discharge rate, average breach width, and failure progression time.'}
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-text uppercase tracking-wider flex items-center gap-1.5">
                    <span>{isHi ? 'चरम प्रवाह दर (Peak Inflow)' : 'Peak Breach Inflow (Q_peak)'}</span>
                    <Tooltip term="Q_peak" definition="Maximum instantaneous water discharge escaping through the breached structure opening." />
                  </label>
                  <span className="text-xs font-mono font-bold text-brand">{peakInflow.toLocaleString()} m³/s</span>
                </div>
                <input
                  type="range"
                  min="500"
                  max="25000"
                  step="250"
                  value={peakInflow}
                  onChange={(e) => setPeakInflow(Number(e.target.value))}
                  className="w-full accent-brand cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-text-tertiary font-mono">
                  <span>500 m³/s</span>
                  <span>Default: 5,000 m³/s (VALIDATION §11.1)</span>
                  <span>25,000 m³/s</span>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-text uppercase tracking-wider flex items-center gap-1.5">
                    <span>{isHi ? 'औसत विफलता चौड़ाई' : 'Average Breach Width (B_avg)'}</span>
                    <Tooltip term="Froehlich (2008)" definition="Empirical formulation: B_avg = 0.27 · K_0 · V_w^0.32 · h_b^0.04 based on 74 dam breach case studies." />
                  </label>
                  <span className="text-xs font-mono font-bold text-brand">{breachWidth} m</span>
                </div>
                <input
                  type="range"
                  min="20"
                  max="500"
                  step="10"
                  value={breachWidth}
                  onChange={(e) => setBreachWidth(Number(e.target.value))}
                  className="w-full accent-brand cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-text-tertiary font-mono">
                  <span>20 m</span>
                  <span>Default: 120 m</span>
                  <span>500 m</span>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-text uppercase tracking-wider flex items-center gap-1.5">
                    <span>{isHi ? 'विफलता निर्माण समय' : 'Time to Failure (T_f)'}</span>
                    <Tooltip term="T_f" definition="Time elapsed from breach initiation until full breach dimensions are attained." />
                  </label>
                  <span className="text-xs font-mono font-bold text-brand">{timeToFailure.toFixed(1)} hrs</span>
                </div>
                <input
                  type="range"
                  min="0.2"
                  max="6.0"
                  step="0.1"
                  value={timeToFailure}
                  onChange={(e) => setTimeToFailure(Number(e.target.value))}
                  className="w-full accent-brand cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-text-tertiary font-mono">
                  <span>0.2 hrs</span>
                  <span>Default: 1.2 hrs</span>
                  <span>6.0 hrs</span>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-bg-subtle border border-border flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold text-text">{isHi ? 'फ्रॉइलिच (2008) स्वचालित गणना' : 'Froehlich (2008) Automated Formulation'}</div>
                  <div className="text-[11px] text-text-secondary">{isHi ? 'जलाशय मात्रा एवं ऊंचाई से स्वतः गणना' : 'Auto-derive parameters from reservoir storage'}</div>
                </div>
                <input
                  type="checkbox"
                  checked={useFroehlich}
                  onChange={(e) => setUseFroehlich(e.target.checked)}
                  className="w-4 h-4 accent-brand cursor-pointer"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-border">
              <button
                onClick={() => setCurrentStep(1)}
                className="py-3 px-5 rounded-xl border border-border text-text font-medium text-sm hover:bg-bg-subtle active:scale-[0.98] transition-all flex items-center gap-2"
              >
                <ArrowLeft size={16} />
                <span>{isHi ? 'पीछे' : 'Back'}</span>
              </button>
              <button
                onClick={() => setCurrentStep(3)}
                className="py-3 px-6 rounded-xl bg-brand text-white font-semibold text-sm hover:bg-brand/90 active:scale-[0.98] transition-all flex items-center gap-2"
              >
                <span>{isHi ? 'अगला: टियर चयन' : 'Next: Solver Tier'}</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: Solver Tier Choice */}
        {currentStep === 3 && (
          <div className="space-y-6 animate-in fade-in duration-200">
            <div>
              <h2 className="text-lg font-bold text-text flex items-center gap-2">
                <Cpu size={20} className="text-brand" />
                <span>{isHi ? 'हाइड्रोडायनामिक सॉल्वर स्तर का चयन' : 'Select Hydrodynamic Computational Tier'}</span>
              </h2>
              <p className="text-xs text-text-secondary mt-1">
                {isHi 
                  ? 'तत्काल स्क्रीनिंग हेतु टियर-0 सक्रिय है; उच्च स्तरीय सॉल्वर की स्थिति पारदर्शी रूप से प्रदर्शित है।' 
                  : 'Tier-0 static screening is fully operational; higher tiers show honest scientific capability status.'}
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Tier-0 (Enabled) */}
              <div 
                onClick={() => setSelectedTier('tier0')}
                className={`p-5 rounded-2xl border-2 transition-all cursor-pointer flex flex-col justify-between ${
                  selectedTier === 'tier0'
                    ? 'border-brand bg-brand/5 shadow-xs'
                    : 'border-border bg-white hover:border-border-strong'
                }`}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-brand-soft text-brand uppercase">
                      Tier-0
                    </span>
                    <span className="text-[11px] font-bold text-status-pass flex items-center gap-1">
                      <CheckCircle2 size={13} />
                      <span>{isHi ? 'सक्रिय' : 'Available'}</span>
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-text">
                    {isHi ? 'HAND स्थैतिक स्क्रीनिंग' : 'HAND Gravity Screening'}
                  </h3>
                  <p className="text-xs text-text-secondary leading-relaxed">
                    Copernicus 30m DEM equilibrium screening. Computes peak water depth raster, road severances, and exposed populations in ~2 seconds.
                  </p>
                </div>
                <div className="pt-4 border-t border-border/60 text-[11px] font-mono text-text-tertiary">
                  Runtime: ~2 seconds · Local CPU
                </div>
              </div>

              {/* Tier-1 (Selectable) */}
              <div 
                onClick={() => setSelectedTier('tier1')}
                className={`p-5 rounded-2xl border-2 transition-all cursor-pointer flex flex-col justify-between ${
                  selectedTier === 'tier1'
                    ? 'border-brand bg-brand/5 shadow-xs'
                    : 'border-border bg-white hover:border-border-strong'
                }`}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-[#FEF0C7] text-[#B54708] uppercase">
                      Tier-1 · Delft3D FM
                    </span>
                    <span className="text-[11px] font-bold text-[#B54708] px-2 py-0.5 rounded-pill bg-[#FFFAEB] border border-[#FEDF89]">
                      Requires compute worker
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-text">
                    {isHi ? 'डेल्फ़्ट3D फ्लेक्सिबल मेश 2D' : 'Delft3D Flexible Mesh 2D'}
                  </h3>
                  <p className="text-xs text-text-secondary leading-relaxed">
                    2D depth-averaged shallow water equations with sub-grid bed levels. Dynamic wave arrival isochrones and velocity vectors.
                  </p>
                </div>
                <div className="pt-4 border-t border-border/60 text-[11px] font-mono text-text-tertiary">
                  Expected runtime: ~18 min on 4 CPU cores · Status: Calibrated past run available
                </div>
              </div>

              {/* Tier-2 (Selectable) */}
              <div 
                onClick={() => setSelectedTier('tier2')}
                className={`p-5 rounded-2xl border-2 transition-all cursor-pointer flex flex-col justify-between ${
                  selectedTier === 'tier2'
                    ? 'border-brand bg-brand/5 shadow-xs'
                    : 'border-border bg-white hover:border-border-strong'
                }`}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-[#EFF8FF] text-[#175CD3] uppercase">
                      Tier-2 · DualSPHysics
                    </span>
                    <span className="text-[11px] font-bold text-[#175CD3] px-2 py-0.5 rounded-pill bg-[#EFF8FF] border border-[#B2DDFF]">
                      Requires compute worker
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-text">
                    {isHi ? 'ड्यूल-एसपीएचइजिक्स 3D SPH' : 'DualSPHysics 3D SPH'}
                  </h3>
                  <p className="text-xs text-text-secondary leading-relaxed">
                    Smoothed particle hydrodynamics for 3D free-surface bore impact, dynamic wave splashing, and structural hydrodynamic loading.
                  </p>
                </div>
                <div className="pt-4 border-t border-border/60 text-[11px] font-mono text-text-tertiary">
                  Expected runtime: ~42 min on CUDA GPU · Status: Not yet validated vs flume
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-border">
              <button
                onClick={() => setCurrentStep(2)}
                className="py-3 px-5 rounded-xl border border-border text-text font-medium text-sm hover:bg-bg-subtle active:scale-[0.98] transition-all flex items-center gap-2"
              >
                <ArrowLeft size={16} />
                <span>{isHi ? 'पीछे' : 'Back'}</span>
              </button>
              <button
                onClick={() => setCurrentStep(4)}
                className="py-3 px-6 rounded-xl bg-brand text-white font-semibold text-sm hover:bg-brand/90 active:scale-[0.98] transition-all flex items-center gap-2"
              >
                <span>{isHi ? 'अगला: समीक्षा एवं रन' : 'Next: Review & Run'}</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* STEP 4: Review & Run */}
        {currentStep === 4 && (
          <div className="space-y-6 animate-in fade-in duration-200">
            <div>
              <h2 className="text-lg font-bold text-text flex items-center gap-2">
                <CheckCircle2 size={20} className="text-brand" />
                <span>{isHi ? 'परिदृश्य विवरण की समीक्षा करें' : 'Review & Launch Scenario Run'}</span>
              </h2>
              <p className="text-xs text-text-secondary mt-1">
                {isHi 
                  ? 'पुष्टि करें और सिमुलेशन प्रारंभ करें। परिणाम तुरंत रन मॉनिटर में दिखाई देंगे।' 
                  : 'Verify configuration inputs and dispatch Tier-0 screening simulation.'}
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-bg-subtle border border-border">
              <div>
                <div className="text-[11px] font-mono text-text-tertiary uppercase">Target Reach</div>
                <div className="text-sm font-bold text-text mt-0.5">Ganga Rishikesh (5×5 km)</div>
              </div>
              <div>
                <div className="text-[11px] font-mono text-text-tertiary uppercase">Peak Inflow</div>
                <div className="text-sm font-bold text-brand mt-0.5">{peakInflow.toLocaleString()} m³/s</div>
              </div>
              <div>
                <div className="text-[11px] font-mono text-text-tertiary uppercase">Breach Width</div>
                <div className="text-sm font-bold text-text mt-0.5">{breachWidth} m</div>
              </div>
              <div>
                <div className="text-[11px] font-mono text-text-tertiary uppercase">Selected Tier</div>
                <div className="text-sm font-bold text-text mt-0.5">
                  {selectedTier === 'tier0' && <span className="text-status-pass">Tier-0 Screening</span>}
                  {selectedTier === 'tier1' && <span className="text-[#B54708]">Tier-1 Delft3D FM 2D</span>}
                  {selectedTier === 'tier2' && <span className="text-[#175CD3]">Tier-2 DualSPHysics 3D</span>}
                </div>
              </div>
            </div>

            {selectedTier !== 'tier0' && (
              <div className="p-4 rounded-xl bg-[#FFFAEB] border border-[#FEDF89] text-[#B54708] text-xs flex items-start gap-3">
                <Info size={18} className="shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">Requires Remote Compute Worker:</span>
                  <p className="mt-0.5 text-text-secondary">
                    This job will be scheduled to the <code className="font-mono font-bold text-text">{selectedTier === 'tier1' ? 'delft3d' : 'dualsphysics'}</code> Celery queue. If no compute worker is connected via the worker adapter API, the job will show status <strong className="text-text">Waiting for compute worker</strong> until an agent registers.
                  </p>
                </div>
              </div>
            )}

            <div className="flex items-center justify-between pt-4 border-t border-border">
              <button
                onClick={() => setCurrentStep(3)}
                className="py-3 px-5 rounded-xl border border-border text-text font-medium text-sm hover:bg-bg-subtle active:scale-[0.98] transition-all flex items-center gap-2"
              >
                <ArrowLeft size={16} />
                <span>{isHi ? 'पीछे' : 'Back'}</span>
              </button>

              <button
                onClick={handleRunScenario}
                disabled={isSubmitting}
                className="py-3.5 px-8 rounded-xl bg-brand text-white font-bold text-base hover:bg-brand/90 active:scale-[0.98] transition-all flex items-center gap-2 shadow-sm disabled:opacity-50"
              >
                <Play size={18} className="fill-white" />
                <span>{isSubmitting ? (isHi ? 'रन शुरू हो रहा है...' : 'Launching Run...') : (isHi ? 'सिमुलेशन रन चलाएँ' : 'Launch Simulation Run')}</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
