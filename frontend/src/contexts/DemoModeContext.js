import React, { createContext, useContext, useState, useEffect } from 'react';

const DemoModeContext = createContext();

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export function DemoModeProvider({ children }) {
  const [demoMode, setDemoMode] = useState(() => {
    // Check localStorage for saved preference
    const isDemoMode = localStorage.getItem('demoMode') === 'true';
    
    // Set cookie if demo mode is active
    if (isDemoMode) {
      document.cookie = 'demo_mode=true; path=/; max-age=86400';
    }
    
    return isDemoMode;
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
    
    // Set/remove demo mode cookie for API requests
    if (newMode) {
      document.cookie = 'demo_mode=true; path=/; max-age=86400'; // 24 hours
    } else {
      document.cookie = 'demo_mode=; path=/; max-age=0'; // Delete cookie
    }
    
    // Reload page to fetch fresh data
    window.location.reload();
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
