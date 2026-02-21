import React, { createContext, useContext, useState, useEffect } from 'react';

const DemoModeContext = createContext();

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export function DemoModeProvider({ children }) {
  const [demoMode, setDemoMode] = useState(() => {
    // Check localStorage for saved preference
    return localStorage.getItem('demoMode') === 'true';
  });
  const [demoUser, setDemoUser] = useState(null);

  // Fetch demo user when demo mode is enabled
  useEffect(() => {
    if (demoMode) {
      fetchDemoUser();
    } else {
      setDemoUser(null);
    }
  }, [demoMode]);

  const fetchDemoUser = async () => {
    try {
      const res = await fetch(`${API}/auth/demo-user`);
      if (res.ok) {
        const user = await res.json();
        setDemoUser(user);
      }
    } catch (error) {
      console.error('Failed to fetch demo user:', error);
    }
  };

  const toggleDemoMode = () => {
    const newMode = !demoMode;
    setDemoMode(newMode);
    localStorage.setItem('demoMode', newMode.toString());
    
    // Reload page to fetch fresh data
    if (newMode) {
      window.location.reload();
    }
  };

  const value = {
    demoMode,
    demoUser,
    toggleDemoMode,
  };

  return (
    <DemoModeContext.Provider value={value}>
      {children}
    </DemoModeContext.Provider>
  );
}

export function useDemoMode() {
  const context = useContext(DemoModeContext);
  if (!context) {
    throw new Error('useDemoMode must be used within DemoModeProvider');
  }
  return context;
}
