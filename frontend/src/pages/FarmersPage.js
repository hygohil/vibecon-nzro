import React, { useState, useEffect } from 'react';
import { Users, Plus, Phone, MapPin, Banknote, Search, ChevronLeft, ChevronRight, AlertCircle, Info } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { PhoneInput } from '../components/ui/phone-input';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../components/ui/tooltip';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function FarmersPage() {
  const [farmers, setFarmers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [search, setSearch] = useState('');
  const [filterProject, setFilterProject] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalCount, setTotalCount] = useState(0);
  const [phoneCheckLoading, setPhoneCheckLoading] = useState(false);
  const [phoneExists, setPhoneExists] = useState(false);
  const [form, setForm] = useState({
    name: '', phone: '',
    land_type: 'owned', acres: '', upi_id: '', project_id: ''
  });

  const fetchData = async () => {
    try {
      const [fRes, pRes, countRes] = await Promise.all([
        fetch(`${API}/farmers?page=${page}&page_size=${pageSize}`, { credentials: 'include' }),
        fetch(`${API}/projects`, { credentials: 'include' }),
        fetch(`${API}/farmers/count/total`, { credentials: 'include' }),
      ]);
      if (fRes.ok) setFarmers(await fRes.json());
      if (pRes.ok) setProjects(await pRes.json());
      if (countRes.ok) {
        const data = await countRes.json();
        setTotalCount(data.total);
      }
    } catch (e) {
      console.error('Error fetching data:', e);
    }
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, [page]);
  
  const checkPhoneUniqueness = async (phone) => {
    if (!phone || phone.length < 10) {
      setPhoneExists(false);
      return;
    }
    
    setPhoneCheckLoading(true);
    try {
      const res = await fetch(`${API}/farmers/check-phone`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone }),
      });
      if (res.ok) {
        const data = await res.json();
        setPhoneExists(data.exists);
        if (data.exists) {
          toast.error('This mobile number is already registered');
        }
      }
    } catch (e) {
      console.error('Error checking phone:', e);
    }
    setPhoneCheckLoading(false);
  };

  const handleCreate = async () => {
    if (!form.name || !form.phone || !form.project_id) {
      toast.error('Fill all required fields'); return;
    }
    if (phoneExists) {
      toast.error('This mobile number is already registered');
      return;
    }
    try {
      const res = await fetch(`${API}/farmers`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, acres: form.acres ? Number(form.acres) : null }),
      });
      if (res.ok) {
        toast.success('Farmer added');
        setShowCreate(false);
        setPage(1); // Reset to first page
        fetchData();
        setForm({ name: '', phone: '', land_type: 'owned', acres: '', upi_id: '', project_id: '' });
        setPhoneExists(false);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed');
      }
    } catch { toast.error('Network error'); }
  };

  const filtered = farmers.filter(f => {
    const matchSearch = !search || f.name.toLowerCase().includes(search.toLowerCase()) || f.phone.includes(search) || (f.project_name && f.project_name.toLowerCase().includes(search.toLowerCase()));
    const matchProject = filterProject === 'all' || f.project_id === filterProject;
    return matchSearch && matchProject;
  });

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-4 border-[#1A4D2E] border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div data-testid="farmers-page" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1F2937] tracking-tight" style={{ fontFamily: 'Manrope, sans-serif' }}>Farmers</h1>
          <p className="text-[#6B7280] mt-1">{farmers.length} farmers enrolled across {projects.length} projects</p>
        </div>
        <Button onClick={() => setShowCreate(true)} data-testid="add-farmer-btn" className="bg-[#1A4D2E] text-white hover:bg-[#143C24] shadow-sm font-medium px-5 py-2.5 rounded-lg transition-all active:scale-95">
          <Plus className="w-4 h-4 mr-2" /> Add Farmer
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 items-center">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7280]" />
          <Input data-testid="farmer-search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by name, phone, project..." className="pl-9" />
        </div>
        <Select value={filterProject} onValueChange={setFilterProject}>
          <SelectTrigger className="w-[200px]" data-testid="project-filter">
            <SelectValue placeholder="Filter by project" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Projects</SelectItem>
            {projects.map(p => <SelectItem key={p.project_id} value={p.project_id}>{p.name}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <Card className="bg-white border border-gray-100 rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50/50 hover:bg-gray-50/50">
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-[#6B7280]">Farmer</TableHead>
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-[#6B7280]">Project</TableHead>
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-[#6B7280]">Trees</TableHead>
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-[#6B7280]">EST. CREDITS</TableHead>
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-[#6B7280]">EST. PAYOUT</TableHead>
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-[#6B7280]">Land</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 ? (
                <TableRow><TableCell colSpan={6} className="text-center py-8 text-[#6B7280]">No farmers found</TableCell></TableRow>
              ) : filtered.map((f) => (
                <TableRow key={f.farmer_id} className="hover:bg-gray-50/50 transition-colors" data-testid={`farmer-row-${f.farmer_id}`}>
                  <TableCell>
                    <div>
                      <p className="text-sm font-medium text-[#1F2937]">{f.name}</p>
                      <div className="flex items-center gap-1 text-xs text-[#6B7280]">
                        <Phone className="w-3 h-3" /> {f.phone}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-[10px] border-[#1A4D2E]/20 text-[#1A4D2E]">{f.project_name || f.project_id}</Badge>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm font-medium">{f.approved_trees}/{f.total_trees}</span>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm font-mono text-[#1A4D2E]">{f.estimated_credits_1y?.toFixed(4) || '0.0000'}</span>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm font-mono font-medium text-[#B45309]">₹{Math.round(f.estimated_payout_1y || 0).toLocaleString('en-IN')}</span>
                  </TableCell>
                  <TableCell>
                    <span className="text-xs text-[#6B7280]">{f.land_type}{f.acres ? ` (${Number(f.acres).toFixed(2)} ac)` : ''}</span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="max-w-md" data-testid="add-farmer-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>Add Farmer</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <Label>Name *</Label>
              <Input data-testid="farmer-name-input" value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="Farmer name" className="mt-1" />
            </div>
            <div>
              <Label>Phone Number *</Label>
              <PhoneInput 
                data-testid="farmer-phone-input" 
                value={form.phone} 
                onChange={e => setForm({...form, phone: e.target.value})} 
                placeholder="Enter phone number"
                className="mt-1" 
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Land Type</Label>
                <Select value={form.land_type} onValueChange={v => setForm({...form, land_type: v})}>
                  <SelectTrigger className="mt-1" data-testid="land-type-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="owned">Owned</SelectItem>
                    <SelectItem value="leased">Leased</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Acres</Label>
                <Input data-testid="farmer-acres-input" type="number" value={form.acres} onChange={e => setForm({...form, acres: e.target.value})} className="mt-1" />
              </div>
            </div>
            <div>
              <Label>UPI ID</Label>
              <Input data-testid="farmer-upi-input" value={form.upi_id} onChange={e => setForm({...form, upi_id: e.target.value})} placeholder="name@upi" className="mt-1" />
            </div>
            <div>
              <Label>Project *</Label>
              <Select value={form.project_id} onValueChange={v => setForm({...form, project_id: v})}>
                <SelectTrigger className="mt-1" data-testid="farmer-project-select"><SelectValue placeholder="Select project" /></SelectTrigger>
                <SelectContent>
                  {projects.map(p => <SelectItem key={p.project_id} value={p.project_id}>{p.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={handleCreate} data-testid="submit-farmer-btn" className="bg-[#1A4D2E] text-white hover:bg-[#143C24]">Add Farmer</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
