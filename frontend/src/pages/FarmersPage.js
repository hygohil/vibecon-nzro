import React, { useState, useEffect } from 'react';
import { Users, Plus, Phone, MapPin, Banknote, Search, ChevronLeft, ChevronRight, AlertCircle, Info, Upload, FileText, CheckCircle, XCircle, Download, ArrowRight, Loader2, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '../components/ui/alert-dialog';
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
  const [submitting, setSubmitting] = useState(false);
  const [phoneError, setPhoneError] = useState('');
  const [showBulkUpload, setShowBulkUpload] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null); // {farmer_id, name, total_trees}
  const [deleting, setDeleting] = useState(false);
  const [form, setForm] = useState({
    name: '', phone: '',
    land_type: 'owned', acres: '', upi_id: '', project_id: ''
  });

  const fetchData = async () => {
    try {
      const [fRes, pRes, countRes] = await Promise.all([
        fetch(`${API}/farmers?page=${page}&page_size=${pageSize}`, { credentials: 'include', cache: 'no-store' }),
        fetch(`${API}/projects`, { credentials: 'include', cache: 'no-store' }),
        fetch(`${API}/farmers/count/total`, { credentials: 'include', cache: 'no-store' }),
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

  const validatePhoneNumber = (phone) => {
    if (!phone) return false;
    // PhoneInput stores "+91XXXXXXXXXX". Strip exactly "+91" then check 10 digits.
    const national = phone.replace(/^\+91/, '').replace(/[^\d]/g, '');
    return national.length === 10;
  };

  const handleCreate = async () => {
    // Clear previous phone error
    setPhoneError('');
    
    // Validate required fields
    if (!form.name || !form.phone || !form.project_id) {
      toast.error('Please fill all required fields'); 
      return;
    }
    
    // Validate phone format (10 digits)
    if (!validatePhoneNumber(form.phone)) {
      setPhoneError('Phone number must be 10 digits');
      return;
    }
    
    setSubmitting(true);
    
    try {
      const res = await fetch(`${API}/farmers`, {
        method: 'POST', 
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          ...form, 
          acres: form.acres ? Number(form.acres) : null 
        }),
      });
      
      if (res.ok) {
        // Success - farmer created
        toast.success('Farmer onboarded successfully');
        setShowCreate(false);
        setPage(1); // Reset to first page
        fetchData();
        setForm({ name: '', phone: '', land_type: 'owned', acres: '', upi_id: '', project_id: '' });
        setPhoneError('');
      } else if (res.status === 409) {
        // Duplicate phone number
        const err = await res.json().catch(() => ({}));
        setPhoneError('This mobile number is already registered');
        // Don't close modal - let user correct the phone number
      } else {
        // Other server errors
        const err = await res.json().catch(() => ({}));
        
        // Check if error message indicates duplicate
        if (err.detail && err.detail.toLowerCase().includes('already registered')) {
          setPhoneError('This mobile number is already registered');
        } else if (err.detail) {
          toast.error(err.detail);
        } else {
          toast.error('Unable to add farmer right now. Please try again.');
        }
      }
    } catch (error) {
      console.error('Error adding farmer:', error);
      toast.error('Something went wrong. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      const res = await fetch(`${API}/farmers/${deleteTarget.farmer_id}`, {
        method: 'DELETE', credentials: 'include',
      });
      if (res.ok) {
        toast.success(`${deleteTarget.name} removed successfully`);
        setDeleteTarget(null);
        if (farmers.length === 1 && page > 1) setPage(p => p - 1);
        else fetchData();
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Could not delete farmer');
      }
    } catch {
      toast.error('Something went wrong');
    } finally {
      setDeleting(false);
    }
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
          <p className="text-[#6B7280] mt-1">View all farmers onboarded into projects</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setShowBulkUpload(true)} variant="outline" data-testid="bulk-upload-btn" className="border-[#1A4D2E]/30 text-[#1A4D2E] hover:bg-emerald-50 font-medium px-4 py-2.5 rounded-lg">
            <Upload className="w-4 h-4 mr-2" /> Bulk Upload
          </Button>
          <Button onClick={() => setShowCreate(true)} data-testid="add-farmer-btn" className="bg-[#1A4D2E] text-white hover:bg-[#143C24] shadow-sm font-medium px-5 py-2.5 rounded-lg transition-all active:scale-95">
            <Plus className="w-4 h-4 mr-2" /> Add Farmer
          </Button>
        </div>
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
                <TableHead className="text-xs font-semibold uppercase tracking-wider text-[#6B7280] w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 ? (
                <TableRow><TableCell colSpan={7} className="text-center py-8 text-[#6B7280]">No farmers found</TableCell></TableRow>
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
                  <TableCell>
                    <button
                      onClick={() => setDeleteTarget({ farmer_id: f.farmer_id, name: f.name, total_trees: f.total_trees || 0 })}
                      data-testid={`delete-farmer-${f.farmer_id}`}
                      className="p-1.5 rounded-md text-gray-300 hover:text-red-500 hover:bg-red-50 transition-colors"
                      title="Delete farmer"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
        
        {/* Pagination Controls */}
        <div className="border-t px-6 py-4 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Showing {Math.min((page - 1) * pageSize + 1, totalCount)}–{Math.min(page * pageSize, totalCount)} of {totalCount}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="h-8"
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </Button>
            <div className="text-sm text-gray-600">
              Page {page} of {Math.ceil(totalCount / pageSize)}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => Math.min(Math.ceil(totalCount / pageSize), p + 1))}
              disabled={page >= Math.ceil(totalCount / pageSize)}
              className="h-8"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
        
        {/* Disclaimer */}
        <div className="bg-amber-50 border-t border-amber-200 px-6 py-3">
          <p className="text-xs text-amber-800 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span><strong>Estimates only.</strong> Actual issuance and payout depend on monitoring, verification, and project rules.</span>
          </p>
        </div>
      </Card>

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteTarget} onOpenChange={open => { if (!open) setDeleteTarget(null); }}>
        <AlertDialogContent data-testid="delete-farmer-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Farmer</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove <strong>{deleteTarget?.name}</strong>?
              {deleteTarget?.total_trees > 0 && (
                <span className="block mt-2 text-amber-600 font-medium">
                  This will also delete all their plantation activities and ledger entries ({deleteTarget.total_trees} trees recorded).
                </span>
              )}
              <span className="block mt-1 text-red-600 text-xs">This action cannot be undone.</span>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              data-testid="confirm-delete-farmer-btn"
              className="bg-red-600 hover:bg-red-700 text-white focus:ring-red-500"
            >
              {deleting ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Deleting...</> : 'Delete Farmer'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Bulk Upload Modal */}
      <BulkUploadModal
        open={showBulkUpload}
        onClose={() => setShowBulkUpload(false)}
        projects={projects}
        onSuccess={() => { setPage(1); fetchData(); }}
      />

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
                onChange={(e) => {
                  setForm({...form, phone: e.target.value});
                  setPhoneError('');
                }}
                placeholder="Enter 10-digit mobile number"
                className={`mt-1 ${phoneError ? 'border-red-500' : form.phone && !validatePhoneNumber(form.phone) ? 'border-yellow-500' : ''}`}
              />
              {phoneError && (
                <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  {phoneError}
                </p>
              )}
              {!phoneError && form.phone && !validatePhoneNumber(form.phone) && (
                <p className="text-xs text-yellow-700 mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  Phone number must be 10 digits
                </p>
              )}
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
            <Button 
              onClick={handleCreate} 
              data-testid="submit-farmer-btn" 
              disabled={submitting || (form.phone && !validatePhoneNumber(form.phone))}
              className="bg-[#1A4D2E] text-white hover:bg-[#143C24] disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              Add Farmer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}


// ─── Bulk Upload Modal ────────────────────────────────────────────────────────

const STEP = { SETUP: 'setup', VALIDATING: 'validating', VALIDATED: 'validated', ONBOARDING: 'onboarding', DONE: 'done' };

function BulkUploadModal({ open, onClose, projects, onSuccess }) {
  const [step, setStep] = useState(STEP.SETUP);
  const [projectId, setProjectId] = useState('');
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [validationResult, setValidationResult] = useState(null); // {total_rows, valid_count, error_count, rows}
  const [onboardResult, setOnboardResult] = useState(null);       // {success_count, error_count, errors}
  const [errorFilter, setErrorFilter] = useState('all');          // 'all' | 'errors' | 'valid'

  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

  const reset = () => {
    setStep(STEP.SETUP);
    setProjectId('');
    setFile(null);
    setDragOver(false);
    setValidationResult(null);
    setOnboardResult(null);
    setErrorFilter('all');
  };

  const handleClose = () => { reset(); onClose(); };

  const downloadTemplate = () => {
    window.open(`${API}/farmers/bulk/template`, '_blank');
  };

  const handleFileSelect = (f) => {
    if (!f) return;
    if (!f.name.endsWith('.csv')) { toast.error('Please upload a .csv file'); return; }
    setFile(f);
  };

  const handleValidate = async () => {
    if (!projectId) { toast.error('Please select a project'); return; }
    if (!file) { toast.error('Please upload a CSV file'); return; }
    setStep(STEP.VALIDATING);
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('project_id', projectId);
      const res = await fetch(`${API}/farmers/bulk/validate-csv`, {
        method: 'POST', credentials: 'include', body: fd,
      });
      const data = await res.json();
      if (!res.ok) { toast.error(data.detail || 'Validation failed'); setStep(STEP.SETUP); return; }
      setValidationResult(data);
      setStep(STEP.VALIDATED);
    } catch (e) {
      toast.error('Something went wrong during validation');
      setStep(STEP.SETUP);
    }
  };

  const handleOnboard = async () => {
    if (!validationResult) return;
    const validRows = validationResult.rows.filter(r => r.errors.length === 0);
    setStep(STEP.ONBOARDING);
    try {
      const res = await fetch(`${API}/farmers/bulk/onboard`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: projectId, rows: validRows }),
      });
      const data = await res.json();
      if (!res.ok) { toast.error(data.detail || 'Onboarding failed'); setStep(STEP.VALIDATED); return; }
      setOnboardResult(data);
      setStep(STEP.DONE);
      if (data.success_count > 0) onSuccess();
    } catch (e) {
      toast.error('Something went wrong during onboarding');
      setStep(STEP.VALIDATED);
    }
  };

  const downloadErrorReport = () => {
    if (!validationResult) return;
    const errorRows = validationResult.rows.filter(r => r.errors.length > 0);
    const lines = ['row,name,phone,land_type,acres,upi_id,errors'];
    errorRows.forEach(r => {
      lines.push([r.row, r.name, r.phone_raw || r.phone, r.land_type, r.acres, r.upi_id, `"${r.errors.join('; ')}"`].join(','));
    });
    const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'bulk_upload_errors.csv'; a.click();
    URL.revokeObjectURL(url);
  };

  const filteredRows = validationResult ? validationResult.rows.filter(r => {
    if (errorFilter === 'errors') return r.errors.length > 0;
    if (errorFilter === 'valid') return r.errors.length === 0;
    return true;
  }) : [];

  const selectedProject = projects.find(p => p.project_id === projectId);

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col" data-testid="bulk-upload-modal">
        <DialogHeader className="flex-shrink-0 pb-2 border-b">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-100 flex items-center justify-center">
              <Upload className="w-5 h-5 text-[#1A4D2E]" />
            </div>
            <div>
              <DialogTitle className="text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>Bulk Upload Farmers</DialogTitle>
              <p className="text-xs text-gray-500 mt-0.5">Upload a CSV to onboard multiple farmers at once</p>
            </div>
          </div>
          {/* Step indicator */}
          <div className="flex items-center gap-1 mt-3">
            {[['1', 'Setup'], ['2', 'Validate'], ['3', 'Onboard']].map(([n, label], i) => {
              const stepMap = { 0: STEP.SETUP, 1: STEP.VALIDATED, 2: STEP.DONE };
              const current = [STEP.SETUP, STEP.VALIDATING].includes(step) ? 0 : [STEP.VALIDATED].includes(step) ? 1 : 2;
              const done = i < current;
              const active = i === current;
              return (
                <React.Fragment key={n}>
                  <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-colors ${active ? 'bg-[#1A4D2E] text-white' : done ? 'bg-emerald-100 text-[#1A4D2E]' : 'bg-gray-100 text-gray-400'}`}>
                    {done ? <CheckCircle className="w-3 h-3" /> : <span>{n}</span>}
                    {label}
                  </div>
                  {i < 2 && <ArrowRight className="w-3 h-3 text-gray-300 flex-shrink-0" />}
                </React.Fragment>
              );
            })}
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto py-4 space-y-4">

          {/* ── STEP 1: SETUP ── */}
          {(step === STEP.SETUP || step === STEP.VALIDATING) && (
            <div className="space-y-4 px-1">
              {/* Project select */}
              <div>
                <Label className="font-medium">Target Project *</Label>
                <Select value={projectId} onValueChange={setProjectId} data-testid="bulk-project-select">
                  <SelectTrigger className="mt-1.5" data-testid="bulk-project-trigger">
                    <SelectValue placeholder="Select a project to map all farmers to" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects.map(p => <SelectItem key={p.project_id} value={p.project_id}>{p.name}</SelectItem>)}
                  </SelectContent>
                </Select>
                {selectedProject && (
                  <p className="text-xs text-gray-500 mt-1">Region: {selectedProject.region} · Rate: ₹{selectedProject.payout_rate}/{selectedProject.payout_rule_type === 'per_tree' ? 'tree' : 'tCO₂e'}</p>
                )}
              </div>

              {/* Template download */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-600 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-blue-800">Download CSV Template</p>
                    <p className="text-xs text-blue-600">Columns: name, phone, land_type, acres, upi_id</p>
                  </div>
                </div>
                <Button variant="outline" size="sm" onClick={downloadTemplate} data-testid="download-template-btn" className="border-blue-300 text-blue-700 hover:bg-blue-100 text-xs">
                  <Download className="w-3 h-3 mr-1.5" /> Template
                </Button>
              </div>

              {/* File drop zone */}
              <div>
                <Label className="font-medium">Upload CSV File *</Label>
                <div
                  data-testid="bulk-csv-dropzone"
                  onDragOver={e => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={e => { e.preventDefault(); setDragOver(false); handleFileSelect(e.dataTransfer.files[0]); }}
                  onClick={() => document.getElementById('bulk-csv-input').click()}
                  className={`mt-1.5 border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${dragOver ? 'border-[#1A4D2E] bg-emerald-50' : file ? 'border-emerald-400 bg-emerald-50/50' : 'border-gray-200 hover:border-[#1A4D2E]/40 hover:bg-gray-50'}`}
                >
                  <input id="bulk-csv-input" type="file" accept=".csv" className="hidden" onChange={e => handleFileSelect(e.target.files[0])} />
                  {file ? (
                    <div className="flex items-center justify-center gap-3">
                      <CheckCircle className="w-8 h-8 text-emerald-600" />
                      <div className="text-left">
                        <p className="text-sm font-semibold text-emerald-800">{file.name}</p>
                        <p className="text-xs text-emerald-600">{(file.size / 1024).toFixed(1)} KB · Click to change</p>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                      <p className="text-sm font-medium text-gray-600">Drop your CSV here or click to browse</p>
                      <p className="text-xs text-gray-400 mt-1">Accepts .csv files only</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Validation rules */}
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <p className="text-xs font-semibold text-amber-800 mb-1.5">Validation Rules</p>
                <ul className="text-xs text-amber-700 space-y-0.5 list-disc list-inside">
                  <li><strong>name</strong>: required, max 100 chars</li>
                  <li><strong>phone</strong>: 10 digits, must start with 6/7/8/9</li>
                  <li><strong>land_type</strong>: "owned" or "leased"</li>
                  <li><strong>acres</strong>: optional, must be a positive number</li>
                  <li><strong>upi_id</strong>: optional</li>
                  <li>Duplicate phones (within CSV or already registered) are flagged</li>
                </ul>
              </div>
            </div>
          )}

          {/* ── STEP 2: VALIDATION RESULTS ── */}
          {step === STEP.VALIDATED && validationResult && (
            <div className="space-y-4 px-1">
              {/* Summary banner */}
              <div className={`rounded-xl p-4 flex items-start gap-3 ${validationResult.error_count === 0 ? 'bg-emerald-50 border border-emerald-200' : 'bg-amber-50 border border-amber-200'}`}>
                {validationResult.error_count === 0
                  ? <CheckCircle className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-0.5" />
                  : <AlertCircle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
                }
                <div className="flex-1">
                  <p className="font-semibold text-sm text-gray-800">
                    {validationResult.error_count === 0
                      ? `All ${validationResult.total_rows} rows are valid — ready to onboard!`
                      : `${validationResult.error_count} row${validationResult.error_count > 1 ? 's' : ''} have errors`
                    }
                  </p>
                  <div className="flex gap-4 mt-1 text-xs">
                    <span className="text-emerald-700 font-medium">{validationResult.valid_count} valid</span>
                    {validationResult.error_count > 0 && <span className="text-red-600 font-medium">{validationResult.error_count} errors</span>}
                    <span className="text-gray-500">{validationResult.total_rows} total rows</span>
                    <span className="text-gray-500">Project: {validationResult.project_name}</span>
                  </div>
                </div>
                {validationResult.error_count > 0 && (
                  <Button variant="outline" size="sm" onClick={downloadErrorReport} data-testid="download-error-report-btn" className="border-amber-300 text-amber-700 hover:bg-amber-100 text-xs flex-shrink-0">
                    <Download className="w-3 h-3 mr-1" /> Error Report
                  </Button>
                )}
              </div>

              {/* Row filter tabs */}
              <div className="flex gap-2">
                {[['all', `All (${validationResult.total_rows})`], ['valid', `Valid (${validationResult.valid_count})`], ['errors', `Errors (${validationResult.error_count})`]].map(([k, label]) => (
                  <button key={k} onClick={() => setErrorFilter(k)} data-testid={`filter-${k}`}
                    className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors ${errorFilter === k ? 'bg-[#1A4D2E] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                    {label}
                  </button>
                ))}
              </div>

              {/* Validation table */}
              <div className="border rounded-xl overflow-hidden">
                <div className="max-h-64 overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-gray-50">
                        <TableHead className="text-xs w-12">Row</TableHead>
                        <TableHead className="text-xs">Name</TableHead>
                        <TableHead className="text-xs">Phone</TableHead>
                        <TableHead className="text-xs">Land</TableHead>
                        <TableHead className="text-xs">Status / Errors</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredRows.map(r => (
                        <TableRow key={r.row} className={r.errors.length > 0 ? 'bg-red-50/50' : 'bg-emerald-50/20'}>
                          <TableCell className="text-xs font-mono text-gray-500">{r.row}</TableCell>
                          <TableCell className="text-xs font-medium">{r.name || <span className="text-red-400 italic">missing</span>}</TableCell>
                          <TableCell className="text-xs font-mono">{r.phone || <span className="text-red-400 italic">missing</span>}</TableCell>
                          <TableCell className="text-xs">{r.land_type || '-'}</TableCell>
                          <TableCell className="text-xs">
                            {r.errors.length === 0
                              ? <span className="text-emerald-600 flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Valid</span>
                              : <div className="space-y-0.5">{r.errors.map((e, i) => <div key={i} className="text-red-600 flex items-start gap-1"><XCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />{e}</div>)}</div>
                            }
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>

              {validationResult.error_count > 0 && validationResult.valid_count === 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
                  <p className="text-sm text-red-700 font-medium">All rows have errors. Fix the CSV and re-upload.</p>
                </div>
              )}
              {validationResult.error_count > 0 && validationResult.valid_count > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-sm text-blue-700"><strong>Partial onboarding:</strong> {validationResult.valid_count} valid rows will be onboarded. {validationResult.error_count} error rows will be skipped.</p>
                </div>
              )}
            </div>
          )}

          {/* ── STEP 3: ONBOARDING SPINNER ── */}
          {step === STEP.ONBOARDING && (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
              <Loader2 className="w-10 h-10 text-[#1A4D2E] animate-spin" />
              <p className="text-sm font-medium text-gray-600">Onboarding {validationResult?.valid_count} farmers...</p>
              <p className="text-xs text-gray-400">Please wait, do not close this window</p>
            </div>
          )}

          {/* ── STEP 4: DONE SUMMARY ── */}
          {step === STEP.DONE && onboardResult && (
            <div className="space-y-4 px-1">
              {/* Success/partial banner */}
              <div className={`rounded-xl p-5 flex items-start gap-4 ${onboardResult.error_count === 0 ? 'bg-emerald-50 border border-emerald-200' : 'bg-amber-50 border border-amber-200'}`}>
                {onboardResult.error_count === 0
                  ? <CheckCircle className="w-8 h-8 text-emerald-600 flex-shrink-0" />
                  : <AlertCircle className="w-8 h-8 text-amber-600 flex-shrink-0" />
                }
                <div>
                  <p className="font-semibold text-gray-800 text-base">
                    {onboardResult.error_count === 0 ? 'All farmers onboarded!' : 'Onboarding complete with some errors'}
                  </p>
                  <div className="flex gap-6 mt-2 text-sm">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-emerald-700">{onboardResult.success_count}</p>
                      <p className="text-xs text-gray-500">Onboarded</p>
                    </div>
                    {onboardResult.error_count > 0 && (
                      <div className="text-center">
                        <p className="text-2xl font-bold text-red-600">{onboardResult.error_count}</p>
                        <p className="text-xs text-gray-500">Failed</p>
                      </div>
                    )}
                    <div className="text-center">
                      <p className="text-sm font-medium text-gray-700 mt-1">{onboardResult.project_name}</p>
                      <p className="text-xs text-gray-500">Project</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Error rows (if any) */}
              {onboardResult.errors?.length > 0 && (
                <div>
                  <p className="text-sm font-semibold text-gray-700 mb-2">Failed rows:</p>
                  <div className="border rounded-xl overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-gray-50">
                          <TableHead className="text-xs w-12">Row</TableHead>
                          <TableHead className="text-xs">Name</TableHead>
                          <TableHead className="text-xs">Phone</TableHead>
                          <TableHead className="text-xs">Reason</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {onboardResult.errors.map((e, i) => (
                          <TableRow key={i} className="bg-red-50/40">
                            <TableCell className="text-xs font-mono text-gray-500">{e.row}</TableCell>
                            <TableCell className="text-xs font-medium">{e.name}</TableCell>
                            <TableCell className="text-xs font-mono">{e.phone}</TableCell>
                            <TableCell className="text-xs text-red-600">{e.reason}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div className="flex-shrink-0 border-t pt-4 flex items-center justify-between">
          <div>
            {step === STEP.VALIDATED && (
              <Button variant="ghost" size="sm" onClick={() => { setStep(STEP.SETUP); setFile(null); setValidationResult(null); }} className="text-gray-500 text-xs">
                Re-upload CSV
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            {step === STEP.DONE
              ? <Button onClick={handleClose} className="bg-[#1A4D2E] text-white hover:bg-[#143C24]">Close</Button>
              : step === STEP.SETUP || step === STEP.VALIDATING
              ? (
                <>
                  <Button variant="outline" onClick={handleClose}>Cancel</Button>
                  <Button
                    onClick={handleValidate}
                    disabled={!projectId || !file || step === STEP.VALIDATING}
                    data-testid="validate-csv-btn"
                    className="bg-[#1A4D2E] text-white hover:bg-[#143C24] disabled:bg-gray-400"
                  >
                    {step === STEP.VALIDATING ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Validating...</> : 'Validate CSV'}
                  </Button>
                </>
              )
              : step === STEP.VALIDATED
              ? (
                <>
                  <Button variant="outline" onClick={handleClose}>Cancel</Button>
                  <Button
                    onClick={handleOnboard}
                    disabled={validationResult?.valid_count === 0}
                    data-testid="confirm-onboard-btn"
                    className="bg-[#1A4D2E] text-white hover:bg-[#143C24] disabled:bg-gray-400"
                  >
                    Confirm Onboard {validationResult?.valid_count > 0 && `(${validationResult.valid_count} farmers)`}
                  </Button>
                </>
              )
              : null
            }
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
