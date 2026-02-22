import React, { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LayoutDashboard, TreePine, Users, ClipboardCheck, Award, Wallet, FileDown, LogOut, ChevronLeft, ChevronRight, Map, X, ZoomIn, ZoomOut } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Button } from '../components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../components/ui/tooltip';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/projects', icon: TreePine, label: 'Projects' },
  { to: '/farmers', icon: Users, label: 'Farmers' },
  { to: '/verification', icon: ClipboardCheck, label: 'Verification' },
  { to: '/credits', icon: Award, label: 'Credits' },
  { to: '/ledger', icon: Wallet, label: 'Ledger' },
  { to: '/exports', icon: FileDown, label: 'Exports' },
];

const WORKFLOW_URL = `${process.env.REACT_APP_BACKEND_URL}/api/static/workflow`;

export default function Sidebar({ collapsed, setCollapsed }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [showWorkflow, setShowWorkflow] = useState(false);
  const [zoom, setZoom] = useState(1);

  // Close on Escape key
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') setShowWorkflow(false); };
    if (showWorkflow) window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [showWorkflow]);

  // Reset zoom when opening
  const openWorkflow = () => { setZoom(1); setShowWorkflow(true); };

  const workflowBtn = (
    <button
      onClick={openWorkflow}
      data-testid="workflow-diagram-btn"
      className={`w-full flex items-center gap-3 rounded-lg transition-all duration-200 group px-3 py-2.5 text-[#6B7280] hover:bg-emerald-50 hover:text-[#1A4D2E] ${collapsed ? 'justify-center px-2' : ''}`}
    >
      <Map className="w-[18px] h-[18px] flex-shrink-0 text-[#6B7280] group-hover:text-[#1A4D2E]" />
      {!collapsed && <span className="text-sm font-medium">Workflow</span>}
    </button>
  );

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        data-testid="sidebar"
        className={`fixed left-0 top-0 h-screen bg-[#F7F6F3] border-r border-gray-200/60 flex flex-col transition-all duration-300 z-40 ${collapsed ? 'w-[68px]' : 'w-[240px]'}`}
      >
        {/* Logo */}
        <div className={`flex items-center h-16 border-b border-gray-200/60 ${collapsed ? 'justify-center px-2' : 'px-5'}`}>
          {!collapsed && (
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 bg-[#1A4D2E] rounded-lg flex items-center justify-center">
                <TreePine className="w-4.5 h-4.5 text-white" />
              </div>
              <span className="font-bold text-[#1A4D2E] text-base tracking-tight" style={{ fontFamily: 'Manrope, sans-serif' }}>VanaLedger</span>
            </div>
          )}
          {collapsed && (
            <div className="w-8 h-8 bg-[#1A4D2E] rounded-lg flex items-center justify-center">
              <TreePine className="w-4.5 h-4.5 text-white" />
            </div>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label }) => {
            const isActive = location.pathname === to || location.pathname.startsWith(to + '/');
            const link = (
              <NavLink
                key={to}
                to={to}
                data-testid={`nav-${label.toLowerCase()}`}
                className={`flex items-center gap-3 rounded-lg transition-all duration-200 group ${collapsed ? 'justify-center px-2 py-2.5' : 'px-3 py-2.5'} ${isActive ? 'bg-[#1A4D2E] text-white shadow-sm' : 'text-[#6B7280] hover:bg-gray-200/50 hover:text-[#1F2937]'}`}
              >
                <Icon className={`w-[18px] h-[18px] flex-shrink-0 ${isActive ? 'text-white' : 'text-[#6B7280] group-hover:text-[#1F2937]'}`} />
                {!collapsed && <span className="text-sm font-medium">{label}</span>}
              </NavLink>
            );
            return collapsed ? (
              <Tooltip key={to}>
                <TooltipTrigger asChild>{link}</TooltipTrigger>
                <TooltipContent side="right" className="bg-[#1F2937] text-white text-xs">
                  {label}
                </TooltipContent>
              </Tooltip>
            ) : link;
          })}
        </nav>

        {/* Workflow button */}
        <div className="px-2 pb-1">
          {collapsed ? (
            <Tooltip>
              <TooltipTrigger asChild>{workflowBtn}</TooltipTrigger>
              <TooltipContent side="right" className="bg-[#1F2937] text-white text-xs">View Workflow</TooltipContent>
            </Tooltip>
          ) : (
            <div className="border-t border-gray-200/60 pt-2">
              {workflowBtn}
            </div>
          )}
        </div>

        {/* Collapse toggle */}
        <div className="px-2 pb-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCollapsed(!collapsed)}
            data-testid="sidebar-toggle"
            className="w-full flex items-center justify-center text-[#6B7280] hover:text-[#1F2937] hover:bg-gray-200/50 py-2"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </Button>
        </div>

        {/* User */}
        <div className={`border-t border-gray-200/60 p-3 ${collapsed ? 'flex justify-center' : ''}`}>
          {collapsed ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <button onClick={logout} data-testid="logout-btn" className="p-1">
                  <Avatar className="w-8 h-8">
                    <AvatarImage src={user?.picture} />
                    <AvatarFallback className="bg-[#1A4D2E] text-white text-xs">{user?.name?.[0] || 'U'}</AvatarFallback>
                  </Avatar>
                </button>
              </TooltipTrigger>
              <TooltipContent side="right" className="bg-[#1F2937] text-white text-xs">Logout</TooltipContent>
            </Tooltip>
          ) : (
            <div className="flex items-center gap-2.5">
              <Avatar className="w-8 h-8">
                <AvatarImage src={user?.picture} />
                <AvatarFallback className="bg-[#1A4D2E] text-white text-xs">{user?.name?.[0] || 'U'}</AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[#1F2937] truncate">{user?.name}</p>
                <p className="text-xs text-[#6B7280] truncate">{user?.email}</p>
              </div>
              <button onClick={logout} data-testid="logout-btn" className="p-1.5 rounded-md text-[#6B7280] hover:text-red-500 hover:bg-red-50 transition-colors">
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* ── Full-Screen Workflow Overlay ── */}
      {showWorkflow && (
        <div
          className="fixed inset-0 z-[9999] flex flex-col bg-black/90"
          style={{ backdropFilter: 'blur(4px)' }}
        >
          {/* Top bar */}
          <div className="flex-shrink-0 flex items-center justify-between px-6 py-3 bg-black/60 border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-7 h-7 bg-[#1A4D2E] rounded-md flex items-center justify-center">
                <Map className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-white font-semibold text-sm" style={{ fontFamily: 'Manrope, sans-serif' }}>VanaLedger — User Workflow</p>
                <p className="text-white/50 text-xs">Tree Plantation: Onboarding to Verification</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* Zoom controls */}
              <button
                onClick={() => setZoom(z => Math.max(0.5, z - 0.25))}
                className="w-8 h-8 rounded-md bg-white/10 hover:bg-white/20 flex items-center justify-center text-white/70 hover:text-white transition-colors"
                title="Zoom out"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="text-white/50 text-xs w-10 text-center">{Math.round(zoom * 100)}%</span>
              <button
                onClick={() => setZoom(z => Math.min(3, z + 0.25))}
                className="w-8 h-8 rounded-md bg-white/10 hover:bg-white/20 flex items-center justify-center text-white/70 hover:text-white transition-colors"
                title="Zoom in"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
              <button
                onClick={() => setZoom(1)}
                className="px-2.5 h-8 rounded-md bg-white/10 hover:bg-white/20 text-white/70 hover:text-white text-xs transition-colors"
              >
                Fit
              </button>
              <div className="w-px h-5 bg-white/20 mx-1" />
              {/* Close */}
              <button
                onClick={() => setShowWorkflow(false)}
                data-testid="workflow-close-btn"
                className="w-8 h-8 rounded-md bg-white/10 hover:bg-red-500/70 flex items-center justify-center text-white/70 hover:text-white transition-colors"
                title="Close (Esc)"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Image area — scrollable if zoomed in */}
          <div
            className="flex-1 overflow-auto flex items-start justify-center p-6"
            onClick={(e) => { if (e.target === e.currentTarget) setShowWorkflow(false); }}
          >
            <img
              src={WORKFLOW_URL}
              alt="VanaLedger User Workflow"
              data-testid="workflow-image"
              style={{
                transform: `scale(${zoom})`,
                transformOrigin: 'top center',
                transition: 'transform 0.2s ease',
                maxWidth: zoom === 1 ? '100%' : 'none',
                height: zoom === 1 ? 'auto' : 'auto',
                borderRadius: '12px',
                boxShadow: '0 25px 60px rgba(0,0,0,0.5)',
              }}
              draggable={false}
            />
          </div>

          {/* Bottom hint */}
          <div className="flex-shrink-0 flex items-center justify-center py-2 border-t border-white/10 bg-black/40">
            <p className="text-white/30 text-xs">Press <kbd className="bg-white/10 text-white/50 px-1.5 py-0.5 rounded text-xs">Esc</kbd> or click outside the diagram to close</p>
          </div>
        </div>
      )}
    </TooltipProvider>
  );
}
