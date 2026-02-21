import React from 'react';
import { TreePine, Eye } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useNavigate } from 'react-router-dom';

export default function LoginPage() {
  const navigate = useNavigate();
  
  const handleLogin = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const handleDemoMode = () => {
    localStorage.setItem('demoMode', 'true');
    navigate('/dashboard');
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-[#FDFCF8] flex" data-testid="login-page">
      {/* Left panel - Hero */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: 'url(https://images.pexels.com/photos/29803637/pexels-photo-29803637.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940)' }}
        />
        <div className="absolute inset-0 bg-[#1A4D2E]/70" />
        <div className="relative z-10 flex flex-col justify-between p-12 text-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
              <TreePine className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight" style={{ fontFamily: 'Manrope, sans-serif' }}>VanaLedger</span>
          </div>
          <div className="max-w-md">
            <h1 className="text-4xl sm:text-5xl font-extrabold leading-tight mb-6" style={{ fontFamily: 'Manrope, sans-serif' }}>
              From Sapling to Carbon Credit
            </h1>
            <p className="text-lg text-white/80 leading-relaxed">
              Manage tree plantation programs, onboard farmers, track claims, and generate MRV-ready evidence packs for carbon credit issuance.
            </p>
            <div className="mt-8 flex gap-6">
              <div>
                <div className="text-2xl font-bold">500+</div>
                <div className="text-sm text-white/60">Trees Tracked</div>
              </div>
              <div>
                <div className="text-2xl font-bold">120+</div>
                <div className="text-sm text-white/60">Farmers Onboarded</div>
              </div>
              <div>
                <div className="text-2xl font-bold">12.5</div>
                <div className="text-sm text-white/60">Est. tCO2e</div>
              </div>
            </div>
          </div>
          <p className="text-xs text-white/40">Estimated units — not issued credits. Final issuance depends on verification + registry rules.</p>
        </div>
      </div>

      {/* Right panel - Login */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-2.5 mb-12">
            <div className="w-9 h-9 bg-[#1A4D2E] rounded-lg flex items-center justify-center">
              <TreePine className="w-4.5 h-4.5 text-white" />
            </div>
            <span className="text-lg font-bold text-[#1A4D2E] tracking-tight" style={{ fontFamily: 'Manrope, sans-serif' }}>VanaLedger</span>
          </div>

          <h2 className="text-2xl font-bold text-[#1F2937] mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>Welcome back</h2>
          <p className="text-[#6B7280] mb-8">Sign in to manage your tree plantation programs.</p>

          <Button
            onClick={handleLogin}
            data-testid="google-login-btn"
            className="w-full bg-[#1A4D2E] text-white hover:bg-[#143C24] shadow-sm font-medium px-6 py-6 rounded-lg transition-all active:scale-[0.98] text-base flex items-center justify-center gap-3"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
              <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            Continue with Google
          </Button>

          <p className="mt-6 text-xs text-center text-[#6B7280]">
            By signing in, you agree to our terms of service and privacy policy.
          </p>
        </div>
      </div>
    </div>
  );
}
