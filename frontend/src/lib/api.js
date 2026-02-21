// API utility to handle demo mode
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export function getFetchOptions(options = {}) {
  const demoMode = localStorage.getItem('demoMode') === 'true';
  
  const headers = {
    ...options.headers,
  };
  
  if (demoMode) {
    headers['X-Demo-Mode'] = 'true';
  }
  
  return {
    credentials: demoMode ? 'omit' : 'include',
    ...options,
    headers,
  };
}

export async function apiFetch(url, options = {}) {
  return fetch(url, getFetchOptions(options));
}
