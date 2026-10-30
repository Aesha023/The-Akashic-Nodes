import React, { createContext, useContext, useState, useEffect } from 'react';

interface DemoModeContextType {
  isPresentationMode: boolean; // true = Presentation (includes DEMO content), false = Operational (only REAL)
  setPresentationMode: (value: boolean) => void;
  togglePresentationMode: () => void;
}

const DemoModeContext = createContext<DemoModeContextType | undefined>(undefined);

export const DemoModeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isPresentationMode, setIsPresentationMode] = useState<boolean>(() => {
    // 1. Check local storage fallback first
    const saved = localStorage.getItem('pravahx_presentation_mode');
    if (saved !== null) {
      return saved === 'true';
    }
    // 2. Check cached auth user preferences if available
    const savedUser = localStorage.getItem('pravahx_auth_user');
    if (savedUser) {
      try {
        const u = JSON.parse(savedUser);
        if (typeof u.presentation_mode === 'boolean') {
          return u.presentation_mode;
        }
      } catch (e) {
        // ignore
      }
    }
    // Default to true (Presentation mode)
    return true;
  });

  // Sync to backend per user + localStorage fallback (Requirement F7)
  useEffect(() => {
    localStorage.setItem('pravahx_presentation_mode', String(isPresentationMode));

    const savedUser = localStorage.getItem('pravahx_auth_user');
    if (savedUser) {
      try {
        const u = JSON.parse(savedUser);
        u.presentation_mode = isPresentationMode;
        localStorage.setItem('pravahx_auth_user', JSON.stringify(u));

        // Fire-and-forget sync to backend API
        if (u.token) {
          fetch('/api/v1/auth/me/preferences', {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${u.token}`,
            },
            body: JSON.stringify({ presentation_mode: isPresentationMode }),
          }).catch(() => {
            // Fallback to localStorage remains seamless if offline
          });
        }
      } catch (e) {
        // Fallback intact
      }
    }
  }, [isPresentationMode]);

  const togglePresentationMode = () => {
    setIsPresentationMode((prev) => !prev);
  };

  return (
    <DemoModeContext.Provider
      value={{
        isPresentationMode,
        setPresentationMode: setIsPresentationMode,
        togglePresentationMode,
      }}
    >
      {children}
    </DemoModeContext.Provider>
  );
};

export const useDemoMode = (): DemoModeContextType => {
  const context = useContext(DemoModeContext);
  if (!context) {
    throw new Error('useDemoMode must be used within a DemoModeProvider');
  }
  return context;
};
