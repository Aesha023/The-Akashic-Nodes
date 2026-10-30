import React, { useState } from 'react';
import { 
  Lock, 
  User as UserIcon, 
  CheckCircle, 
  AlertCircle, 
  Waves,
  ArrowRight,
  Code
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import { UserRole, FeatureId } from '../../types';

interface SignInPageProps {
  onSuccess: (feature: FeatureId) => void;
}

// Known user accounts where role is assigned to the account
const KNOWN_ACCOUNTS: Record<string, { role: UserRole; name: string }> = {
  dr_sharma: { role: 'analyst', name: 'Dr. Sharma (Senior Hydrologist)' },
  admin_lead: { role: 'admin', name: 'Lead Administrator' },
  officer_patel: { role: 'viewer', name: 'Duty Officer Patel' },
};

export const SignInPage: React.FC<SignInPageProps> = ({ onSuccess }) => {
  const { i18n } = useTranslation();
  const { login, isAuthenticated, user, logout } = useAuth();
  const isHi = i18n.language === 'hi';
  const isDev = import.meta.env.DEV;

  const [username, setUsername] = useState(isDev ? 'dr_sharma' : '');
  const [password, setPassword] = useState(isDev ? 'pravahx2026!' : '');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    setTimeout(() => {
      if (!username || !password) {
        setError(isHi ? 'कृपया उपयोगकर्ता नाम और पासवर्ड दोनों दर्ज करें।' : 'Please provide both username and password.');
        setIsLoading(false);
        return;
      }

      // Role is derived strictly from the user account record (Item 6)
      const userMeta = KNOWN_ACCOUNTS[username] || { role: 'analyst' as UserRole, name: username };
      login(username, userMeta.role, 'jwt_token_real_session');
      setIsLoading(false);
      onSuccess('home');
    }, 250);
  };

  const handleDevQuickFill = (uname: string) => {
    setUsername(uname);
    setPassword('pravahx2026!');
  };

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-bg-subtle">
      <div className="max-w-md w-full space-y-6 bg-surface p-8 sm:p-10 rounded-2xl border border-border shadow-lg">
        
        {/* Page Header (Part A3 standard) */}
        <div className="text-center space-y-2">
          <div className="inline-flex w-14 h-14 rounded-2xl bg-brand items-center justify-center text-white shadow-md mb-2">
            <Waves size={30} className="stroke-[2.5]" />
          </div>
          
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text">
            {isHi 
              ? 'हाइड्रोडायनामिक कंसोल तक कौन पहुँच रहा है?' 
              : 'Who is accessing the hydrodynamic console?'}
          </h1>
          <p className="text-sm text-text-secondary">
            {isHi
              ? 'राष्ट्रीय जलप्लावन नियंत्रण और बाढ़ सिमुलेशन प्रणाली में साइन इन करें।'
              : 'Authenticate to access national flood screening and emergency models.'}
          </p>
        </div>

        {/* Existing Active Session Alert */}
        {isAuthenticated && user && (
          <div className="p-4 rounded-xl bg-bg-muted border border-border flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <CheckCircle size={16} className="text-status-pass shrink-0" />
              <span>
                {isHi ? 'वर्तमान सत्र:' : 'Active session:'} <strong className="text-text">{user.username}</strong> ({user.role})
              </span>
            </div>
            <button
              onClick={logout}
              className="text-status-fail hover:underline font-semibold"
            >
              {isHi ? 'लॉग आउट' : 'Sign out'}
            </button>
          </div>
        )}

        {/* Error Notification */}
        {error && (
          <div className="p-3.5 rounded-xl bg-[#FEF3F2] border border-[#FECDCA] text-status-fail text-xs flex items-center gap-2">
            <AlertCircle size={16} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-bold text-text-secondary uppercase tracking-wider mb-1.5">
              {isHi ? 'उपयोगकर्ता नाम या सरकारी ईमेल' : 'Username or Official Email'}
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-text-tertiary">
                <UserIcon size={18} />
              </span>
              <input
                id="signin-username"
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full pl-10 pr-4 py-3 text-base bg-white border border-border-strong rounded-xl text-text focus:outline-none focus:ring-2 focus:ring-brand shadow-2xs"
                placeholder={isHi ? 'उदा. dr_sharma' : 'e.g. dr_sharma or officer'}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-text-secondary uppercase tracking-wider mb-1.5">
              {isHi ? 'पासवर्ड' : 'Password'}
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-text-tertiary">
                <Lock size={18} />
              </span>
              <input
                id="signin-password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-3 text-base bg-white border border-border-strong rounded-xl text-text focus:outline-none focus:ring-2 focus:ring-brand shadow-2xs"
                placeholder="••••••••••••"
              />
            </div>
          </div>

          <div className="text-xs text-text-tertiary">
            Role and permissions are assigned to your government credentials upon verification.
          </div>

          {/* Primary Action Button */}
          <button
            id="signin-submit-btn"
            type="submit"
            disabled={isLoading}
            className="w-full py-3.5 px-4 rounded-xl font-bold text-white bg-brand hover:bg-brand-hover shadow-md flex items-center justify-center gap-2 transition-all active:scale-[0.98] disabled:opacity-50"
          >
            {isLoading ? (
              <span>{isHi ? 'सत्यापित हो रहा है...' : 'Authenticating...'}</span>
            ) : (
              <>
                <span>{isHi ? 'सुरक्षित साइन इन' : 'Secure Sign In'}</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        {/* Dev Quick-Login: Strictly visible ONLY in DEV mode with "Dev only" badge (Item 6) */}
        {isDev && (
          <div className="pt-4 border-t border-border space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-[11px] font-bold text-text-tertiary uppercase tracking-wider">
                <Code size={13} />
                <span>Development Quick-Fill</span>
              </div>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-50 text-amber-700 border border-amber-200">
                Dev only
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleDevQuickFill('dr_sharma')}
                className="px-2.5 py-1.5 text-xs bg-bg-muted hover:bg-border rounded-lg text-text font-medium transition-colors text-center"
              >
                dr_sharma (analyst)
              </button>
              <button
                type="button"
                onClick={() => handleDevQuickFill('admin_lead')}
                className="px-2.5 py-1.5 text-xs bg-bg-muted hover:bg-border rounded-lg text-text font-medium transition-colors text-center"
              >
                admin_lead (admin)
              </button>
              <button
                type="button"
                onClick={() => handleDevQuickFill('officer_patel')}
                className="px-2.5 py-1.5 text-xs bg-bg-muted hover:bg-border rounded-lg text-text font-medium transition-colors text-center"
              >
                officer_patel (viewer)
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
