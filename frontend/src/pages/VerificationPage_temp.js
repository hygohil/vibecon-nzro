import React, { useState, useEffect } from 'react';
import { ClipboardCheck, Check, X, MessageCircle, MapPin, Image as ImageIcon, TreePine, Plus, Eye } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const statusColors = {
  pending: 'bg-amber-50 text-amber-700 border-amber-200',
  approved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  rejected: 'bg-red-50 text-red-700 border-red-200',
  needs_info: 'bg-blue-50 text-blue-700 border-blue-200',
};

export default function ClaimsPage() {
  const [claims, setClaims] = useState([]);
  const [programs, setPrograms] = useState([]);
  const [farmers, setFarmers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [verifierNotes, setVerifierNotes] = useState('');
  const [tab, setTab] = useState('pending');
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    farmer_id: '', program_id: '', tree_count: '', species: 'Neem',
    planted_date: new Date().toISOString().slice(0, 10),
    lat: '', lng: '', photo_urls: ['', ''], notes: ''
  });

  const fetchData = async () => {
    try {
      const [cRes, pRes, fRes] = await Promise.all([
        fetch(`${API}/claims`, { credentials: 'include' }),
        fetch(`${API}/programs`, { credentials: 'include' }),
        fetch(`${API}/farmers`, { credentials: 'include' }),
      ]);
      if (cRes.ok) setClaims(await cRes.json());
      if (pRes.ok) setPrograms(await pRes.json());
      if (fRes.ok) setFarmers(await fRes.json());
    } catch {}
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  const handleAction = async (claimId, action) => {
    try {
      const res = await fetch(`${API}/claims/${claimId}/action`, {
        method: 'PUT', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, verifier_notes: verifierNotes }),
      });
      if (res.ok) {
        toast.success(`Claim ${action === 'approve' ? 'approved' : action === 'reject' ? 'rejected' : 'updated'}`);
        setSelectedClaim(null);
        setVerifierNotes('');
        fetchData();
      }
    } catch { toast.error('Action failed'); }
  };

  const handleCreateClaim = async () => {
    if (!form.farmer_id || !form.program_id || !form.tree_count) {
      toast.error('Fill required fields'); return;
    }
    try {
      const photos = form.photo_urls.filter(u => u.trim());
      const res = await fetch(`${API}/claims`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          tree_count: Number(form.tree_count),
          lat: form.lat ? Number(form.lat) : null,
          lng: form.lng ? Number(form.lng) : null,
          photo_urls: photos,
        }),
      });
      if (res.ok) {
        toast.success('Claim submitted');
        setShowCreate(false);
        fetchData();
        setForm({ farmer_id: '', program_id: '', tree_count: '', species: 'Neem', planted_date: new Date().toISOString().slice(0, 10), lat: '', lng: '', photo_urls: ['', ''], notes: '' });
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed');
      }
    } catch { toast.error('Network error'); }
  };

  const filtered = claims.filter(c => tab === 'all' || c.status === tab);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-4 border-[#1A4D2E] border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div data-testid="claims-page" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1F2937] tracking-tight" style={{ fontFamily: 'Manrope, sans-serif' }}>Claims Queue</h1>
          <p className="text-[#6B7280] mt-1">Review and verify plantation claims</p>
        </div>
        <Button onClick={() => setShowCreate(true)} data-testid="create-claim-btn" className="bg-[#1A4D2E] text-white hover:bg-[#143C24] shadow-sm font-medium px-5 py-2.5 rounded-lg transition-all active:scale-95">
          <Plus className="w-4 h-4 mr-2" /> Add Claim
        </Button>
      </div>

      {/* Tabs */}
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="bg-gray-100/50 p-1">
          <TabsTrigger value="pending" data-testid="tab-pending" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
            Pending ({claims.filter(c => c.status === 'pending').length})
          </TabsTrigger>
          <TabsTrigger value="approved" data-testid="tab-approved" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
            Approved ({claims.filter(c => c.status === 'approved').length})
          </TabsTrigger>
          <TabsTrigger value="rejected" data-testid="tab-rejected" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
            Rejected ({claims.filter(c => c.status === 'rejected').length})
          </TabsTrigger>
          <TabsTrigger value="all" data-testid="tab-all" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
            All ({claims.length})
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Claims List */}
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <Card className="bg-white border border-gray-100 rounded-xl shadow-sm">
            <CardContent className="py-12 text-center">
              <ClipboardCheck className="w-10 h-10 mx-auto text-gray-300 mb-3" />
              <p className="text-[#6B7280] text-sm">No {tab !== 'all' ? tab : ''} claims</p>
            </CardContent>
          </Card>
        ) : filtered.map((claim) => (
          <Card key={claim.claim_id} data-testid={`claim-card-${claim.claim_id}`} className="bg-white border border-gray-100 rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:shadow-md transition-shadow duration-300">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div className="flex gap-4 flex-1">
                  {/* Photo preview */}
                  <div className="w-20 h-20 rounded-lg bg-gray-100 flex-shrink-0 overflow-hidden flex items-center justify-center">
                    {claim.photo_urls?.length > 0 && claim.photo_urls[0] ? (
                      <img src={claim.photo_urls[0]} alt="evidence" className="w-full h-full object-cover" />
                    ) : (
                      <ImageIcon className="w-6 h-6 text-gray-300" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-semibold text-[#1F2937]" style={{ fontFamily: 'Manrope, sans-serif' }}>{claim.farmer_name}</h3>
                      <Badge className={`text-[10px] border ${statusColors[claim.status]}`}>{claim.status}</Badge>
                    </div>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-[#6B7280]">
                      <span className="flex items-center gap-1"><TreePine className="w-3 h-3" /> {claim.tree_count} {claim.species}</span>
                      <span>Planted: {claim.planted_date}</span>
                      {claim.lat && claim.lng && (
                        <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {claim.lat.toFixed(4)}, {claim.lng.toFixed(4)}</span>
                      )}
                      <span className="flex items-center gap-1"><ImageIcon className="w-3 h-3" /> {claim.photo_urls?.length || 0} photos</span>
                    </div>
                    <div className="flex gap-4 mt-2">
                      <span className="text-xs"><span className="text-[#6B7280]">Est. Credits:</span> <span className="font-mono text-[#1A4D2E] font-medium">{claim.estimated_credits?.toFixed(4)} tCO2e</span></span>
                      <span className="text-xs"><span className="text-[#6B7280]">Est. Payout:</span> <span className="font-mono text-[#B45309] font-medium">₹{claim.estimated_payout?.toLocaleString('en-IN')}</span></span>
                    </div>
                  </div>
                </div>
                <Button variant="outline" size="sm" onClick={() => { setSelectedClaim(claim); setVerifierNotes(claim.verifier_notes || ''); }} data-testid={`review-claim-${claim.claim_id}`} className="text-xs border-[#1A4D2E]/20 text-[#1A4D2E] hover:bg-emerald-50 ml-3">
                  <Eye className="w-3 h-3 mr-1" /> Review
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Review Dialog */}
      <Dialog open={!!selectedClaim} onOpenChange={() => setSelectedClaim(null)}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto" data-testid="review-claim-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>Review Claim</DialogTitle>
          </DialogHeader>
          {selectedClaim && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="text-[#6B7280]">Farmer:</span> <span className="font-medium">{selectedClaim.farmer_name}</span></div>
                <div><span className="text-[#6B7280]">Phone:</span> <span className="font-mono text-xs">{selectedClaim.farmer_phone}</span></div>
                <div><span className="text-[#6B7280]">Village:</span> <span className="font-medium">{selectedClaim.farmer_village}</span></div>
                <div><span className="text-[#6B7280]">Program:</span> <span className="font-medium">{selectedClaim.program_name}</span></div>
                <div><span className="text-[#6B7280]">Trees:</span> <span className="font-bold text-[#1A4D2E]">{selectedClaim.tree_count} {selectedClaim.species}</span></div>
                <div><span className="text-[#6B7280]">Planted:</span> <span>{selectedClaim.planted_date}</span></div>
                <div><span className="text-[#6B7280]">Est. Credits:</span> <span className="font-mono text-[#1A4D2E]">{selectedClaim.estimated_credits?.toFixed(4)} tCO2e</span></div>
                <div><span className="text-[#6B7280]">Est. Payout:</span> <span className="font-mono text-[#B45309]">₹{selectedClaim.estimated_payout}</span></div>
              </div>

              {/* Location */}
              {selectedClaim.lat && selectedClaim.lng && (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs font-medium text-[#6B7280] mb-1">Location Evidence</p>
                  <p className="text-sm font-mono">{selectedClaim.lat.toFixed(6)}, {selectedClaim.lng.toFixed(6)}</p>
                  <a href={`https://www.google.com/maps?q=${selectedClaim.lat},${selectedClaim.lng}`} target="_blank" rel="noopener noreferrer" className="text-xs text-[#1A4D2E] underline mt-1 inline-block" data-testid="view-on-map-link">View on Google Maps</a>
                </div>
              )}

              {/* Photos */}
              {selectedClaim.photo_urls?.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-[#6B7280] mb-2">Photo Evidence</p>
                  <div className="grid grid-cols-2 gap-3">
                    {selectedClaim.photo_urls.map((url, i) => (
                      url && (
                        <div key={i} className="aspect-video rounded-lg overflow-hidden bg-gray-100 border border-gray-200">
                          <img src={url} alt={`Evidence ${i + 1}`} className="w-full h-full object-cover" />
                        </div>
                      )
                    ))}
                  </div>
                </div>
              )}

              {/* Verifier Notes */}
              <div>
                <Label>Verifier Notes</Label>
                <Textarea data-testid="verifier-notes" value={verifierNotes} onChange={e => setVerifierNotes(e.target.value)} placeholder="Add notes for this claim..." className="mt-1" rows={3} />
              </div>

              {/* Disclaimer */}
              <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 text-xs text-amber-700">
                Estimated units — not issued credits. Final issuance depends on verification + registry rules.
              </div>

              {/* Actions */}
              {selectedClaim.status === 'pending' && (
                <div className="flex gap-3">
                  <Button onClick={() => handleAction(selectedClaim.claim_id, 'approve')} data-testid="approve-claim-btn" className="flex-1 bg-[#1A4D2E] text-white hover:bg-[#143C24]">
                    <Check className="w-4 h-4 mr-2" /> Approve
                  </Button>
                  <Button onClick={() => handleAction(selectedClaim.claim_id, 'reject')} data-testid="reject-claim-btn" variant="outline" className="flex-1 border-red-200 text-red-600 hover:bg-red-50">
                    <X className="w-4 h-4 mr-2" /> Reject
                  </Button>
                  <Button onClick={() => handleAction(selectedClaim.claim_id, 'needs_info')} data-testid="needs-info-btn" variant="outline" className="border-blue-200 text-blue-600 hover:bg-blue-50">
                    <MessageCircle className="w-4 h-4 mr-1" /> Need Info
                  </Button>
                </div>
              )}
              {selectedClaim.status !== 'pending' && (
                <div className="p-3 bg-gray-50 rounded-lg text-center">
                  <Badge className={`${statusColors[selectedClaim.status]} border`}>This claim has been {selectedClaim.status}</Badge>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Create Claim Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="max-w-md max-h-[85vh] overflow-y-auto" data-testid="create-claim-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>Submit Claim</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <Label>Program *</Label>
              <Select value={form.program_id} onValueChange={v => setForm({...form, program_id: v})}>
                <SelectTrigger className="mt-1" data-testid="claim-program-select"><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  {programs.map(p => <SelectItem key={p.program_id} value={p.program_id}>{p.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Farmer *</Label>
              <Select value={form.farmer_id} onValueChange={v => setForm({...form, farmer_id: v})}>
                <SelectTrigger className="mt-1" data-testid="claim-farmer-select"><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  {farmers.filter(f => !form.program_id || f.program_id === form.program_id).map(f => <SelectItem key={f.farmer_id} value={f.farmer_id}>{f.name} ({f.phone})</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Tree Count *</Label>
                <Input data-testid="claim-tree-count" type="number" value={form.tree_count} onChange={e => setForm({...form, tree_count: e.target.value})} className="mt-1" />
              </div>
              <div>
                <Label>Species</Label>
                <Select value={form.species} onValueChange={v => setForm({...form, species: v})}>
                  <SelectTrigger className="mt-1" data-testid="claim-species-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {['Neem', 'Mango', 'Teak', 'Eucalyptus', 'Bamboo', 'Banyan', 'Peepal', 'Moringa', 'Jackfruit'].map(s => (
                      <SelectItem key={s} value={s}>{s}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label>Date Planted</Label>
              <Input data-testid="claim-planted-date" type="date" value={form.planted_date} onChange={e => setForm({...form, planted_date: e.target.value})} className="mt-1" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Latitude</Label>
                <Input data-testid="claim-lat" type="number" step="any" value={form.lat} onChange={e => setForm({...form, lat: e.target.value})} placeholder="e.g., 21.1702" className="mt-1" />
              </div>
              <div>
                <Label>Longitude</Label>
                <Input data-testid="claim-lng" type="number" step="any" value={form.lng} onChange={e => setForm({...form, lng: e.target.value})} placeholder="e.g., 72.8311" className="mt-1" />
              </div>
            </div>
            <div>
              <Label>Photo URL 1 (sapling)</Label>
              <Input data-testid="claim-photo-1" value={form.photo_urls[0]} onChange={e => { const urls = [...form.photo_urls]; urls[0] = e.target.value; setForm({...form, photo_urls: urls}); }} placeholder="https://..." className="mt-1" />
            </div>
            <div>
              <Label>Photo URL 2 (wide shot)</Label>
              <Input data-testid="claim-photo-2" value={form.photo_urls[1]} onChange={e => { const urls = [...form.photo_urls]; urls[1] = e.target.value; setForm({...form, photo_urls: urls}); }} placeholder="https://..." className="mt-1" />
            </div>
            <div>
              <Label>Notes</Label>
              <Textarea data-testid="claim-notes" value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} placeholder="Optional notes" className="mt-1" rows={2} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={handleCreateClaim} data-testid="submit-claim-btn" className="bg-[#1A4D2E] text-white hover:bg-[#143C24]">Submit Claim</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
