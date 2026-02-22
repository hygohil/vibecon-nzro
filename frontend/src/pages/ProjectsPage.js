import React, { useState, useEffect } from 'react';
import { Plus, TreePine, MapPin, Trash2, Eye, X, Lock, AlertCircle, Pencil, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import { Combobox } from '../components/ui/combobox';
import { toast } from 'sonner';
import { INDIAN_STATES, getStateLabel } from '../lib/indian-states';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Conservative MRV defaults - locked for standardization
const LOCKED_PARAMS = {
  survival_rate: 0.7,
  conservative_discount: 0.2,
  max_trees_per_acre: 400,
  cooldown_days: 30,
  monitoring_frequency_days: 90,
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [showDetail, setShowDetail] = useState(null);
  const [form, setForm] = useState({
    name: '',
    region: '',
    description: '',
    species_list: [],
    payout_rule_type: 'per_tco2e',
    payout_rate: 500,
    ...LOCKED_PARAMS,
    required_proofs: ['location', 'photo'],
  });

  const fetchProjects = async () => {
    try {
      const res = await fetch(`${API}/projects`, { credentials: 'include' });
      if (res.ok) setProjects(await res.json());
    } catch {}
    setLoading(false);
  };

  useEffect(() => { fetchProjects(); }, []);

  const handleCreate = async () => {
    if (!form.name || !form.region) { toast.error('Name and Region are required'); return; }
    try {
      const res = await fetch(`${API}/projects`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          payout_rate: Number(form.payout_rate),
          survival_rate: LOCKED_PARAMS.survival_rate,
          conservative_discount: LOCKED_PARAMS.conservative_discount,
          max_trees_per_acre: LOCKED_PARAMS.max_trees_per_acre,
          cooldown_days: LOCKED_PARAMS.cooldown_days,
          monitoring_frequency_days: LOCKED_PARAMS.monitoring_frequency_days,
        }),
      });
      if (res.ok) {
        toast.success('Project created');
        setShowCreate(false);
        fetchProjects();
        setForm({
          name: '',
          region: '',
          description: '',
          species_list: [],
          payout_rule_type: 'per_tco2e',
          payout_rate: 500,
          ...LOCKED_PARAMS,
          required_proofs: ['location', 'photo'],
        });
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to create');
      }
    } catch { toast.error('Network error'); }
  };

  const deleteProject = async (id) => {
    try {
      const res = await fetch(`${API}/projects/${id}`, { method: 'DELETE', credentials: 'include' });
      if (res.ok) { toast.success('Project deleted'); fetchProjects(); }
    } catch { toast.error('Failed to delete'); }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-4 border-[#1A4D2E] border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div data-testid="projects-page" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1F2937] tracking-tight" style={{ fontFamily: 'Manrope, sans-serif' }}>Projects</h1>
          <p className="text-[#6B7280] mt-1">Manage your tree plantation projects</p>
        </div>
        <Button onClick={() => setShowCreate(true)} data-testid="create-project-btn" className="bg-[#1A4D2E] text-white hover:bg-[#143C24] shadow-sm font-medium px-5 py-2.5 rounded-lg transition-all active:scale-95">
          <Plus className="w-4 h-4 mr-2" /> Create Project
        </Button>
      </div>

      {projects.length === 0 ? (
        <Card className="bg-white border border-gray-100 rounded-xl shadow-sm">
          <CardContent className="py-16 text-center">
            <TreePine className="w-12 h-12 mx-auto text-gray-300 mb-4" />
            <p className="text-[#6B7280]">No projects yet. Create your first tree plantation project.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {projects.map((p) => (
            <Card key={p.project_id} data-testid={`project-card-${p.project_id}`} className="bg-white border border-gray-100 rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:shadow-md transition-shadow duration-300">
              <CardContent className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-9 h-9 bg-emerald-50 rounded-lg flex items-center justify-center">
                      <TreePine className="w-4 h-4 text-[#1A4D2E]" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-[#1F2937] text-sm" style={{ fontFamily: 'Manrope, sans-serif' }}>{p.name}</h3>
                      <div className="flex items-center gap-1 text-xs text-[#6B7280]">
                        <MapPin className="w-3 h-3" /> {getStateLabel(p.region)}
                      </div>
                    </div>
                  </div>
                  <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200 text-[10px]">{p.status}</Badge>
                </div>
                <p className="text-xs text-[#6B7280] mb-3 line-clamp-2">{p.description || 'No description'}</p>
                <div className="grid grid-cols-3 gap-2 mb-4">
                  <div className="text-center p-2 bg-gray-50 rounded-lg">
                    <p className="text-lg font-bold text-[#1A4D2E]" style={{ fontFamily: 'Manrope, sans-serif' }}>{p.farmers_count}</p>
                    <p className="text-[10px] text-[#6B7280]">Farmers</p>
                  </div>
                  <div className="text-center p-2 bg-gray-50 rounded-lg">
                    <p className="text-lg font-bold text-[#B45309]" style={{ fontFamily: 'Manrope, sans-serif' }}>{p.activities_count}</p>
                    <p className="text-[10px] text-[#6B7280]">Activities</p>
                  </div>
                  <div className="text-center p-2 bg-gray-50 rounded-lg">
                    <p className="text-lg font-bold text-[#059669]" style={{ fontFamily: 'Manrope, sans-serif' }}>₹{p.payout_rate}</p>
                    <p className="text-[10px] text-[#6B7280]">/tCO₂e</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => setShowDetail(p)} data-testid={`view-project-${p.project_id}`} className="flex-1 text-xs border-[#1A4D2E]/20 text-[#1A4D2E] hover:bg-emerald-50">
                    <Eye className="w-3 h-3 mr-1" /> View
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => deleteProject(p.project_id)} data-testid={`delete-project-${p.project_id}`} className="text-xs border-red-200 text-red-500 hover:bg-red-50">
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto" data-testid="create-project-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>Create Tree Project</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {/* Disclaimer Banner */}
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
              <p className="text-xs text-amber-800">
                <strong>Note:</strong> All values are estimates until verified. Issuance depends on monitoring evidence and verification.
              </p>
            </div>

            <div>
              <Label>Project Name *</Label>
              <Input data-testid="project-name-input" value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="e.g., Saurashtra Tree Revival" className="mt-1" />
            </div>

            <div>
              <Label>Region / State *</Label>
              <Combobox
                data-testid="project-region-input"
                value={form.region}
                onValueChange={v => setForm({...form, region: v})}
                options={INDIAN_STATES}
                placeholder="Select state or region..."
                searchPlaceholder="Search Indian states..."
                emptyText="No state found."
                className="mt-1"
              />
            </div>

            <div>
              <Label>Description (Optional)</Label>
              <Textarea data-testid="project-desc-input" value={form.description} onChange={e => setForm({...form, description: e.target.value})} placeholder="Brief description of the project" className="mt-1" rows={2} />
            </div>

            {/* Payout Configuration */}
            <div className="border-t pt-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Payout Configuration</h3>
              <div>
                <Label>Payout Rate (₹/tCO₂e) *</Label>
                <Input
                  data-testid="payout-rate-input"
                  type="number"
                  step="50"
                  min="0"
                  value={form.payout_rate}
                  onChange={e => setForm({...form, payout_rate: e.target.value})}
                  className="mt-1"
                  placeholder="500"
                />
                <p className="text-xs text-gray-500 mt-1">Default market rate: ₹500 per tCO₂e (editable)</p>
              </div>
            </div>

            {/* Locked Conservative Parameters */}
            <div className="border-t pt-4">
              <div className="flex items-center gap-2 mb-3">
                <Lock className="w-4 h-4 text-gray-500" />
                <h3 className="text-sm font-semibold text-gray-700">Conservative MRV Settings</h3>
              </div>
              <p className="text-xs text-gray-600 mb-3">
                Locked to maintain conservative MRV settings and prevent over-claiming.
              </p>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-gray-600">Survival Rate</Label>
                  <div className="relative mt-1">
                    <Input
                      type="number"
                      value={LOCKED_PARAMS.survival_rate}
                      disabled
                      className="bg-gray-50 text-gray-600 cursor-not-allowed"
                    />
                    <Lock className="w-3 h-3 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2" />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">70% (locked)</p>
                </div>

                <div>
                  <Label className="text-gray-600">Conservative Discount</Label>
                  <div className="relative mt-1">
                    <Input
                      type="number"
                      value={LOCKED_PARAMS.conservative_discount}
                      disabled
                      className="bg-gray-50 text-gray-600 cursor-not-allowed"
                    />
                    <Lock className="w-3 h-3 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2" />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">20% (locked)</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mt-3">
                <div>
                  <Label className="text-gray-600">Max Trees/Acre</Label>
                  <div className="relative mt-1">
                    <Input
                      type="number"
                      value={LOCKED_PARAMS.max_trees_per_acre}
                      disabled
                      className="bg-gray-50 text-gray-600 cursor-not-allowed"
                    />
                    <Lock className="w-3 h-3 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2" />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">400 (locked)</p>
                </div>

                <div>
                  <Label className="text-gray-600">Cooldown (days)</Label>
                  <div className="relative mt-1">
                    <Input
                      type="number"
                      value={LOCKED_PARAMS.cooldown_days}
                      disabled
                      className="bg-gray-50 text-gray-600 cursor-not-allowed"
                    />
                    <Lock className="w-3 h-3 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2" />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Prevents repeated activities</p>
                </div>
              </div>

              <div className="mt-3">
                <Label className="text-gray-600">Monitoring Frequency (days)</Label>
                <div className="relative mt-1">
                  <Input
                    type="number"
                    value={LOCKED_PARAMS.monitoring_frequency_days}
                    disabled
                    className="bg-gray-50 text-gray-600 cursor-not-allowed"
                  />
                  <Lock className="w-3 h-3 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2" />
                </div>
                <p className="text-xs text-gray-500 mt-1">Standard 90-day survival verification cycle</p>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={handleCreate} data-testid="submit-project-btn" className="bg-[#1A4D2E] text-white hover:bg-[#143C24]">Create Project</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={!!showDetail} onOpenChange={() => setShowDetail(null)}>
        <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto" data-testid="project-detail-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>{showDetail?.name}</DialogTitle>
          </DialogHeader>
          {showDetail && (
            <div className="space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div><span className="text-[#6B7280]">Region:</span> <span className="font-medium">{getStateLabel(showDetail.region)}</span></div>
                <div><span className="text-[#6B7280]">Status:</span> <Badge className="bg-emerald-50 text-emerald-700 ml-1">{showDetail.status}</Badge></div>
                <div><span className="text-[#6B7280]">Payout:</span> <span className="font-medium">₹{showDetail.payout_rate}/tCO₂e</span></div>
                <div><span className="text-[#6B7280]">Farmers:</span> <span className="font-medium">{showDetail.farmers_count || 0}</span></div>
              </div>

              {showDetail.description && (
                <div>
                  <p className="text-[#6B7280] mb-1">Description:</p>
                  <p className="text-gray-700">{showDetail.description}</p>
                </div>
              )}

              <div className="border-t pt-4">
                <div className="flex items-center gap-2 mb-3">
                  <Lock className="w-4 h-4 text-gray-500" />
                  <h3 className="text-sm font-semibold text-gray-700">Conservative MRV Settings</h3>
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="bg-gray-50 p-2 rounded">
                    <span className="text-gray-600">Survival Rate:</span> <span className="font-medium">{(showDetail.survival_rate * 100).toFixed(0)}%</span>
                  </div>
                  <div className="bg-gray-50 p-2 rounded">
                    <span className="text-gray-600">Discount:</span> <span className="font-medium">{(showDetail.conservative_discount * 100).toFixed(0)}%</span>
                  </div>
                  <div className="bg-gray-50 p-2 rounded">
                    <span className="text-gray-600">Max Trees/Acre:</span> <span className="font-medium">{showDetail.max_trees_per_acre}</span>
                  </div>
                  <div className="bg-gray-50 p-2 rounded">
                    <span className="text-gray-600">Cooldown:</span> <span className="font-medium">{showDetail.cooldown_days}d</span>
                  </div>
                  <div className="bg-gray-50 p-2 rounded col-span-2">
                    <span className="text-gray-600">Monitoring:</span> <span className="font-medium">Every {showDetail.monitoring_frequency_days} days</span>
                  </div>
                </div>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-amber-800">
                  <strong>Note:</strong> All values are estimates until verified. Issuance depends on monitoring evidence and verification.
                </p>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setShowDetail(null)} className="bg-[#1A4D2E] text-white hover:bg-[#143C24]">Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
