import React, { useState, useEffect } from 'react';
import { TreePine, Users, ClipboardCheck, TrendingUp, Wallet, Leaf, ArrowUpRight, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const statusColors = {
  pending: 'bg-amber-50 text-amber-700 border-amber-200',
  approved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  rejected: 'bg-red-50 text-red-700 border-red-200',
  needs_info: 'bg-blue-50 text-blue-700 border-blue-200',
};

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API}/dashboard/stats`, { credentials: 'include' });
        if (res.ok) setStats(await res.json());
      } catch {}
      setLoading(false);
    })();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-[#1A4D2E] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const metrics = [
    { label: 'Projects', value: stats?.total_projects || 0, icon: TreePine, color: '#1A4D2E', bg: 'bg-emerald-50' },
    { label: 'Farmers Enrolled', value: stats?.total_farmers || 0, icon: Users, color: '#B45309', bg: 'bg-amber-50' },
    { label: 'Total Activities', value: stats?.total_activities || 0, icon: ClipboardCheck, color: '#1A4D2E', bg: 'bg-emerald-50' },
    { label: 'Pending Verification', value: stats?.pending_verification || 0, icon: Clock, color: '#D97706', bg: 'bg-amber-50' },
    { label: 'Approved Trees', value: stats?.approved_trees || 0, icon: Leaf, color: '#059669', bg: 'bg-green-50' },
    { label: 'Est. tCO2e', value: stats?.estimated_credits?.toFixed(2) || '0.00', icon: TrendingUp, color: '#1A4D2E', bg: 'bg-emerald-50', subtitle: 'Estimated units' },
    { label: 'Total Payout', value: `₹${(stats?.total_payout || 0).toLocaleString('en-IN')}`, icon: Wallet, color: '#B45309', bg: 'bg-amber-50' },
    { label: 'Verified Activities', value: stats?.verified_activities || 0, icon: ArrowUpRight, color: '#059669', bg: 'bg-green-50' },
  ];

  return (
    <div data-testid="dashboard-page" className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-[#1F2937] tracking-tight" style={{ fontFamily: 'Manrope, sans-serif' }}>Dashboard</h1>
        <p className="text-[#6B7280] mt-1">Overview of your tree plantation projects</p>
      </div>

      {/* Bento Grid Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-5" data-testid="metrics-grid">
        {metrics.map((m, i) => (
          <Card key={i} className="bg-white border border-gray-100 rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:shadow-md transition-shadow duration-300">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs font-medium text-[#6B7280] uppercase tracking-wider">{m.label}</p>
                  <p className="text-2xl font-bold mt-1.5" style={{ fontFamily: 'Manrope, sans-serif', color: m.color }}>{m.value}</p>
                  {m.subtitle && <p className="text-[10px] text-[#9CA3AF] mt-0.5 italic">{m.subtitle}</p>}
                </div>
                <div className={`${m.bg} p-2 rounded-lg`}>
                  <m.icon className="w-4.5 h-4.5" style={{ color: m.color }} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3" data-testid="disclaimer-banner">
        <Leaf className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
        <div>
          <p className="text-sm font-medium text-amber-800">Estimated Units — Not Issued Credits</p>
          <p className="text-xs text-amber-600 mt-0.5">All carbon values shown are estimates based on rule-of-thumb calculations. Final issuance depends on verification + registry rules.</p>
        </div>
      </div>

      {/* Recent Claims */}
      <Card className="bg-white border border-gray-100 rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg font-semibold" style={{ fontFamily: 'Manrope, sans-serif' }}>Recent Claims</CardTitle>
        </CardHeader>
        <CardContent>
          {stats?.recent_claims?.length > 0 ? (
            <div className="space-y-3">
              {stats.recent_claims.map((claim) => (
                <div key={claim.claim_id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50/50 hover:bg-gray-100/50 transition-colors" data-testid={`recent-claim-${claim.claim_id}`}>
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 bg-emerald-100 rounded-full flex items-center justify-center">
                      <Leaf className="w-4 h-4 text-[#1A4D2E]" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-[#1F2937]">{claim.farmer_name || 'Unknown'}</p>
                      <p className="text-xs text-[#6B7280]">{claim.tree_count} {claim.species} trees</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-[#1A4D2E]" style={{ fontFamily: 'JetBrains Mono, monospace' }}>₹{claim.estimated_payout}</span>
                    <Badge className={`text-[10px] border ${statusColors[claim.status] || statusColors.pending}`}>{claim.status}</Badge>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-[#6B7280]">
              <ClipboardCheck className="w-10 h-10 mx-auto mb-3 text-gray-300" />
              <p className="text-sm">No claims yet. Create a program and onboard farmers to get started.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
