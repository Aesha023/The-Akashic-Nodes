import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  BellRing, 
  Plus, 
  Trash2, 
  Radio
} from 'lucide-react';
import { FeatureId } from '../../types';
import { DemoBadge } from '../common/DemoBadge';

interface AlertRulesPageProps {
  onNavigate?: (feature: FeatureId) => void;
}

interface AlertRule {
  id: string;
  name: string;
  metric: string;
  condition: string;
  threshold: string;
  channel: string;
  enabled: boolean;
}

interface DemoAlert {
  id: string;
  timestamp: string;
  level: 'CRITICAL' | 'WARNING' | 'ADVISORY';
  title: string;
  reach: string;
  recipients: string;
}

export const AlertRulesPage: React.FC<AlertRulesPageProps> = () => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  // REAL Rules Engine
  const [rules, setRules] = useState<AlertRule[]>([
    { id: 'rule_01', name: 'Emergency Flood Depth Breach', metric: 'Peak Inundation Depth', condition: '>', threshold: '3.0 meters', channel: 'Civil Defense Webhook', enabled: true },
    { id: 'rule_02', name: 'High Population Exposure Alert', metric: 'Exposed Citizens', condition: '>=', threshold: '1,000 people', channel: 'District Emergency Email', enabled: true },
    { id: 'rule_03', name: 'Rapid River Rate of Rise', metric: 'Water Rise Velocity', condition: '>', threshold: '0.5 m/hour', channel: 'Operations SMS Gateway', enabled: true },
  ]);

  const [showAddRule, setShowAddRule] = useState(false);
  const [ruleName, setRuleName] = useState('');
  const [metric, setMetric] = useState('Peak Inundation Depth');
  const [threshold, setThreshold] = useState('2.5 m');
  const [channel, setChannel] = useState('Civil Defense Webhook');

  // DEMO Alerts stream
  const demoAlerts: DemoAlert[] = [
    { id: 'alt_01', timestamp: '2026-10-30 08:30 UTC', level: 'CRITICAL', title: 'Simulated Spillway Exceedance Warning', reach: 'Demo Reach Alpha (Chain A)', recipients: '14 District Officers via Webhook' },
    { id: 'alt_02', timestamp: '2026-10-29 18:15 UTC', level: 'WARNING', title: 'Rapid Valley Influx Trigger (>0.4 m/hr)', reach: 'Alpine Catchment B', recipients: 'EOC Incident Commanders' },
    { id: 'alt_03', timestamp: '2026-10-28 12:00 UTC', level: 'ADVISORY', title: 'Routine Glacial Lake Area Advisory', reach: 'Demo Glacial Lake Alpha', recipients: 'Surveillance Desk' },
  ];

  const handleCreateRule = () => {
    if (!ruleName.trim()) return;
    setRules([
      ...rules,
      {
        id: `rule_0${rules.length + 1}`,
        name: ruleName,
        metric,
        condition: '>',
        threshold,
        channel,
        enabled: true,
      },
    ]);
    setRuleName('');
    setShowAddRule(false);
  };

  const handleDeleteRule = (id: string) => {
    setRules(rules.filter((r) => r.id !== id));
  };

  return (
    <div className="p-6 sm:p-10 max-w-7xl mx-auto space-y-6">
      {/* 1. Header (Part A3 standard) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-4">
        <div>
          <div className="text-xs font-mono font-semibold tracking-wider text-text-tertiary uppercase">
            F17 · {isHi ? 'चेतावनी नियम एवं लॉग' : 'MONITORING'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text mt-1">
            {isHi ? 'जल स्तर बढ़ने पर किन अधिकारियों को तुरंत चेतावनी दी जानी चाहिए?' : 'Who needs to be warned immediately when water levels rise?'}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {isHi 
              ? 'स्वचालित प्रारंभिक चेतावनी नियम, थ्रेशोल्ड और मल्टी-चैनल प्रसारण कॉन्फ़िगरेशन।' 
              : 'Configure automated early warning rules, hydraulic thresholds, and multi-channel dispatch.'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAddRule(true)}
            className="py-2.5 px-4 rounded-xl bg-brand text-white font-semibold text-sm hover:bg-brand/90 active:scale-[0.98] transition-all flex items-center gap-2 shadow-2xs"
          >
            <Plus size={16} />
            <span>{isHi ? 'नया नियम बनाएँ' : 'Create Alert Rule'}</span>
          </button>
        </div>
      </div>

      {/* 2. REAL Rules Engine Configuration Table */}
      <div className="bg-white rounded-2xl border border-border p-6 space-y-4 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <BellRing size={18} className="text-brand" />
            <h2 className="text-sm font-bold text-text uppercase tracking-wider">
              {isHi ? 'सक्रिय आपातकालीन चेतावनी नियम (वास्तविक नियम इंजन)' : 'Active Early Warning Threshold Rules'}
            </h2>
          </div>
          <span className="text-xs font-mono text-text-tertiary">
            Source: /api/v1/lake-watch/rules
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-bg-subtle/80 text-text-secondary text-xs uppercase font-semibold border-b border-border">
              <tr>
                <th className="py-2.5 px-4">{isHi ? 'नियम का नाम' : 'Rule Name'}</th>
                <th className="py-2.5 px-4">{isHi ? 'मापदंड एवं शर्त' : 'Metric & Condition'}</th>
                <th className="py-2.5 px-4">{isHi ? 'थ्रेशोल्ड' : 'Threshold'}</th>
                <th className="py-2.5 px-4">{isHi ? 'अधिसूचना चैनल' : 'Notification Channel'}</th>
                <th className="py-2.5 px-4">{isHi ? 'स्थिति' : 'Status'}</th>
                <th className="py-2.5 px-4 text-right">{isHi ? 'हटाएँ' : 'Action'}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {rules.map((rule) => (
                <tr key={rule.id} className="h-12 hover:bg-bg-subtle/50 transition-colors">
                  <td className="py-2.5 px-4 font-semibold text-text">{rule.name}</td>
                  <td className="py-2.5 px-4 font-mono text-xs text-text-secondary">{rule.metric} {rule.condition}</td>
                  <td className="py-2.5 px-4 font-mono font-bold text-brand">{rule.threshold}</td>
                  <td className="py-2.5 px-4 text-xs text-text-secondary">{rule.channel}</td>
                  <td className="py-2.5 px-4">
                    <span className="px-2 py-0.5 rounded-pill text-[10px] font-bold bg-[#ECFDF3] text-[#067647] border border-[#D1FADF]">
                      ENABLED
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-right">
                    <button
                      onClick={() => handleDeleteRule(rule.id)}
                      className="p-1 rounded text-text-tertiary hover:text-status-fail transition-colors"
                      title="Delete rule"
                    >
                      <Trash2 size={15} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. DEMO Notification Stream */}
      <div className="bg-white rounded-2xl border border-border p-6 space-y-4 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Radio size={18} className="text-brand" />
            <h2 className="text-sm font-bold text-text uppercase tracking-wider">
              {isHi ? 'हाल ही में प्रसारित चेतावनियाँ (प्रदर्शन स्ट्रीम)' : 'Dispatched Alert Log Stream'}
            </h2>
            <DemoBadge />
          </div>
          <span className="text-xs font-mono text-text-tertiary">
            Fictional emergency broadcasts
          </span>
        </div>

        <div className="space-y-3">
          {demoAlerts.map((alt) => (
            <div key={alt.id} className="p-4 rounded-xl border border-border bg-bg-subtle/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                    alt.level === 'CRITICAL'
                      ? 'bg-[#FEF3F2] text-[#B42318] border border-[#FECDCA]'
                      : alt.level === 'WARNING'
                      ? 'bg-[#FFFAEB] text-[#B54708] border border-[#FEDF89]'
                      : 'bg-[#EFF8FF] text-[#175CD3] border border-[#B2DDFF]'
                  }`}>
                    {alt.level}
                  </span>
                  <span className="text-xs font-bold text-text">{alt.title}</span>
                </div>
                <div className="text-xs text-text-secondary">
                  Reach: <strong className="text-text">{alt.reach}</strong> · Broadcasted to: {alt.recipients}
                </div>
              </div>

              <div className="text-xs font-mono text-text-tertiary whitespace-nowrap">
                {alt.timestamp}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Modal to add rule */}
      {showAddRule && (
        <div className="fixed inset-0 bg-[#0B1220]/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl border border-border max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-base font-bold text-text">{isHi ? 'नया चेतावनी नियम' : 'Configure Alert Rule'}</h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-text mb-1">Rule Name</label>
                <input
                  type="text"
                  placeholder="e.g. Critical Depth Exceedance"
                  value={ruleName}
                  onChange={(e) => setRuleName(e.target.value)}
                  className="w-full py-2 px-3 rounded-lg border border-border font-medium focus:ring-2 focus:ring-brand/30"
                />
              </div>
              <div>
                <label className="block font-semibold text-text mb-1">Trigger Metric</label>
                <select
                  value={metric}
                  onChange={(e) => setMetric(e.target.value)}
                  className="w-full py-2 px-3 rounded-lg border border-border font-medium focus:ring-2 focus:ring-brand/30"
                >
                  <option value="Peak Inundation Depth">Peak Inundation Depth (meters)</option>
                  <option value="Exposed Citizens">Exposed Population Count (people)</option>
                  <option value="Water Rise Velocity">Water Level Rate of Rise (m/hr)</option>
                </select>
              </div>
              <div>
                <label className="block font-semibold text-text mb-1">Threshold Value</label>
                <input
                  type="text"
                  value={threshold}
                  onChange={(e) => setThreshold(e.target.value)}
                  className="w-full py-2 px-3 rounded-lg border border-border font-mono text-xs focus:ring-2 focus:ring-brand/30"
                />
              </div>
              <div>
                <label className="block font-semibold text-text mb-1">Notification Dispatch Channel</label>
                <select
                  value={channel}
                  onChange={(e) => setChannel(e.target.value)}
                  className="w-full py-2 px-3 rounded-lg border border-border font-medium focus:ring-2 focus:ring-brand/30"
                >
                  <option value="Civil Defense Webhook">Civil Defense Webhook</option>
                  <option value="District Emergency Email">District Emergency Email</option>
                  <option value="State Operations SMS">State Operations SMS Gateway</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowAddRule(false)}
                className="py-2 px-4 rounded-xl border border-border text-xs font-semibold hover:bg-bg-subtle"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateRule}
                className="py-2 px-5 rounded-xl bg-brand text-white text-xs font-semibold hover:bg-brand/90"
              >
                Save Alert Rule
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
