import React, { useState, useEffect } from 'react';
import { ClipboardCheck, Check, X, MessageCircle, MapPin, Image as ImageIcon, TreePine, Plus, Eye, ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const statusColors = {
  pending: 'bg-amber-50 text-amber-700 border-amber-200',
  approved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  rejected: 'bg-red-50 text-red-700 border-red-200',
  needs_info: 'bg-blue-50 text-blue-700 border-blue-200',
};

const SURVEY_QUESTIONS = [
  {
    id: 'main_crop',
    label: 'Q1. What is your main crop?',
    options: ['Rice', 'Wheat', 'Maize', 'Cotton', 'Pulses', 'Millets', 'Mixed crops', 'Other'],
  },
  {
    id: 'crops_per_year',
    label: 'Q2. How many crops do you grow per year?',
    options: ['1', '2', '3 or more'],
  },
  {
    id: 'crop_residue',
    label: 'Q3. What do you usually do with crop residue after harvest?',
    options: ['Burn it', 'Remove it', 'Mix it into soil', 'Leave it as mulch'],
  },
  {
    id: 'land_preparation',
    label: 'Q4. How do you usually prepare your land before sowing?',
    options: ['Heavy ploughing (3+ times)', 'Medium ploughing (1–2 times)', 'Light tillage', 'No tillage'],
  },
  {
    id: 'fertilizer_level',
    label: 'Q5. What level of chemical fertilizer do you use?',
    options: ['High', 'Medium', 'Low', 'None'],
  },
  {
    id: 'irrigation_type',
    label: 'Q6. What type of irrigation do you mainly use?',
    options: ['Flood irrigation', 'Sprinkler', 'Drip', 'Rainfed'],
  },
  {
    id: 'compost_usage',
    label: 'Q7. Do you use compost or manure?',
    options: ['Yes', 'No'],
  },
  {
    id: 'water_management',
    label: 'Q8. How is water usually managed in your rice field?',
    options: ['Continuous flooding', 'Intermittent (sometimes dry)', 'Rainfed', 'Not sure'],
  },
  {
    id: 'participation_agreement',
    label: 'Q9. Program Participation Agreement',
    description: 'To participate in the carbon program, I agree to:\n• avoid crop residue burning where required\n• adopt improved farming practices as guided\n• allow farm visits, monitoring, and data collection\n• allow third-party verification\n• provide accurate information',
    options: ['I Agree and want to participate', 'I Do Not Agree'],
  },
];

const emptySurvey = () => SURVEY_QUESTIONS.reduce((acc, q) => ({ ...acc, [q.id]: '' }), {});

export default function VerificationPage() {
  const [activities, setActivities] = useState([]);
  const [projects, setProjects] = useState([]);
  const [farmers, setFarmers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedActivity, setSelectedActivity] = useState(null);
  const [verifierNotes, setVerifierNotes] = useState('');
  const [tab, setTab] = useState('pending');
  const [showCreate, setShowCreate] = useState(false);
  const [surveyExpanded, setSurveyExpanded] = useState(false);
  const [form, setForm] = useState({
    farmer_id: '', project_id: '', tree_count: '', species: 'Neem',
    planted_date: new Date().toISOString().slice(0, 10),
    lat: '', lng: '', photo_urls: ['', ''], notes: ''
  });
  const [survey, setSurvey] = useState(emptySurvey());

  const fetchData = async () => {
    try {
      const [cRes, pRes, fRes] = await Promise.all([
        fetch(`${API}/activities`, { credentials: 'include' }),
        fetch(`${API}/projects`, { credentials: 'include' }),
        fetch(`${API}/farmers?page_size=9999`, { credentials: 'include' }),
      ]);
      if (cRes.ok) setActivities(await cRes.json());
      if (pRes.ok) setProjects(await pRes.json());
      if (fRes.ok) setFarmers(await fRes.json());
    } catch {}
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  const handleAction = async (activityId, action) => {
    try {
      const res = await fetch(`${API}/activities/${activityId}/verify`, {
        method: 'PUT', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, verifier_notes: verifierNotes }),
      });
      if (res.ok) {
        toast.success(`Activity ${action === 'approve' ? 'approved' : action === 'reject' ? 'rejected' : 'updated'}`);
        setSelectedActivity(null);
        setVerifierNotes('');
        fetchData();
      }
    } catch { toast.error('Action failed'); }
  };

  const handleCreateActivity = async () => {
    if (!form.farmer_id || !form.project_id || !form.tree_count) {
      toast.error('Fill required fields'); return;
    }
    // Check if all survey questions are answered
    const unanswered = SURVEY_QUESTIONS.filter(q => !survey[q.id]);
    if (unanswered.length > 0) {
      toast.error(`Please answer all survey questions (${unanswered.length} remaining)`);
      setSurveyExpanded(true);
      return;
    }
    try {
      const photos = form.photo_urls.filter(u => u.trim());
      const res = await fetch(`${API}/activities`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          tree_count: Number(form.tree_count),
          lat: form.lat ? Number(form.lat) : null,
          lng: form.lng ? Number(form.lng) : null,
          photo_urls: photos,
          survey_responses: survey,
        }),
      });
      if (res.ok) {
        toast.success('Activity submitted');
        setShowCreate(false);
        fetchData();
        setForm({ farmer_id: '', project_id: '', tree_count: '', species: 'Neem', planted_date: new Date().toISOString().slice(0, 10), lat: '', lng: '', photo_urls: ['', ''], notes: '' });
        setSurvey(emptySurvey());
        setSurveyExpanded(false);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed');
      }
    } catch { toast.error('Network error'); }
  };

  const filtered = activities.filter(c => tab === 'all' || c.status === tab);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-4 border-[#1A4D2E] border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div data-testid="activities-page" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1F2937] tracking-tight" style={{ fontFamily: 'Manrope, sans-serif' }}>Activities Queue</h1>
          <p className="text-[#6B7280] mt-1">Review and verify plantation activities</p>
        </div>
        <Button onClick={() => setShowCreate(true)} data-testid="create-activity-btn" className="bg-[#1A4D2E] text-white hover:bg-[#143C24] shadow-sm font-medium px-5 py-2.5 rounded-lg transition-all active:scale-95">
          <Plus className="w-4 h-4 mr-2" /> Add Activity
        </Button>
      </div>

      {/* Tabs */}
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="bg-gray-100/50 p-1">
          <TabsTrigger value="pending" data-testid="tab-pending" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
            Pending ({activities.filter(c => c.status === 'pending').length})
          </TabsTrigger>
          <TabsTrigger value="approved" data-testid="tab-approved" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
            Approved ({activities.filter(c => c.status === 'approved').length})
          </TabsTrigger>
          <TabsTrigger value="rejected" data-testid="tab-rejected" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
            Rejected ({activities.filter(c => c.status === 'rejected').length})
          </TabsTrigger>
          <TabsTrigger value="all" data-testid="tab-all" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
            All ({activities.length})
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Activities List */}
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <Card className="bg-white border border-gray-100 rounded-xl shadow-sm">
            <CardContent className="py-12 text-center">
              <ClipboardCheck className="w-10 h-10 mx-auto text-gray-300 mb-3" />
              <p className="text-[#6B7280] text-sm">No {tab !== 'all' ? tab : ''} activities</p>
            </CardContent>
          </Card>
        ) : filtered.map((activity) => (
          <Card key={activity.activity_id} data-testid={`activity-card-${activity.activity_id}`} className="bg-white border border-gray-100 rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:shadow-md transition-shadow duration-300">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div className="flex gap-4 flex-1">
                  {/* Photo preview */}
                  <div className="w-20 h-20 rounded-lg bg-gray-100 flex-shrink-0 overflow-hidden flex items-center justify-center">
                    {activity.photo_urls?.length > 0 && activity.photo_urls[0] ? (
                      <img src={activity.photo_urls[0]} alt="evidence" className="w-full h-full object-cover" />
                    ) : (
                      <ImageIcon className="w-6 h-6 text-gray-300" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-semibold text-[#1F2937]" style={{ fontFamily: 'Manrope, sans-serif' }}>{activity.farmer_name}</h3>
                      <Badge className={`text-[10px] border ${statusColors[activity.status]}`}>{activity.status}</Badge>
                    </div>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-[#6B7280]">
                      <span className="flex items-center gap-1"><TreePine className="w-3 h-3" /> {activity.tree_count} {activity.species}</span>
                      <span>Planted: {activity.planted_date}</span>
                      {activity.lat && activity.lng && (
                        <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {activity.lat.toFixed(4)}, {activity.lng.toFixed(4)}</span>
                      )}
                      <span className="flex items-center gap-1"><ImageIcon className="w-3 h-3" /> {activity.photo_urls?.length || 0} photos</span>
                    </div>
                    <div className="flex gap-4 mt-2">
                      <span className="text-xs"><span className="text-[#6B7280]">Est. Credits:</span> <span className="font-mono text-[#1A4D2E] font-medium">{activity.estimated_credits?.toFixed(4)} tCO2e</span></span>
                      <span className="text-xs"><span className="text-[#6B7280]">Est. Payout:</span> <span className="font-mono text-[#B45309] font-medium">₹{activity.estimated_payout?.toLocaleString('en-IN')}</span></span>
                    </div>
                  </div>
                </div>
                <Button variant="outline" size="sm" onClick={() => { setSelectedActivity(activity); setVerifierNotes(activity.verifier_notes || ''); }} data-testid={`review-activity-${activity.activity_id}`} className="text-xs border-[#1A4D2E]/20 text-[#1A4D2E] hover:bg-emerald-50 ml-3">
                  <Eye className="w-3 h-3 mr-1" /> Review
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Review Dialog */}
      <Dialog open={!!selectedActivity} onOpenChange={() => setSelectedActivity(null)}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto" data-testid="review-activity-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>Review Activity</DialogTitle>
          </DialogHeader>
          {selectedActivity && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="text-[#6B7280]">Farmer:</span> <span className="font-medium">{selectedActivity.farmer_name}</span></div>
                <div><span className="text-[#6B7280]">Phone:</span> <span className="font-mono text-xs">{selectedActivity.farmer_phone}</span></div>
                <div><span className="text-[#6B7280]">Project:</span> <span className="font-medium">{selectedActivity.project_name}</span></div>
                <div><span className="text-[#6B7280]">Activity ID:</span> <span className="font-mono text-xs">{selectedActivity.activity_id}</span></div>
                <div><span className="text-[#6B7280]">Trees:</span> <span className="font-bold text-[#1A4D2E]">{selectedActivity.tree_count} {selectedActivity.species}</span></div>
                <div><span className="text-[#6B7280]">Planted:</span> <span>{selectedActivity.planted_date}</span></div>
                <div><span className="text-[#6B7280]">Est. Credits:</span> <span className="font-mono text-[#1A4D2E]">{selectedActivity.estimated_credits?.toFixed(4)} tCO2e</span></div>
                <div><span className="text-[#6B7280]">Est. Payout:</span> <span className="font-mono text-[#B45309]">₹{selectedActivity.estimated_payout}</span></div>
              </div>

              {/* Carbon Credit Estimation Breakdown */}
              {(() => {
                const survey = selectedActivity.survey_responses || {};
                const totalCredits = selectedActivity.estimated_credits || 0;
                const totalPayout = selectedActivity.estimated_payout || 0;

                const hasARR = selectedActivity.lat && selectedActivity.lng && selectedActivity.tree_count > 0;
                const hasRice = survey.water_management && survey.water_management !== 'Not sure';
                const hasALS = ['main_crop', 'crop_residue', 'land_preparation', 'fertilizer_level', 'compost_usage'].some(k => survey[k]);

                const weights = [];
                if (hasARR) weights.push({ method: 'ARR', full: 'Afforestation, Reforestation & Revegetation', w: 5.2, basis: 'Location + Trees' });
                if (hasRice) weights.push({ method: 'Rice Methane', full: 'Rice Cultivation Methane Reduction', w: 2, basis: `Water: ${survey.water_management}` });
                if (hasALS) weights.push({ method: 'ALS', full: 'Improved Agricultural Land Management', w: 3, basis: 'Farm practices' });

                if (weights.length === 0) return null;

                const totalWeight = weights.reduce((s, r) => s + r.w, 0);
                const rows = weights.map(r => ({
                  ...r,
                  credits: totalCredits * (r.w / totalWeight),
                  payout: totalPayout * (r.w / totalWeight),
                }));

                return (
                  <div className="rounded-lg border border-[#1A4D2E]/15 overflow-hidden" data-testid="credit-breakdown-table">
                    <div className="bg-[#1A4D2E] px-4 py-2.5">
                      <p className="text-xs font-semibold text-white uppercase tracking-wide">Carbon Credit Estimation Breakdown</p>
                    </div>
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="bg-[#F0F8F0] text-[#1A4D2E]">
                          <th className="text-left px-4 py-2 font-semibold">Methodology</th>
                          <th className="text-center px-3 py-2 font-semibold">Est. tCO2e</th>
                          <th className="text-right px-4 py-2 font-semibold">Est. Payout (₹)</th>
                          <th className="text-right px-4 py-2 font-semibold">Basis</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((r, i) => (
                          <tr key={r.method} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
                            <td className="px-4 py-2.5">
                              <span className="font-semibold text-[#1F2937]">{r.method}</span>
                              <span className="block text-[10px] text-[#6B7280]">{r.full}</span>
                            </td>
                            <td className="text-center px-3 py-2.5 font-mono font-semibold text-[#1A4D2E]">{r.credits.toFixed(4)}</td>
                            <td className="text-right px-4 py-2.5 font-mono font-semibold text-[#B45309]">₹{Math.round(r.payout).toLocaleString('en-IN')}</td>
                            <td className="text-right px-4 py-2.5 text-[#6B7280]">{r.basis}</td>
                          </tr>
                        ))}
                      </tbody>
                      <tfoot>
                        <tr className="border-t-2 border-[#1A4D2E]/20 bg-[#F0F8F0]">
                          <td className="px-4 py-2.5 font-bold text-[#1F2937]">Total</td>
                          <td className="text-center px-3 py-2.5 font-mono font-bold text-[#1A4D2E]">{totalCredits.toFixed(4)}</td>
                          <td className="text-right px-4 py-2.5 font-mono font-bold text-[#B45309]">₹{Math.round(totalPayout).toLocaleString('en-IN')}</td>
                          <td className="text-right px-4 py-2.5">—</td>
                        </tr>
                      </tfoot>
                    </table>
                    <div className="px-4 py-2 bg-amber-50/60 text-[10px] text-amber-700 border-t border-amber-200/50">
                      Breakdown of estimated credits &amp; payout across applicable methodologies. Subject to verification.
                    </div>
                  </div>
                );
              })()}

              {/* Location */}
              {selectedActivity.lat && selectedActivity.lng && (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs font-medium text-[#6B7280] mb-1">Location Evidence</p>
                  <p className="text-sm font-mono">{selectedActivity.lat.toFixed(6)}, {selectedActivity.lng.toFixed(6)}</p>
                  <a href={`https://www.google.com/maps?q=${selectedActivity.lat},${selectedActivity.lng}`} target="_blank" rel="noopener noreferrer" className="text-xs text-[#1A4D2E] underline mt-1 inline-block" data-testid="view-on-map-link">View on Google Maps</a>
                </div>
              )}

              {/* Photos */}
              {selectedActivity.photo_urls?.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-[#6B7280] mb-2">Photo Evidence</p>
                  <div className="grid grid-cols-2 gap-3">
                    {selectedActivity.photo_urls.map((url, i) => (
                      url && (
                        <div key={i} className="aspect-video rounded-lg overflow-hidden bg-gray-100 border border-gray-200">
                          <img src={url} alt={`Evidence ${i + 1}`} className="w-full h-full object-cover" />
                        </div>
                      )
                    ))}
                  </div>
                </div>
              )}

              {/* Survey Responses in Review */}
              {selectedActivity.survey_responses && Object.keys(selectedActivity.survey_responses).length > 0 && (
                <div className="p-4 bg-[#F0F8F0] rounded-lg border border-[#1A4D2E]/10">
                  <p className="text-xs font-semibold text-[#1A4D2E] mb-3 uppercase tracking-wide">Survey Responses</p>
                  <div className="space-y-3">
                    {SURVEY_QUESTIONS.map(q => {
                      const answer = selectedActivity.survey_responses[q.id];
                      if (!answer) return null;
                      return (
                        <div key={q.id} className="text-xs" data-testid={`review-survey-${q.id}`}>
                          <p className="text-[#6B7280] font-medium mb-0.5">{q.label}</p>
                          <p className="text-[#1F2937] font-semibold pl-3"><span className="text-[#1A4D2E]">Ans:</span> {answer}</p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Verifier Notes */}
              <div>
                <Label>Verifier Notes</Label>
                <Textarea data-testid="verifier-notes" value={verifierNotes} onChange={e => setVerifierNotes(e.target.value)} placeholder="Add notes for this activity..." className="mt-1" rows={3} />
              </div>

              {/* Disclaimer */}
              <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 text-xs text-amber-700">
                Estimated units — not issued credits. Final issuance depends on verification + registry rules.
              </div>

              {/* Actions */}
              {selectedActivity.status === 'pending' && (
                <div className="flex gap-3">
                  <Button onClick={() => handleAction(selectedActivity.activity_id, 'approve')} data-testid="approve-activity-btn" className="flex-1 bg-[#1A4D2E] text-white hover:bg-[#143C24]">
                    <Check className="w-4 h-4 mr-2" /> Approve
                  </Button>
                  <Button onClick={() => handleAction(selectedActivity.activity_id, 'reject')} data-testid="reject-activity-btn" variant="outline" className="flex-1 border-red-200 text-red-600 hover:bg-red-50">
                    <X className="w-4 h-4 mr-2" /> Reject
                  </Button>
                  <Button onClick={() => handleAction(selectedActivity.activity_id, 'needs_info')} data-testid="needs-info-btn" variant="outline" className="border-blue-200 text-blue-600 hover:bg-blue-50">
                    <MessageCircle className="w-4 h-4 mr-1" /> Need Info
                  </Button>
                </div>
              )}
              {selectedActivity.status !== 'pending' && (
                <div className="p-3 bg-gray-50 rounded-lg text-center">
                  <Badge className={`${statusColors[selectedActivity.status]} border`}>This activity has been {selectedActivity.status}</Badge>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Create Activity Dialog */}
      <Dialog open={showCreate} onOpenChange={(open) => {
        setShowCreate(open);
        if (!open) { setSurveyExpanded(false); }
      }}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto" data-testid="create-activity-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>Submit Activity</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <Label>Project *</Label>
              <Select value={form.project_id} onValueChange={v => setForm({...form, project_id: v})}>
                <SelectTrigger className="mt-1" data-testid="activity-project-select"><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  {projects.map(p => <SelectItem key={p.project_id} value={p.project_id}>{p.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Farmer *</Label>
              <Select value={form.farmer_id} onValueChange={v => setForm({...form, farmer_id: v})}>
                <SelectTrigger className="mt-1" data-testid="activity-farmer-select"><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  {farmers.filter(f => !form.project_id || f.project_id === form.project_id).map(f => <SelectItem key={f.farmer_id} value={f.farmer_id}>{f.name} ({f.phone})</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Tree Count *</Label>
                <Input data-testid="activity-tree-count" type="number" value={form.tree_count} onChange={e => setForm({...form, tree_count: e.target.value})} className="mt-1" />
              </div>
              <div>
                <Label>Species</Label>
                <Select value={form.species} onValueChange={v => setForm({...form, species: v})}>
                  <SelectTrigger className="mt-1" data-testid="activity-species-select"><SelectValue /></SelectTrigger>
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
              <Input data-testid="activity-planted-date" type="date" value={form.planted_date} onChange={e => setForm({...form, planted_date: e.target.value})} className="mt-1" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Latitude</Label>
                <Input data-testid="activity-lat" type="number" step="any" value={form.lat} onChange={e => setForm({...form, lat: e.target.value})} placeholder="e.g., 21.1702" className="mt-1" />
              </div>
              <div>
                <Label>Longitude</Label>
                <Input data-testid="activity-lng" type="number" step="any" value={form.lng} onChange={e => setForm({...form, lng: e.target.value})} placeholder="e.g., 72.8311" className="mt-1" />
              </div>
            </div>
            <div>
              <Label>Photo URL 1 (sapling)</Label>
              <Input data-testid="activity-photo-1" value={form.photo_urls[0]} onChange={e => { const urls = [...form.photo_urls]; urls[0] = e.target.value; setForm({...form, photo_urls: urls}); }} placeholder="https://..." className="mt-1" />
            </div>
            <div>
              <Label>Photo URL 2 (wide shot)</Label>
              <Input data-testid="activity-photo-2" value={form.photo_urls[1]} onChange={e => { const urls = [...form.photo_urls]; urls[1] = e.target.value; setForm({...form, photo_urls: urls}); }} placeholder="https://..." className="mt-1" />
            </div>
            <div>
              <Label>Notes</Label>
              <Textarea data-testid="activity-notes" value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} placeholder="Optional notes" className="mt-1" rows={2} />
            </div>

            {/* Survey Section */}
            <div className="border border-[#1A4D2E]/15 rounded-lg overflow-hidden mt-2">
              <button
                type="button"
                onClick={() => setSurveyExpanded(!surveyExpanded)}
                data-testid="survey-toggle-btn"
                className="w-full flex items-center justify-between px-4 py-3 bg-[#F0F8F0] hover:bg-[#E5F2E5] transition-colors text-left"
              >
                <div className="flex items-center gap-2">
                  <ClipboardCheck className="w-4 h-4 text-[#1A4D2E]" />
                  <span className="text-sm font-semibold text-[#1A4D2E]" style={{ fontFamily: 'Manrope, sans-serif' }}>Farmer Survey *</span>
                  <span className="text-[10px] text-[#6B7280]">
                    ({SURVEY_QUESTIONS.filter(q => survey[q.id]).length}/{SURVEY_QUESTIONS.length} answered)
                  </span>
                </div>
                {surveyExpanded ? <ChevronUp className="w-4 h-4 text-[#1A4D2E]" /> : <ChevronDown className="w-4 h-4 text-[#1A4D2E]" />}
              </button>

              {surveyExpanded && (
                <div className="p-4 space-y-5 bg-white" data-testid="survey-section">
                  {SURVEY_QUESTIONS.map((q, qIdx) => (
                    <div key={q.id} data-testid={`survey-q-${q.id}`}>
                      <p className="text-sm font-medium text-[#1F2937] mb-1">{q.label}</p>
                      {q.description && (
                        <p className="text-xs text-[#6B7280] mb-2 whitespace-pre-line leading-relaxed">{q.description}</p>
                      )}
                      <RadioGroup
                        value={survey[q.id]}
                        onValueChange={(val) => setSurvey(prev => ({ ...prev, [q.id]: val }))}
                        className="grid gap-1.5 mt-1"
                      >
                        {q.options.map((opt) => (
                          <label
                            key={opt}
                            className={`flex items-center gap-2.5 px-3 py-2 rounded-md cursor-pointer border transition-colors text-sm ${
                              survey[q.id] === opt
                                ? 'border-[#1A4D2E]/40 bg-[#F0F8F0]'
                                : 'border-transparent hover:bg-gray-50'
                            }`}
                          >
                            <RadioGroupItem
                              value={opt}
                              data-testid={`survey-${q.id}-${opt.toLowerCase().replace(/[^a-z0-9]/g, '-')}`}
                            />
                            <span className="text-[#374151]">{opt}</span>
                          </label>
                        ))}
                      </RadioGroup>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={handleCreateActivity} data-testid="submit-activity-btn" className="bg-[#1A4D2E] text-white hover:bg-[#143C24]">Submit Activity</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
