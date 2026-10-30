import React from 'react';
import { 
  Play, 
  Map, 
  ShieldCheck, 
  ArrowRight, 
  Sparkles
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { FeatureId } from '../../types';
import { Tooltip } from '../common/Tooltip';
import { Badge } from '../common/Badge';
import { useAuth } from '../../context/AuthContext';

interface HomePageProps {
  onNavigate: (feature: FeatureId) => void;
}

export const HomePage: React.FC<HomePageProps> = ({ onNavigate }) => {
  const { i18n } = useTranslation();
  const { user } = useAuth();
  const isHi = i18n.language === 'hi';

  return (
    <div className="w-full min-h-[calc(100vh-64px)] bg-bg p-6 sm:p-10 lg:p-14 max-w-7xl mx-auto flex flex-col justify-between">
      {/* 1. Header with single clear English question */}
      <div className="space-y-3 max-w-3xl">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-pill bg-brand-soft border border-brand/20 text-brand text-xs font-semibold">
          <Sparkles size={14} className="stroke-[2.2]" />
          <span>{isHi ? 'प्रवाह-X त्वरित कमांड सेंटर' : 'PravahX Tactical Command'}</span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-bold tracking-tight text-text leading-tight">
          {isHi 
            ? 'आज आप क्या करना चाहेंगे?' 
            : 'What would you like to do today?'}
        </h1>

        <p className="text-base sm:text-lg text-text-secondary leading-relaxed">
          {isHi
            ? '६,५९८ पंजीकृत बांधों के लिए हाइड्रोडायनामिक सिमुलेशन, बाढ़ मानचित्र, या वैज्ञानिक सत्यापन चुनें।'
            : 'Select an operation below to simulate a breach, inspect active inundation extents, or review scientific validation proofs.'}
        </p>
      </div>

      {/* 2. Three Large, High-Contrast Cards (Simplicity First) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 my-10">
        
        {/* Card 1: Run a new scenario */}
        <div className="bg-surface rounded-2xl p-8 border border-border hover:border-border-strong hover:shadow-lg transition-all duration-200 flex flex-col justify-between group">
          <div className="space-y-4">
            <div className="w-14 h-14 rounded-xl bg-bg-muted border border-border flex items-center justify-center text-brand group-hover:scale-105 transition-transform">
              <Play size={28} className="stroke-[2.2] ml-0.5" />
            </div>

            <div>
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-text-tertiary">
                {isHi ? 'सिमुलेशन' : 'SIMULATION'}
              </span>
              <h2 className="text-2xl font-bold text-text mt-1">
                {isHi ? 'नया परिदृश्य चलाएँ' : 'Run a new scenario'}
              </h2>
            </div>

            <p className="text-base text-text-secondary leading-relaxed">
              {isHi
                ? 'काल्पनिक बांध विफलता प्रवाह दर दर्ज करें और '
                : 'Configure breach hydrograph and run rapid '}
              <Tooltip 
                term={isHi ? 'टियर-0' : 'Tier-0'} 
                definition={isHi 
                  ? 'गुरुत्वाकर्षण-संतुलन विधि द्वारा कुछ ही सेकंड में बाढ़ सीमा का निर्धारण।' 
                  : 'Fast gravity-equilibrium screening calculating peak flood depths in ~2 seconds.'}
              />
              {isHi 
                ? ' स्क्रीनिंग द्वारा तुरंत बाढ़ सीमा प्राप्त करें।' 
                : ' flood screening on high-resolution terrain.'}
            </p>

            <div className="pt-2 text-sm text-text-tertiary space-y-1">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-brand"></span>
                <span>{isHi ? '६,५९८ बांधों की सूची' : '6,598 monitored dams in NRLD'}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-brand"></span>
                <span>{isHi ? 'स्वचालित फ्रॉइलिच समीकरण' : 'Automatic Froehlich breach breach equations'}</span>
              </div>
            </div>
          </div>

          <div className="pt-8">
            <button
              onClick={() => onNavigate('f02_new_scenario')}
              className="w-full py-3.5 px-5 rounded-xl border border-border-strong text-text font-semibold text-base hover:bg-bg-subtle active:scale-[0.98] transition-all flex items-center justify-center gap-2 shadow-2xs"
            >
              <span>{isHi ? 'नया परिदृश्य बनाएँ' : 'Start new scenario'}</span>
              <ArrowRight size={18} />
            </button>
          </div>
        </div>

        {/* Card 2: Open latest result (PRIMARY ACTION FOR GOVERNMENT OFFICERS) */}
        <div className="bg-surface rounded-2xl p-8 border-2 border-brand shadow-md hover:shadow-xl transition-all duration-200 flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute top-0 right-0 bg-brand text-white px-4 py-1 text-xs font-bold rounded-bl-xl uppercase tracking-wider shadow-2xs">
            {isHi ? 'नवीनतम परिणाम तैयार' : 'Ready to inspect'}
          </div>

          <div className="space-y-4">
            <div className="w-14 h-14 rounded-xl bg-brand text-white flex items-center justify-center shadow-md group-hover:scale-105 transition-transform">
              <Map size={28} className="stroke-[2.2]" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-brand">
                  {isHi ? 'त्वरित बाढ़ नक्शा' : 'PRIMARY DISASTER MAP'}
                </span>
                <Badge status="RUN AND PASSED" size="sm" />
              </div>
              <h2 className="text-2xl font-bold text-text mt-1">
                {isHi ? 'नवीनतम परिणाम खोलें' : 'Open latest result'}
              </h2>
            </div>

            <div className="p-3 bg-brand-soft rounded-lg border border-brand/20 text-sm font-semibold text-brand">
              {isHi
                ? 'गंगा नदी स्क्रीनिंग (ऋषिकेश, उत्तराखण्ड)'
                : 'Which villages flood if this dam breaks?'}
            </div>

            <p className="text-base text-text-secondary leading-relaxed">
              {isHi
                ? 'गंगा नदी क्षेत्र का '
                : 'Inspect the Ganga Reach breach screening: peak depth of 7.73 m, 2,696 exposed people, and inundated roads mapped via '}
              <Tooltip 
                term={isHi ? 'हैंड (HAND)' : 'HAND'} 
                definition={isHi 
                  ? 'हाइट एबव नियरेस्ट ड्रेनेज - हाइड्रोलॉजिकल स्थलाकृतिक सामान्यीकरण पद्धति।' 
                  : 'Height Above Nearest Drainage - terrain normalization method for gravity-driven flood extents.'}
              />
              {isHi
                ? ' मॉडल। २४००x१६०० रिज़ॉल्यूशन पर त्वरित दृश्य।'
                : ' on 30m Copernicus GLO-30.'}
            </p>

            <div className="text-xs font-mono text-text-tertiary pt-1">
              {isHi
                ? 'स्थान: ३०.१२° उ, ७८.३२° पू · प्रभाव: २,६९६ लोग'
                : 'Location: 30.12°N, 78.32°E · Impact: 2,696 people'}
            </div>
          </div>

          <div className="pt-8">
            {/* The One Big Blue Button (Simplicity First: Sign in -> Click this -> Flood map!) */}
            <button
              id="open-flood-map-btn"
              onClick={() => onNavigate('f05_results_explorer')}
              className="w-full py-4 px-6 rounded-xl bg-brand hover:bg-brand-hover text-white font-bold text-lg active:scale-[0.98] transition-all flex items-center justify-center gap-2.5 shadow-md"
            >
              <span>{isHi ? 'बाढ़ मानचित्र खोलें' : 'Open Flood Map'}</span>
              <ArrowRight size={20} className="stroke-[2.5]" />
            </button>
          </div>
        </div>

        {/* Card 3: Check validation */}
        <div className="bg-surface rounded-2xl p-8 border border-border hover:border-border-strong hover:shadow-lg transition-all duration-200 flex flex-col justify-between group">
          <div className="space-y-4">
            <div className="w-14 h-14 rounded-xl bg-bg-muted border border-border flex items-center justify-center text-status-pass group-hover:scale-105 transition-transform">
              <ShieldCheck size={28} className="stroke-[2.2]" />
            </div>

            <div>
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-text-tertiary">
                {isHi ? 'सत्यापन' : 'SCIENTIFIC INTEGRITY'}
              </span>
              <h2 className="text-2xl font-bold text-text mt-1">
                {isHi ? 'सत्यापन प्रमाण देखें' : 'Check validation'}
              </h2>
            </div>

            <p className="text-base text-text-secondary leading-relaxed">
              {isHi
                ? 'रिटर १८९२ विश्लेषणात्मक बांध विफलता मानक और '
                : 'Review analytical Ritter (1892) dam-break benchmarks and '}
              <Tooltip 
                term={isHi ? 'CSI मानक' : 'CSI score'} 
                definition={isHi 
                  ? 'क्रिटिकल सक्सेस इंडेक्स - उपग्रह प्रेक्षण और सिमुलेशन बाढ़ सीमा के बीच स्थानिक मिलान का मापक।' 
                  : 'Critical Success Index - spatial flood extent overlap metric between simulation and satellite radar.'}
              />
              {isHi
                ? ' द्वारा सत्यापित गणितीय परिशुद्धता की समीक्षा करें।'
                : ' with mass conservation proofs (500k → 500k m³).'}
            </p>

            <div className="pt-2 text-sm text-text-tertiary space-y-1">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-status-pass"></span>
                <span>{isHi ? 'रिटर शुष्क तल: RMSE ०.०४२ मीटर' : 'Ritter Dry Bed: RMSE 0.042m (Pass < 0.5m)'}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-status-pass"></span>
                <span>{isHi ? 'डेल्फ़्ट3D FM: शून्य द्रव्यमान क्षरण' : 'Delft3D FM: 0 m³ mass residual'}</span>
              </div>
            </div>
          </div>

          <div className="pt-8">
            <button
              onClick={() => onNavigate('f19_benchmarks')}
              className="w-full py-3.5 px-5 rounded-xl border border-border-strong text-text font-semibold text-base hover:bg-bg-subtle active:scale-[0.98] transition-all flex items-center justify-center gap-2 shadow-2xs"
            >
              <span>{isHi ? 'सत्यापन रिपोर्ट देखें' : 'View validation report'}</span>
              <ArrowRight size={18} />
            </button>
          </div>
        </div>

      </div>

      {/* 3. Bottom Wall-Display Ready Summary Bar */}
      <div className="p-4 rounded-xl bg-surface border border-border flex flex-col md:flex-row items-center justify-between text-xs text-text-secondary gap-3">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 font-medium text-text">
            <span className="w-2.5 h-2.5 rounded-full bg-status-pass animate-pulse"></span>
            <span>{isHi ? 'सिस्टम स्थिति: सक्रिय' : 'Hydrodynamic Solver Engine: Online'}</span>
          </div>
          <span className="text-border">|</span>
          <span>{isHi ? '६,५९८ बांध ट्रैक किए गए' : '6,598 large dams monitored in registry'}</span>
        </div>

        <div className="flex items-center gap-3">
          {user && (
            <span className="text-text-tertiary">
              {isHi ? 'प्रमाणीकृत भूमिका:' : 'Session Role:'} <strong className="text-text font-semibold capitalize">{user.role}</strong> ({user.username})
            </span>
          )}
          <button
            onClick={() => onNavigate('f01_mission_control')}
            className="text-brand hover:underline font-semibold flex items-center gap-1"
          >
            <span>{isHi ? 'पूर्ण मिशन नियंत्रण खोलें' : 'Open Mission Control'}</span>
            <ArrowRight size={13} />
          </button>
        </div>
      </div>
    </div>
  );
};
