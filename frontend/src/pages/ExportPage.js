import React, { useState, useEffect } from 'react';
import { FileText, Table2, FolderArchive, Calculator, Shield, Download, ChevronRight, Leaf } from 'lucide-react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const exports = [
  {
    id: 'dossier',
    title: 'Project Dossier (PDF)',
    description: 'Comprehensive project narrative for verifiers/buyers. Includes project details, geography, species, monitoring plan, credit methodology, risk controls, and summary stats.',
    icon: FileText,
    endpoint: '/export/dossier-pdf',
    color: '#1A4D2E',
    bg: 'bg-emerald-50',
    badge: 'PDD-Ready',
  },
  {
    id: 'activity',
    title: 'Activity Data (CSV)',
    description: 'One row per activity with farmer info, plot coordinates, species, tree counts, verification status, evidence URLs, and timestamps. The spreadsheet auditors want.',
    icon: Table2,
    endpoint: '/export/activity-csv',
    color: '#B45309',
    bg: 'bg-amber-50',
    badge: 'MRV Data',
  },
  {
    id: 'evidence',
    title: 'Evidence Pack (JSON)',
    description: 'Structured geo-evidence data for every activity: coordinates, photo URLs, farmer IDs, and verification status. Foundation for a data room.',
    icon: FolderArchive,
    endpoint: '/export/evidence-json',
    color: '#059669',
    bg: 'bg-green-50',
    badge: 'Evidence',
  },
  {
    id: 'calculation',
    title: 'Calculation Sheet (CSV)',
    description: 'Transparent estimation math: per-species sequestration factors, survival rates, conservative discounts, formulas, and resulting tCO2e per activity.',
    icon: Calculator,
    endpoint: '/export/calculation-sheet',
    color: '#7C3AED',
    bg: 'bg-purple-50',
    badge: 'Quantification',
  },
  {
    id: 'audit',
    title: 'Audit Log (CSV)',
    description: 'Complete audit trail: who approved/rejected what, when, with notes. Chain of custody for every activity action.',
    icon: Shield,
    endpoint: '/export/audit-log',
    color: '#DC2626',
    bg: 'bg-red-50',
    badge: 'Audit',
  },
];

export default function ExportPage() {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState('all');
  const [downloading, setDownloading] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API}/projects`, { credentials: 'include' });
        if (res.ok) setProjects(await res.json());
      } catch {}
    })();
  }, []);

  const handleDownload = async (exp) => {
    setDownloading(exp.id);
    try {
      const url = selectedProject !== 'all' ? `${API}${exp.endpoint}?project_id=${selectedProject}` : `${API}${exp.endpoint}`;
      const res = await fetch(url, { credentials: 'include' });
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      const cd = res.headers.get('Content-Disposition');
      const filename = cd ? cd.split('filename=')[1] : `export_${exp.id}.${exp.endpoint.includes('pdf') ? 'pdf' : exp.endpoint.includes('json') ? 'json' : 'csv'}`;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(a.href);
      toast.success(`${exp.title} downloaded`);
    } catch {
      toast.error(`Failed to export ${exp.title}`);
    }
    setDownloading(null);
  };

  return (
    <div data-testid="export-page" className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-[#1F2937] tracking-tight" style={{ fontFamily: 'Manrope, sans-serif' }}>Export Center</h1>
        <p className="text-[#6B7280] mt-1">Generate MRV-ready evidence packs and project documentation</p>
      </div>

      {/* Disactivityer */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3" data-testid="export-disactivityer">
        <Leaf className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
        <div>
          <p className="text-sm font-medium text-amber-800">Estimated Units — Not Issued Credits</p>
          <p className="text-xs text-amber-600 mt-0.5">All exported data contains estimated values. Final carbon credit issuance depends on third-party verification and registry approval.</p>
        </div>
      </div>

      {/* Project Filter */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-[#6B7280]">Export for:</span>
        <Select value={selectedProject} onValueChange={setSelectedProject}>
          <SelectTrigger className="w-[260px]" data-testid="export-project-filter">
            <SelectValue placeholder="Select project" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Projects</SelectItem>
            {projects.map(p => <SelectItem key={p.project_id} value={p.project_id}>{p.name}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {/* Export Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {exports.map((exp) => (
          <Card key={exp.id} data-testid={`export-card-${exp.id}`} className="bg-white border border-gray-100 rounded-xl shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:shadow-md transition-all duration-300 group">
            <CardContent className="p-6 flex flex-col h-full">
              <div className="flex items-start justify-between mb-4">
                <div className={`${exp.bg} p-3 rounded-xl`}>
                  <exp.icon className="w-5 h-5" style={{ color: exp.color }} />
                </div>
                <Badge variant="outline" className="text-[10px]" style={{ borderColor: exp.color + '40', color: exp.color }}>{exp.badge}</Badge>
              </div>
              <h3 className="text-base font-semibold text-[#1F2937] mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>{exp.title}</h3>
              <p className="text-xs text-[#6B7280] leading-relaxed flex-1 mb-4">{exp.description}</p>
              <Button
                onClick={() => handleDownload(exp)}
                disabled={downloading === exp.id}
                data-testid={`download-${exp.id}`}
                className="w-full bg-white text-[#1F2937] border border-gray-200 hover:bg-gray-50 hover:border-gray-300 shadow-sm font-medium transition-all group-hover:border-gray-300"
              >
                {downloading === exp.id ? (
                  <span className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-[#1A4D2E] border-t-transparent rounded-full animate-spin" />
                    Generating...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Download className="w-4 h-4" /> Download
                    <ChevronRight className="w-3 h-3 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                  </span>
                )}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Info */}
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-[#1F2937] mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>Why these exports help carbon credit issuance</h3>
        <ul className="space-y-2 text-xs text-[#6B7280]">
          <li className="flex items-start gap-2"><ChevronRight className="w-3 h-3 mt-0.5 text-[#1A4D2E] flex-shrink-0" /> <span><strong>Project Dossier</strong> becomes the backbone of a PDD/PoA narrative. Verifiers love a clean "single source of truth."</span></li>
          <li className="flex items-start gap-2"><ChevronRight className="w-3 h-3 mt-0.5 text-[#1A4D2E] flex-shrink-0" /> <span><strong>Activity Data CSV</strong> — MRV and credit quantification always starts from structured data. A clean CSV saves weeks.</span></li>
          <li className="flex items-start gap-2"><ChevronRight className="w-3 h-3 mt-0.5 text-[#1A4D2E] flex-shrink-0" /> <span><strong>Evidence Pack</strong> — Most delays happen because evidence is scattered. A structured vault reduces cycle time.</span></li>
          <li className="flex items-start gap-2"><ChevronRight className="w-3 h-3 mt-0.5 text-[#1A4D2E] flex-shrink-0" /> <span><strong>Calculation Sheet</strong> — Verifiers need to reproduce numbers. Explicit assumptions speed up validation.</span></li>
          <li className="flex items-start gap-2"><ChevronRight className="w-3 h-3 mt-0.5 text-[#1A4D2E] flex-shrink-0" /> <span><strong>Audit Log</strong> — Clean chain of custody removes blockers on "who approved what when."</span></li>
        </ul>
      </div>
    </div>
  );
}
