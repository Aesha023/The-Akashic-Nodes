import React, { createContext, useContext, useState, useEffect } from 'react';

interface DemoModeContextType {
  isPresentationMode: boolean; // true = Presentation (includes DEMO content), false = Operational (only REAL)
  setPresentationMode: (value: boolean) => void;
  togglePresentationMode: () => void;
}

const DemoModeContext = createContext<DemoModeContextType | undefined>(undefined);

export const DemoModeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isPresentationMode, setIsPresentationMode] = useState<boolean>(() => {
    const saved = localStorage.getItem('pravahx_presentation_mode');
    // Default to Presentation mode (Demo ON) as per spec, toggleable per user
    return saved !== null ? saved === 'true' : true;
  });

  useEffect(() => {
    localStorage.setItem('pravahx_presentation_mode', String(isPresentationMode));
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
