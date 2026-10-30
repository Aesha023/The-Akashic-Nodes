import React, { useState, useEffect } from 'react';
import { 
  Search, 
  X, 
  Compass, 
  Activity, 
  Map, 
  Satellite, 
  Users, 
  Navigation, 
  Award, 
  Cpu, 
  ShieldAlert, 
  Waves,
  LucideIcon
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { FeatureId } from '../../types';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectFeature: (feature: FeatureId) => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onSelectFeature,
}) => {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) {
          onClose();
        } else {
          // Open
        }
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const quickActions: { id: FeatureId; title: string; category: string; icon: LucideIcon }[] = [
    { id: 'landing', title: 'PravahX Overview & Landing', category: 'Navigation', icon: Waves },
    { id: 'f01_mission_control', title: 'Mission Control (F01)', category: 'Tactical Command', icon: Compass },
    { id: 'f04_run_monitor', title: 'Run Monitor (F04)', category: 'Tactical Command', icon: Activity },
    { id: 'f05_results_explorer', title: 'Results Explorer: Ganga Tier-0 (F05)', category: 'Analysis', icon: Map },
    { id: 'f09_impact', title: 'Impact Assessment & Exposure (F09)', category: 'Disaster', icon: Users },
    { id: 'f10_evacuation', title: 'Evacuation Router & Safe Corridors (F10)', category: 'Disaster', icon: Navigation },
    { id: 'f07_satellite_validation', title: 'Satellite SAR Validation: Kuttanad (F07)', category: 'Analysis', icon: Satellite },
    { id: 'f19_benchmarks', title: 'Validation & Benchmarks (Ritter, Delft3D, DualSPHysics) (F19)', category: 'Verification', icon: Award },
    { id: 'f20_health', title: 'System Health & Engine Services (F20)', category: 'Infrastructure', icon: Cpu },
    { id: 'f22_admin', title: 'Admin & User Security (F22)', category: 'Administration', icon: ShieldAlert },
  ];

  const filtered = quickActions.filter(
    (action) =>
      action.title.toLowerCase().includes(query.toLowerCase()) ||
      action.category.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-[#0B1220]/40 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="w-full max-w-xl bg-white rounded-xl shadow-lg border border-border overflow-hidden">
        {/* Search Input Bar */}
        <div className="flex items-center px-4 border-b border-border">
          <Search size={18} className="text-text-tertiary mr-2 shrink-0" />
          <input
            type="text"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t('topbar.searchPlaceholder')}
            className="w-full py-3.5 text-sm bg-transparent border-none text-text focus:outline-none placeholder:text-text-tertiary"
          />
          <button
            onClick={onClose}
            className="p-1 text-text-tertiary hover:text-text rounded-md"
          >
            <X size={16} />
          </button>
        </div>

        {/* Results list */}
        <div className="max-h-80 overflow-y-auto p-2">
          {filtered.length > 0 ? (
            filtered.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onSelectFeature(item.id);
                    onClose();
                  }}
                  className="w-full flex items-center justify-between p-2.5 rounded-lg hover:bg-bg-muted transition-colors text-left group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-md bg-bg-subtle group-hover:bg-brand-soft text-text-secondary group-hover:text-brand flex items-center justify-center transition-colors">
                      <Icon size={16} />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-text">
                        {item.title}
                      </p>
                      <p className="text-[10px] text-text-tertiary">
                        {item.category}
                      </p>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono text-text-tertiary bg-bg-muted px-1.5 py-0.5 rounded">
                    Jump
                  </span>
                </button>
              );
            })
          ) : (
            <div className="py-8 text-center text-xs text-text-tertiary">
              No results found for "{query}". Try "Ganga", "Tier-0", "Ritter", or "Admin".
            </div>
          )}
        </div>

        {/* Footer info */}
        <div className="px-4 py-2 bg-bg-subtle border-t border-border flex items-center justify-between text-[11px] text-text-tertiary">
          <span>Tip: Press ESC to close</span>
          <span className="font-mono">PravahX Navigation</span>
        </div>
      </div>
    </div>
  );
};
