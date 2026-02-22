import React, { useState, useEffect } from 'react';
import { Wallet, Download, Search } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function LedgerPage() {
  const [ledger, setLedger] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API}/ledger`, { credentials: 'include' });
        if (res.ok) setLedger(await res.json());
      } catch {}
      setLoading(false);
    })();
  }, []);

  const totals = ledger.reduce((acc, e) => ({
    trees: acc.trees + (e.approved_trees_total || 0),
    credits: acc.credits + (e.approved_credits_total || 0),
    payable: acc.payable + (e.payable_amount || 0),
    paid: acc.paid + (e.paid_amount || 0),
  }), { trees: 0, credits: 0, payable: 0, paid: 0 });

  const filtered = ledger.filter(e =>
    !search || e.farmer_name?.toLowerCase().includes(search.toLowerCase()) || e.farmer_phone?.includes(search)
  );

  const exportPayoutCSV = () => {
    window.open(`${API}/export/payout-csv`, '_blank');
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-4 border-[#1A4D2E] border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div data-testid="ledger-page" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1F2937] tracking-tight" style={{ fontFamily: 'Manrope, sans-serif' }}>Payout Ledger</h1>
          <p className="text-[#6B7280] mt-1">Farmer-wise balance and payout tracking</p>
        </div>
        <Button onClick={exportPayoutCSV} data-testid="export-payout-csv-btn" className="bg-[#1A4D2E] text-white hover:bg-[#143C24] shadow-sm font-medium px-5 py-2.5 rounded-lg transition-all active:scale-95">
          <Download className="w-4 h-4 mr-2" /> Export CSV
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4" data-testid="ledger-summary">
        <Card className="bg-white border border-gray-100 rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
          <CardContent className="p-5">
            <p className="text-xs font-medium text-[#6B7280] uppercase tracking-wider">Total Farmers</p>
            <p className="text-2xl font-bold text-[#1A4D2E] mt-1" style={{ fontFamily: 'Manrope, sans-serif' }}>{ledger.length}</p>
          </CardContent>
        </Card>
        <Card className="bg-white border border-gray-100 rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
          <CardContent className="p-5">
            <p className="text-xs font-medium text-[#6B7280] uppercase tracking-wider">Approved Trees</p>
            <p className="text-2xl font-bold text-[#059669] mt-1" style={{ fontFamily: 'Manrope, sans-serif' }}>{totals.trees.toLocaleString('en-IN')}</p>
          </CardContent>
        </Card>
        <Card className="bg-white border border-gray-100 rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
          <CardContent className="p-5">
            <p className="text-xs font-medium text-[#6B7280] uppercase tracking-wider">Est. tCO2e</p>
            <p className="text-2xl font-bold text-[#1A4D2E] mt-1 font-mono" style={{ fontFamily: 'Manrope, sans-serif' }}>{totals.credits.toFixed(4)}</p>
            <p className="text-[10px] text-[#9CA3AF] italic">Estimated units</p>
          </CardContent>
        </Card>
        <Card className="bg-white border border-gray-100 rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
          <CardContent className="p-5">
            <p className="text-xs font-medium text-[#6B7280] uppercase tracking-wider">Total Payable</p>
            <p className="text-2xl font-bold text-[#B45309] mt-1" style={{ fontFamily: 'Manrope, sans-serif' }}>₹{totals.payable.toLocaleString('en-IN')}</p>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7280]" />
        <Input data-testid="ledger-search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search farmer..." className="pl-9" />
      </div>

      {/* Table */}
      <Card className="bg-white border border-gray-100 rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50/50 hover:bg-gray-50/50">
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-[#6B7280]">Farmer</TableHead>
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-[#6B7280]">Project</TableHead>
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-[#6B7280]">UPI ID</TableHead>
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-[#6B7280] text-right">Approved Trees</TableHead>
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-[#6B7280] text-right">Est. tCO2e</TableHead>
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-[#6B7280] text-right">Payable (₹)</TableHead>
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-[#6B7280] text-right">Paid (₹)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 ? (
                <TableRow><TableCell colSpan={7} className="text-center py-8 text-[#6B7280]">No ledger entries yet. Approve claims to see payouts.</TableCell></TableRow>
              ) : filtered.map((e) => (
                <TableRow key={e.ledger_id || e.farmer_id} className="hover:bg-gray-50/50 transition-colors" data-testid={`ledger-row-${e.farmer_id}`}>
                  <TableCell>
                    <div>
                      <p className="text-sm font-medium text-[#1F2937]">{e.farmer_name}</p>
                      <p className="text-xs text-[#6B7280]">{e.farmer_phone}</p>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-[#6B7280]">
                    <Badge variant="outline" className="text-xs">{e.project_name || '-'}</Badge>
                  </TableCell>
                  <TableCell className="text-xs font-mono text-[#6B7280]">{e.upi_id || '-'}</TableCell>
                  <TableCell className="text-right text-sm font-medium">{e.approved_trees_total}</TableCell>
                  <TableCell className="text-right text-sm font-mono text-[#1A4D2E]">{e.approved_credits_total?.toFixed(4)}</TableCell>
                  <TableCell className="text-right text-sm font-mono font-medium text-[#B45309]">₹{e.payable_amount?.toLocaleString('en-IN')}</TableCell>
                  <TableCell className="text-right text-sm font-mono text-[#059669]">₹{e.paid_amount?.toLocaleString('en-IN')}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <p className="text-xs text-[#9CA3AF] text-center italic">
        All values shown are estimates based on rule-of-thumb calculations. Final issuance depends on verification + registry rules.
      </p>
    </div>
  );
}
