import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  UserPlus, 
  Key, 
  Trash2, 
  Smartphone
} from 'lucide-react';
import { FeatureId, UserRole } from '../../types';

interface UserAdminPageProps {
  onNavigate?: (feature: FeatureId) => void;
}

interface UserItem {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  mfa_enabled: boolean;
  created_at: string;
  status: 'active' | 'disabled';
}

interface ApiKeyItem {
  id: string;
  name: string;
  key_prefix: string;
  role: string;
  created_at: string;
  last_used: string;
}

export const UserAdminPage: React.FC<UserAdminPageProps> = () => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  const [users, setUsers] = useState<UserItem[]>([
    { id: 'usr_01', username: 'admin_officer', email: 'officer@pravahx.internal', role: 'admin', mfa_enabled: true, created_at: '2026-10-01', status: 'active' },
    { id: 'usr_02', username: 'analyst_sharma', email: 'r.sharma@sdma.gov.in', role: 'analyst', mfa_enabled: true, created_at: '2026-10-15', status: 'active' },
    { id: 'usr_03', username: 'field_viewer_04', email: 'district_eoc@ddma.gov.in', role: 'viewer', mfa_enabled: false, created_at: '2026-10-20', status: 'active' },
  ]);

  const [apiKeys, setApiKeys] = useState<ApiKeyItem[]>([
    { id: 'key_01', name: 'Automated Ingestion Pipeline', key_prefix: 'px_live_9f81a7...', role: 'analyst', created_at: '2026-10-10', last_used: '2026-10-30 08:14 UTC' },
    { id: 'key_02', name: 'Emergency Broadcast Gateway', key_prefix: 'px_live_3c4d5e...', role: 'admin', created_at: '2026-10-18', last_used: '2026-10-29 14:02 UTC' },
  ]);

  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<UserRole>('analyst');

  const [showCreateKeyModal, setShowCreateKeyModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState(false);

  const handleInviteUser = () => {
    if (!inviteEmail.trim()) return;
    setUsers([
      ...users,
      {
        id: `usr_0${users.length + 1}`,
        username: inviteEmail.split('@')[0],
        email: inviteEmail,
        role: inviteRole,
        mfa_enabled: false,
        created_at: new Date().toISOString().split('T')[0],
        status: 'active',
      },
    ]);
    setInviteEmail('');
    setShowInviteModal(false);
  };

  const handleCreateApiKey = () => {
    if (!newKeyName.trim()) return;
    const secret = `px_live_${Math.random().toString(36).substring(2, 14)}${Date.now().toString(36)}`;
    setGeneratedKey(secret);
    setApiKeys([
      ...apiKeys,
      {
        id: `key_0${apiKeys.length + 1}`,
        name: newKeyName,
        key_prefix: `${secret.substring(0, 16)}...`,
        role: 'analyst',
        created_at: new Date().toISOString().split('T')[0],
        last_used: 'Never',
      },
    ]);
    setNewKeyName('');
  };

  const handleRevokeKey = (id: string) => {
    setApiKeys(apiKeys.filter((k) => k.id !== id));
  };

  const handleToggleUserStatus = (id: string) => {
    setUsers(users.map((u) => (u.id === id ? { ...u, status: u.status === 'active' ? 'disabled' : 'active' } : u)));
  };

  return (
    <div className="p-6 sm:p-10 max-w-7xl mx-auto space-y-8">
      {/* 1. Header (Part A3 standard) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-border gap-4">
        <div>
          <div className="text-xs font-mono font-semibold tracking-wider text-text-tertiary uppercase">
            F22 · {isHi ? 'प्रशासन एवं सुरक्षा' : 'ADMIN'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text mt-1">
            {isHi ? 'सिमुलेशन रन शुरू करने या अनुमोदित करने की अनुमति किसके पास है?' : 'Who has permission to launch or approve simulation runs?'}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {isHi 
              ? 'भूमिका-आधारित पहुँच नियंत्रण (RBAC), दो-चरणीय प्रमाणीकरण (MFA) और API कुंजियों का प्रबंधन।' 
              : 'Role-based access control, cryptographic API key issuance, and RFC 6238 TOTP enforcement.'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowInviteModal(true)}
            className="py-2.5 px-4 rounded-xl bg-brand text-white font-semibold text-sm hover:bg-brand/90 active:scale-[0.98] transition-all flex items-center gap-2 shadow-2xs"
          >
            <UserPlus size={16} />
            <span>{isHi ? 'उपयोगकर्ता आमंत्रित करें' : 'Invite User'}</span>
          </button>
        </div>
      </div>

      {/* 2. Users & Roles Management Table */}
      <div className="bg-white rounded-2xl border border-border overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <span className="text-xs font-mono font-bold text-text-tertiary uppercase tracking-wider">
            {isHi ? 'पंजीकृत उपयोगकर्ता' : 'Registered Console Operators'}
          </span>
          <span className="text-xs text-text-tertiary font-mono">
            Source: /api/v1/admin/users
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-bg-subtle/80 text-text-secondary text-xs uppercase font-semibold border-b border-border">
              <tr>
                <th className="py-3 px-6">{isHi ? 'उपयोगकर्ता' : 'User / Identity'}</th>
                <th className="py-3 px-4">{isHi ? 'ईमेल' : 'Email Address'}</th>
                <th className="py-3 px-4">{isHi ? 'भूमिका (RBAC)' : 'Role'}</th>
                <th className="py-3 px-4">{isHi ? 'MFA स्थिति' : '2-Factor MFA'}</th>
                <th className="py-3 px-4">{isHi ? 'स्थिति' : 'Account Status'}</th>
                <th className="py-3 px-6 text-right">{isHi ? 'कार्रवाई' : 'Action'}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {users.map((u) => (
                <tr key={u.id} className="h-[52px] hover:bg-bg-subtle/50 transition-colors">
                  <td className="py-3 px-6 font-semibold text-text">{u.username}</td>
                  <td className="py-3 px-4 text-xs font-mono text-text-secondary">{u.email}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold uppercase ${
                      u.role === 'admin'
                        ? 'bg-status-fail-soft text-status-fail'
                        : u.role === 'analyst'
                        ? 'bg-brand-soft text-brand'
                        : 'bg-bg-muted text-text-secondary'
                    }`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded-pill text-[10px] font-bold border inline-flex items-center gap-1 ${
                      u.mfa_enabled
                        ? 'bg-[#ECFDF3] text-[#067647] border-[#D1FADF]'
                        : 'bg-[#FFFAEB] text-[#B54708] border-[#FEDF89]'
                    }`}>
                      <Smartphone size={11} />
                      <span>{u.mfa_enabled ? 'TOTP ENABLED' : 'PENDING'}</span>
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded-pill text-[10px] font-bold border ${
                      u.status === 'active'
                        ? 'bg-[#ECFDF3] text-[#067647] border-[#D1FADF]'
                        : 'bg-[#F2F4F7] text-[#475467] border-[#D0D5DD]'
                    }`}>
                      {u.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-3 px-6 text-right">
                    <button
                      onClick={() => handleToggleUserStatus(u.id)}
                      className="text-xs font-medium text-text-secondary hover:text-text hover:underline"
                    >
                      {u.status === 'active' ? (isHi ? 'अक्षम करें' : 'Disable') : (isHi ? 'सक्षम करें' : 'Enable')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. API Keys Management Section */}
      <div className="bg-white rounded-2xl border border-border p-6 space-y-4 shadow-xs">
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Key size={18} className="text-brand" />
            <h2 className="text-xs font-mono font-bold text-text-tertiary uppercase tracking-wider">
              {isHi ? 'प्रोग्रामेटिक API कुंजियाँ' : 'Programmatic Integration API Keys'}
            </h2>
          </div>
          <button
            onClick={() => setShowCreateKeyModal(true)}
            className="py-1.5 px-4 rounded-xl bg-brand text-white text-xs font-semibold hover:bg-brand/90 transition-all flex items-center gap-1.5"
          >
            <span>{isHi ? 'नई कुंजी बनाएँ' : 'Generate API Key'}</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-bg-subtle/80 text-text-secondary text-xs uppercase font-semibold border-b border-border">
              <tr>
                <th className="py-2.5 px-4">{isHi ? 'कुंजी का नाम' : 'Key Label'}</th>
                <th className="py-2.5 px-4">{isHi ? 'कुंजी उपसर्ग' : 'Token Prefix'}</th>
                <th className="py-2.5 px-4">{isHi ? 'भूमिका का दायरा' : 'Scope'}</th>
                <th className="py-2.5 px-4">{isHi ? 'अंतिम उपयोग' : 'Last Ingested'}</th>
                <th className="py-2.5 px-4 text-right">{isHi ? 'रद्द करें' : 'Revoke'}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {apiKeys.map((k) => (
                <tr key={k.id} className="h-12 hover:bg-bg-subtle/50 transition-colors">
                  <td className="py-2.5 px-4 font-semibold text-text">{k.name}</td>
                  <td className="py-2.5 px-4 font-mono text-xs text-text-secondary">{k.key_prefix}</td>
                  <td className="py-2.5 px-4 font-mono text-xs text-text-tertiary uppercase">{k.role}</td>
                  <td className="py-2.5 px-4 font-mono text-xs text-text-secondary">{k.last_used}</td>
                  <td className="py-2.5 px-4 text-right">
                    <button
                      onClick={() => handleRevokeKey(k.id)}
                      className="p-1 rounded text-text-tertiary hover:text-status-fail transition-colors"
                      title="Revoke key"
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

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-[#0B1220]/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl border border-border max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-base font-bold text-text">{isHi ? 'नया ऑपरेटर आमंत्रित करें' : 'Invite Platform Operator'}</h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-text mb-1">Official Email Address</label>
                <input
                  type="email"
                  placeholder="operator@sdma.gov.in"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="w-full py-2 px-3 rounded-lg border border-border font-medium focus:ring-2 focus:ring-brand/30"
                />
              </div>
              <div>
                <label className="block font-semibold text-text mb-1">Assigned RBAC Role</label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value as UserRole)}
                  className="w-full py-2 px-3 rounded-lg border border-border font-medium focus:ring-2 focus:ring-brand/30"
                >
                  <option value="analyst">Analyst (Can configure and execute runs)</option>
                  <option value="viewer">Viewer (Read-only results exploration)</option>
                  <option value="admin">Admin (Full administrative & audit authority)</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowInviteModal(false)}
                className="py-2 px-4 rounded-xl border border-border text-xs font-semibold hover:bg-bg-subtle"
              >
                Cancel
              </button>
              <button
                onClick={handleInviteUser}
                className="py-2 px-5 rounded-xl bg-brand text-white text-xs font-semibold hover:bg-brand/90"
              >
                Send Invite
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Key Modal */}
      {showCreateKeyModal && (
        <div className="fixed inset-0 bg-[#0B1220]/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl border border-border max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-base font-bold text-text">{isHi ? 'नई गुप्त API कुंजी' : 'Issue Secret API Key'}</h3>
            {!generatedKey ? (
              <div className="space-y-3 text-xs">
                <div>
                  <label className="block font-semibold text-text mb-1">Key Label</label>
                  <input
                    type="text"
                    placeholder="e.g. Automated Basin Telemetry"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    className="w-full py-2 px-3 rounded-lg border border-border font-medium focus:ring-2 focus:ring-brand/30"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    onClick={() => setShowCreateKeyModal(false)}
                    className="py-2 px-4 rounded-xl border border-border text-xs font-semibold hover:bg-bg-subtle"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateApiKey}
                    className="py-2 px-5 rounded-xl bg-brand text-white text-xs font-semibold hover:bg-brand/90"
                  >
                    Generate Key
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4 text-xs">
                <div className="p-3 rounded-xl bg-[#FEF3F2] border border-[#FECDCA] text-[#B42318]">
                  <strong>Warning:</strong> This key will only be displayed once. Copy and store it securely.
                </div>
                <div className="p-3 rounded-xl bg-bg-subtle border border-border font-mono text-xs flex items-center justify-between">
                  <span className="truncate">{generatedKey}</span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(generatedKey);
                      setCopiedKey(true);
                      setTimeout(() => setCopiedKey(false), 2000);
                    }}
                    className="text-brand font-bold shrink-0 ml-2"
                  >
                    {copiedKey ? 'Copied!' : 'Copy'}
                  </button>
                </div>
                <div className="flex justify-end pt-2">
                  <button
                    onClick={() => {
                      setShowCreateKeyModal(false);
                      setGeneratedKey(null);
                    }}
                    className="py-2 px-5 rounded-xl bg-brand text-white text-xs font-semibold hover:bg-brand/90"
                  >
                    Done
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
