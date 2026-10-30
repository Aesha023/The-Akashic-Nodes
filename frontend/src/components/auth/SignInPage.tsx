import React, { useState } from 'react';
import { 
  KeyRound, 
  Lock, 
  User as UserIcon, 
  CheckCircle, 
  AlertCircle, 
  Waves,
  ArrowRight
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../common/Button';
import { UserRole, FeatureId } from '../../types';

interface SignInPageProps {
  onSuccess: (feature: FeatureId) => void;
}

export const SignInPage: React.FC<SignInPageProps> = ({ onSuccess }) => {
  const { t } = useTranslation();
  const { login, isAuthenticated, user, logout } = useAuth();

  const [username, setUsername] = useState('dr_sharma');
  const [password, setPassword] = useState('pravahx2026!');
  const [totpCode, setTotpCode] = useState('482910');
  const [selectedRole, setSelectedRole] = useState<UserRole>('hydrologist');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    setTimeout(() => {
      if (!username || !password) {
        setError('Please provide both username and password.');
        setIsLoading(false);
        return;
      }

      login(username, selectedRole, 'jwt_token_real_session');
      setIsLoading(false);
      onSuccess('f01_mission_control');
    }, 400);
  };

  const handleQuickFill = (name: string, role: UserRole) => {
    setUsername(name);
    setPassword('pravahx2026!');
    setSelectedRole(role);
    setTotpCode('591024');
  };

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-bg-subtle">
      <div className="max-w-md w-full space-y-8 bg-surface p-8 rounded-2xl border border-border shadow-lg">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex w-12 h-12 rounded-xl bg-brand items-center justify-center text-white shadow-sm mb-2">
            <Waves size={26} className="stroke-[2.5]" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-text">
            {t('auth.signInTitle')}
          </h2>
          <p className="text-xs text-text-secondary">
            {t('auth.signInSubtitle')}
          </p>
        </div>

        {/* Existing Active Session Alert if any */}
        {isAuthenticated && user && (
          <div className="p-3.5 rounded-lg bg-bg-muted border border-border flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <CheckCircle size={15} className="text-status-pass shrink-0" />
              <span>
                Signed in as <strong className="text-text">{user.username}</strong> ({user.role})
              </span>
            </div>
            <button
              onClick={logout}
              className="text-status-fail hover:underline font-semibold"
            >
              Sign out
            </button>
          </div>
        )}

        {/* Error Notification */}
        {error && (
          <div className="p-3 rounded-lg bg-[#FEF3F2] border border-[#FECDCA] text-status-fail text-xs flex items-center gap-2">
            <AlertCircle size={15} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1">
              {t('auth.usernameLabel')}
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-text-tertiary">
                <UserIcon size={16} />
              </span>
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm bg-white border border-border-strong rounded-lg text-text focus:outline-none focus:ring-2 focus:ring-brand shadow-2xs"
                placeholder="e.g. dr_sharma"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1">
              {t('auth.passwordLabel')}
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-text-tertiary">
                <Lock size={16} />
              </span>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm bg-white border border-border-strong rounded-lg text-text focus:outline-none focus:ring-2 focus:ring-brand shadow-2xs"
                placeholder="••••••••••••"
              />
            </div>
          </div>

          {/* TOTP MFA Step */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-text-secondary uppercase tracking-wider flex items-center gap-1">
                <KeyRound size={13} className="text-brand" />
                <span>{t('auth.totpLabel')}</span>
              </label>
              <span className="text-[10px] text-brand font-medium">MFA Required</span>
            </div>
            <input
              type="text"
              maxLength={6}
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value)}
              className="w-full px-3 py-2 text-sm font-mono tracking-widest text-center bg-white border border-border-strong rounded-lg text-text focus:outline-none focus:ring-2 focus:ring-brand shadow-2xs"
              placeholder="000000"
            />
            <p className="text-[10px] text-text-tertiary mt-1">
              {t('auth.totpHint')}
            </p>
          </div>

          {/* Role Selection for RBAC testing */}
          <div>
            <label className="block text-xs font-semibold text-text-tertiary uppercase tracking-wider mb-1.5">
              Assigned Operational Role
            </label>
            <div className="grid grid-cols-2 gap-2">
              {(
                [
                  { id: 'hydrologist', name: 'Lead Hydrologist' },
                  { id: 'emergency_commander', name: 'Incident Commander' },
                  { id: 'admin', name: 'System Administrator' },
                  { id: 'viewer', name: 'Public / Field Observer' },
                ] as const
              ).map((role) => (
                <button
                  type="button"
                  key={role.id}
                  onClick={() => setSelectedRole(role.id)}
                  className={`p-2 text-left rounded-md border text-xs transition-colors ${
                    selectedRole === role.id
                      ? 'border-brand bg-brand-soft text-brand font-semibold shadow-2xs'
                      : 'border-border bg-white text-text-secondary hover:bg-bg-subtle'
                  }`}
                >
                  <p className="font-medium truncate">{role.name}</p>
                  <p className="text-[10px] text-text-tertiary uppercase">{role.id}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Submit */}
          <Button
            type="submit"
            variant="primary"
            size="md"
            isLoading={isLoading}
            className="w-full mt-4 shadow-sm"
            icon={<ArrowRight size={16} />}
            iconPosition="right"
          >
            {t('auth.submitBtn')}
          </Button>
        </form>

        {/* Quick Demo Pre-fills */}
        <div className="pt-4 border-t border-border">
          <p className="text-[11px] font-semibold text-text-tertiary uppercase tracking-wider mb-2 text-center">
            Reviewer Quick Profiles
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2">
            <button
              onClick={() => handleQuickFill('dr_sharma', 'hydrologist')}
              className="px-2.5 py-1 text-xs bg-bg-muted hover:bg-border rounded text-text-secondary transition-colors"
            >
              Dr. Sharma (Hydrologist)
            </button>
            <button
              onClick={() => handleQuickFill('cmdr_patel', 'emergency_commander')}
              className="px-2.5 py-1 text-xs bg-bg-muted hover:bg-border rounded text-text-secondary transition-colors"
            >
              Cmdr. Patel (HADR)
            </button>
            <button
              onClick={() => handleQuickFill('admin_sys', 'admin')}
              className="px-2.5 py-1 text-xs bg-bg-muted hover:bg-border rounded text-text-secondary transition-colors"
            >
              Admin Sys
            </button>
          </div>
        </div>

        {/* Production notice */}
        <p className="text-[10px] text-text-tertiary text-center leading-tight">
          {t('auth.defaultNotice')}
        </p>
      </div>
    </div>
  );
};
