import React, { useState, useEffect } from 'react';
import { Award, Plus, TrendingUp, CheckCircle2, DollarSign, XCircle, Trash2, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '../components/ui/alert-dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const statusColors = {
  issued: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  approved: 'bg-blue-50 text-blue-700 border-blue-200',
  sold: 'bg-amber-50 text-amber-700 border-amber-200',
  retired: 'bg-gray-100 text-gray-600 border-gray-300',
};

const registries = ['Verra VCS', 'Gold Standard', 'India Carbon Market', 'Other'];

export default function CreditsPage() {
  const [credits, setCredits] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showLogDialog, setShowLogDialog] = useState(false);
  const [showStatusDialog, setShowStatusDialog] = useState(false);
  const [selectedCredit, setSelectedCredit] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);
  
  // Form states
  const [projectId, setProjectId] = useState('');
  const [registryName, setRegistryName] = useState('');
  const [creditsIssued, setCreditsIssued] = useState('');
  const [issuanceDate, setIssuanceDate] = useState('');
  const [vintageYear, setVintageYear] = useState(new Date().getFullYear().toString());
  const [registryReference, setRegistryReference] = useState('');
  const [serialNumbers, setSerialNumbers] = useState('');
  const [notes, setNotes] = useState('');
  
  // Status update states
  const [newStatus, setNewStatus] = useState('');
  const [buyerName, setBuyerName] = useState('');
  const [salePricePerCredit, setSalePricePerCredit] = useState('');
  const [saleDate, setSaleDate] = useState('');
  const [retirementReason, setRetirementReason] = useState('');
  const [retirementBeneficiary, setRetirementBeneficiary] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [creditsRes, projectsRes] = await Promise.all([
        fetch(`${API}/credits`, { credentials: 'include' }),
        fetch(`${API}/projects`, { credentials: 'include' }),
      ]);
      if (creditsRes.ok) setCredits(await creditsRes.json());
      if (projectsRes.ok) setProjects(await projectsRes.json());
    } catch (error) {
      toast.error('Failed to load data');
    }
    setLoading(false);
  };

  const handleLogIssuance = async () => {
    try {
      const res = await fetch(`${API}/credits`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          project_id: projectId,
          registry_name: registryName,
          credits_issued: parseFloat(creditsIssued),
          issuance_date: issuanceDate,
          vintage_year: parseInt(vintageYear),
          registry_reference: registryReference,
          serial_numbers: serialNumbers,
          notes: notes,
        }),
      });
      if (res.ok) {
        toast.success('Credit issuance logged successfully');
        setShowLogDialog(false);
        resetForm();
        fetchData();
      } else {
        toast.error('Failed to log issuance');
      }
    } catch (error) {
      toast.error('Error logging issuance');
    }
  };

  const handleStatusUpdate = async () => {
    try {
      const payload = {
        status: newStatus,
        notes: notes,
      };
      
      if (newStatus === 'approved') {
        payload.approved_date = saleDate || new Date().toISOString().split('T')[0];
      } else if (newStatus === 'sold') {
        payload.buyer_name = buyerName;
        payload.sale_price_per_credit = parseFloat(salePricePerCredit);
        payload.sale_date = saleDate || new Date().toISOString().split('T')[0];
      } else if (newStatus === 'retired') {
        payload.retired_date = saleDate || new Date().toISOString().split('T')[0];
        payload.retirement_reason = retirementReason;
        payload.retirement_beneficiary = retirementBeneficiary;
      }

      const res = await fetch(`${API}/credits/${selectedCredit.credit_id}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        toast.success(`Credit status updated to ${newStatus}`);
        setShowStatusDialog(false);
        resetForm();
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Failed to update status');
      }
    } catch (error) {
      toast.error('Error updating status');
    }
  };

  const resetForm = () => {
    setProjectId('');
    setRegistryName('');
    setCreditsIssued('');
    setIssuanceDate('');
    setVintageYear(new Date().getFullYear().toString());
    setRegistryReference('');
    setSerialNumbers('');
    setNotes('');
    setBuyerName('');
    setSalePricePerCredit('');
    setSaleDate('');
    setRetirementReason('');
    setRetirementBeneficiary('');
  };

  const filteredCredits = statusFilter === 'all' 
    ? credits 
    : credits.filter(c => c.status === statusFilter);

  // Calculate summary stats
  const totalIssued = credits.reduce((sum, c) => sum + c.credits_issued, 0);
  const totalApproved = credits.filter(c => c.status === 'approved').reduce((sum, c) => sum + c.credits_issued, 0);
  const totalSold = credits.filter(c => c.status === 'sold').reduce((sum, c) => sum + c.credits_issued, 0);
  const totalRevenue = credits.filter(c => c.status === 'sold').reduce((sum, c) => sum + (c.total_revenue || 0), 0);
  const totalRetired = credits.filter(c => c.status === 'retired').reduce((sum, c) => sum + c.credits_issued, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-[#1A4D2E] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1F2937]">Carbon Credits</h1>
          <p className="text-[#6B7280] mt-1">Registry-issued carbon credits lifecycle management</p>
        </div>
        <Button onClick={() => setShowLogDialog(true)} className="bg-[#1A4D2E] hover:bg-[#15401F]">
          <Plus className="w-4 h-4 mr-2" />
          Log Issuance
        </Button>
      </div>

      {/* Info Banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <p className="text-sm text-amber-800">
          <strong>Note:</strong> These are registry-issued carbon credits (VCUs/CCCs). Distinct from estimated units shown elsewhere.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Issued</p>
                <p className="text-2xl font-bold text-emerald-600">{totalIssued.toFixed(2)}</p>
                <p className="text-xs text-gray-500">tCO₂e</p>
              </div>
              <Award className="w-8 h-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Approved for Sale</p>
                <p className="text-2xl font-bold text-blue-600">{totalApproved.toFixed(2)}</p>
                <p className="text-xs text-gray-500">tCO₂e</p>
              </div>
              <CheckCircle2 className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Sold</p>
                <p className="text-2xl font-bold text-amber-600">{totalSold.toFixed(2)}</p>
                <p className="text-xs text-gray-500">₹{totalRevenue.toLocaleString('en-IN')}</p>
              </div>
              <DollarSign className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Retired</p>
                <p className="text-2xl font-bold text-gray-600">{totalRetired.toFixed(2)}</p>
                <p className="text-xs text-gray-500">tCO₂e</p>
              </div>
              <XCircle className="w-8 h-8 text-gray-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter Tabs */}
      <Tabs value={statusFilter} onValueChange={setStatusFilter}>
        <TabsList>
          <TabsTrigger value="all">All ({credits.length})</TabsTrigger>
          <TabsTrigger value="issued">Issued ({credits.filter(c => c.status === 'issued').length})</TabsTrigger>
          <TabsTrigger value="approved">Approved ({credits.filter(c => c.status === 'approved').length})</TabsTrigger>
          <TabsTrigger value="sold">Sold ({credits.filter(c => c.status === 'sold').length})</TabsTrigger>
          <TabsTrigger value="retired">Retired ({credits.filter(c => c.status === 'retired').length})</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Credits List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filteredCredits.length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-500">
            No credits found. Log your first credit issuance to get started.
          </div>
        ) : (
          filteredCredits.map((credit) => (
            <Card key={credit.credit_id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <Badge className={`${statusColors[credit.status]} mb-2`}>
                      {credit.status.toUpperCase()}
                    </Badge>
                    <CardTitle className="text-lg">{credit.project_name}</CardTitle>
                    <p className="text-sm text-gray-600 mt-1">{credit.registry_name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-emerald-600">{credit.credits_issued}</p>
                    <p className="text-xs text-gray-500">tCO₂e</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-gray-600">Issuance Date</p>
                    <p className="font-medium">{credit.issuance_date}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Vintage Year</p>
                    <p className="font-medium">{credit.vintage_year || 'N/A'}</p>
                  </div>
                </div>
                
                {credit.registry_reference && (
                  <div className="text-sm">
                    <p className="text-gray-600">Registry Reference</p>
                    <p className="font-medium text-xs">{credit.registry_reference}</p>
                  </div>
                )}

                {credit.serial_numbers && (
                  <div className="text-sm">
                    <p className="text-gray-600">Serial Numbers</p>
                    <p className="font-medium text-xs">{credit.serial_numbers}</p>
                  </div>
                )}

                {credit.status === 'sold' && (
                  <div className="bg-amber-50 rounded p-3 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Buyer:</span>
                      <span className="font-medium">{credit.buyer_name}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Price:</span>
                      <span className="font-medium">₹{credit.sale_price_per_credit}/tCO₂e</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Total Revenue:</span>
                      <span className="font-bold text-amber-700">₹{(credit.total_revenue || 0).toLocaleString('en-IN')}</span>
                    </div>
                  </div>
                )}

                {credit.status === 'retired' && (
                  <div className="bg-gray-50 rounded p-3 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Reason:</span>
                      <span className="font-medium">{credit.retirement_reason}</span>
                    </div>
                    {credit.retirement_beneficiary && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Beneficiary:</span>
                        <span className="font-medium">{credit.retirement_beneficiary}</span>
                      </div>
                    )}
                  </div>
                )}

                {credit.notes && (
                  <div className="text-sm">
                    <p className="text-gray-600">Notes</p>
                    <p className="text-gray-700">{credit.notes}</p>
                  </div>
                )}

                <Button
                  onClick={() => {
                    setSelectedCredit(credit);
                    setShowStatusDialog(true);
                  }}
                  variant="outline"
                  size="sm"
                  className="w-full"
                  disabled={credit.status === 'retired'}
                >
                  Update Status
                </Button>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Log Issuance Dialog */}
      <Dialog open={showLogDialog} onOpenChange={setShowLogDialog}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Log Credit Issuance</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Project *</Label>
              <Select value={projectId} onValueChange={setProjectId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select project" />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((p) => (
                    <SelectItem key={p.project_id} value={p.project_id}>
                      {p.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Registry *</Label>
              <Select value={registryName} onValueChange={setRegistryName}>
                <SelectTrigger>
                  <SelectValue placeholder="Select registry" />
                </SelectTrigger>
                <SelectContent>
                  {registries.map((r) => (
                    <SelectItem key={r} value={r}>{r}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Credits Issued (tCO₂e) *</Label>
              <Input
                type="number"
                step="0.01"
                value={creditsIssued}
                onChange={(e) => setCreditsIssued(e.target.value)}
                placeholder="e.g., 12.5"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Issuance Date *</Label>
                <Input
                  type="date"
                  value={issuanceDate}
                  onChange={(e) => setIssuanceDate(e.target.value)}
                />
              </div>
              <div>
                <Label>Vintage Year</Label>
                <Input
                  type="number"
                  value={vintageYear}
                  onChange={(e) => setVintageYear(e.target.value)}
                  placeholder="2026"
                />
              </div>
            </div>

            <div>
              <Label>Registry Reference</Label>
              <Input
                value={registryReference}
                onChange={(e) => setRegistryReference(e.target.value)}
                placeholder="e.g., VCS-1234-5678"
              />
            </div>

            <div>
              <Label>Serial Numbers</Label>
              <Input
                value={serialNumbers}
                onChange={(e) => setSerialNumbers(e.target.value)}
                placeholder="e.g., VCU-001 to VCU-013"
              />
            </div>

            <div>
              <Label>Notes</Label>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Additional notes..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowLogDialog(false)}>Cancel</Button>
            <Button
              onClick={handleLogIssuance}
              disabled={!projectId || !registryName || !creditsIssued || !issuanceDate}
              className="bg-[#1A4D2E] hover:bg-[#15401F]"
            >
              Log Issuance
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Status Update Dialog */}
      <Dialog open={showStatusDialog} onOpenChange={setShowStatusDialog}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Update Credit Status</DialogTitle>
          </DialogHeader>
          {selectedCredit && (
            <div className="space-y-4 py-4">
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-sm text-gray-600">Current Status</p>
                <Badge className={`${statusColors[selectedCredit.status]} mt-1`}>
                  {selectedCredit.status.toUpperCase()}
                </Badge>
              </div>

              <div>
                <Label>New Status *</Label>
                <Select value={newStatus} onValueChange={setNewStatus}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select new status" />
                  </SelectTrigger>
                  <SelectContent>
                    {selectedCredit.status === 'issued' && (
                      <SelectItem value="approved">Approved for Sale</SelectItem>
                    )}
                    {selectedCredit.status === 'approved' && (
                      <>
                        <SelectItem value="sold">Sold</SelectItem>
                        <SelectItem value="issued">Revert to Issued</SelectItem>
                      </>
                    )}
                    {selectedCredit.status === 'sold' && (
                      <>
                        <SelectItem value="retired">Retired</SelectItem>
                        <SelectItem value="approved">Revert to Approved</SelectItem>
                      </>
                    )}
                  </SelectContent>
                </Select>
              </div>

              {newStatus === 'sold' && (
                <>
                  <div>
                    <Label>Buyer Name *</Label>
                    <Input
                      value={buyerName}
                      onChange={(e) => setBuyerName(e.target.value)}
                      placeholder="Company name or individual"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label>Price per tCO₂e (₹) *</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={salePricePerCredit}
                        onChange={(e) => setSalePricePerCredit(e.target.value)}
                        placeholder="e.g., 1500"
                      />
                    </div>
                    <div>
                      <Label>Sale Date</Label>
                      <Input
                        type="date"
                        value={saleDate}
                        onChange={(e) => setSaleDate(e.target.value)}
                      />
                    </div>
                  </div>
                  {salePricePerCredit && (
                    <div className="bg-amber-50 p-3 rounded">
                      <p className="text-sm text-gray-600">Estimated Total Revenue</p>
                      <p className="text-xl font-bold text-amber-700">
                        ₹{(selectedCredit.credits_issued * parseFloat(salePricePerCredit)).toLocaleString('en-IN')}
                      </p>
                      <p className="text-xs text-amber-600 mt-1">
                        Benefit sharing will be auto-calculated across farmers
                      </p>
                    </div>
                  )}
                </>
              )}

              {newStatus === 'retired' && (
                <>
                  <div>
                    <Label>Retirement Reason *</Label>
                    <Select value={retirementReason} onValueChange={setRetirementReason}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select reason" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="offset">Offset</SelectItem>
                        <SelectItem value="compliance">Compliance</SelectItem>
                        <SelectItem value="voluntary">Voluntary</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Beneficiary</Label>
                    <Input
                      value={retirementBeneficiary}
                      onChange={(e) => setRetirementBeneficiary(e.target.value)}
                      placeholder="Who claims the offset?"
                    />
                  </div>
                  <div>
                    <Label>Retirement Date</Label>
                    <Input
                      type="date"
                      value={saleDate}
                      onChange={(e) => setSaleDate(e.target.value)}
                    />
                  </div>
                </>
              )}

              <div>
                <Label>Notes</Label>
                <Textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Additional notes about this status change..."
                  rows={3}
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowStatusDialog(false)}>Cancel</Button>
            <Button
              onClick={handleStatusUpdate}
              disabled={!newStatus || (newStatus === 'sold' && (!buyerName || !salePricePerCredit)) || (newStatus === 'retired' && !retirementReason)}
              className="bg-[#1A4D2E] hover:bg-[#15401F]"
            >
              Update Status
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
