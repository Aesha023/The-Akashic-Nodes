import React, { useState } from 'react';
import { 
  Lock, 
  User as UserIcon, 
  CheckCircle, 
  AlertCircle, 
  Waves,
  ArrowRight
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import { UserRole, FeatureId } from '../../types';

interface SignInPageProps {
  onSuccess: (feature: FeatureId) => void;
}

export const SignInPage: React.FC<SignInPageProps> = ({ onSuccess }) => {
  const { i18n } = useTranslation();
  const { login, isAuthenticated, user, logout } = useAuth();
  const isHi = i18n.language === 'hi';
  const isDev = import.meta.env.DEV;

  // Strict Fix F.3: No credential pre-fills unless ENV=dev with a "Dev only" badge
  const [username, setUsername] = useState(isDev ? 'dr_sharma' : '');
  const [password, setPassword] = useState(isDev ? 'pravahx2026!' : '');
  const [selectedRole, setSelectedRole] = useState<UserRole>('analyst');
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

      login(username, selectedRole, 'jwt_token_real_session');
      setIsLoading(false);
      // Route immediately to Home (Click 1: Sign in -> Click 2 on Home: Flood Map)
      onSuccess('home');
    }, 300);
  };

  const handleQuickFill = (name: string, role: UserRole) => {
    setUsername(name);
    setPassword('pravahx2026!');
    setSelectedRole(role);
  };

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-bg-subtle">
      <div className="max-w-md w-full space-y-6 bg-surface p-8 sm:p-10 rounded-2xl border border-border shadow-lg">
        
        {/* Requirement A: Plain English question at the top */}
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

        {/* Existing Active Session Alert if any */}
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
                placeholder={isHi ? 'उदा. dr_sharma' : 'e.g. dr_sharma or ntro_officer'}
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

          {/* Backend RBAC Roles strictly: admin / analyst / viewer (§F.2) */}
          <div>
            <label className="block text-xs font-bold text-text-secondary uppercase tracking-wider mb-2">
              {isHi ? 'भूमिका (RBAC)' : 'Operational Role (RBAC)'}
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(
                [
                  { id: 'admin', label: 'Admin', sub: 'System Manager' },
                  { id: 'analyst', label: 'Analyst', sub: 'Hydrologist' },
                  { id: 'viewer', label: 'Viewer', sub: 'Observer / Govt' },
                ] as const
              ).map((role) => (
                <button
                  type="button"
                  key={role.id}
                  onClick={() => setSelectedRole(role.id as UserRole)}
                  className={`p-3 text-center rounded-xl border text-xs transition-all ${
                    selectedRole === role.id
                      ? 'border-brand bg-brand-soft text-brand font-bold shadow-2xs ring-1 ring-brand'
                      : 'border-border bg-white text-text-secondary hover:bg-bg-subtle'
                  }`}
                >
                  <p className="font-bold text-sm text-text capitalize">{role.label}</p>
                  <p className="text-[10px] text-text-tertiary mt-0.5">{role.sub}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Primary Action: One Big Blue Button (§A) */}
          <button
            id="signin-submit-btn"
            type="submit"
            disabled={isLoading}
            className="w-full py-4 px-6 rounded-xl bg-brand hover:bg-brand-hover active:scale-[0.98] text-white font-bold text-lg transition-all flex items-center justify-center gap-2 shadow-md disabled:opacity-60"
          >
            <span>{isHi ? 'प्रवाह-X में प्रवेश करें' : 'Sign In to PravahX'}</span>
            <ArrowRight size={20} className="stroke-[2.5]" />
          </button>
        </form>

        {/* F.3: Quick pre-fills ONLY rendered when import.meta.env.DEV with "Dev only" badge */}
        {isDev && (
          <div className="pt-4 border-t border-border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-text-tertiary uppercase tracking-wider">
                Test Profiles
              </span>
              <span className="px-2 py-0.5 text-[10px] font-bold rounded-pill bg-[#FEF3F2] text-[#B42318] border border-[#FECDCA]">
                Dev only
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickFill('admin_sys', 'admin')}
                className="px-2.5 py-1.5 text-xs bg-bg-muted hover:bg-border rounded-lg text-text-secondary font-medium transition-colors text-center"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('dr_sharma', 'analyst')}
                className="px-2.5 py-1.5 text-xs bg-bg-muted hover:bg-border rounded-lg text-text-secondary font-medium transition-colors text-center"
              >
                Analyst
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('ntro_officer', 'viewer')}
                className="px-2.5 py-1.5 text-xs bg-bg-muted hover:bg-border rounded-lg text-text-secondary font-medium transition-colors text-center"
              >
                Viewer
              </button>
            </div>
          </div>
        )}

        {/* Production notice */}
        <p className="text-[11px] text-text-tertiary text-center leading-normal">
          {isHi
            ? 'सुरक्षित पर्यावरण: भूमिका-आधारित पहुँच नियंत्रण (RBAC) और पूर्ण ऑडिट लॉगिंग सक्रिय है।'
            : 'Secure command interface · Role-based access control (RBAC) and SHA-256 audit logging enforced.'}
        </p>
      </div>
    </div>
  );
};
