import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LayoutDashboard, TreePine, Users, ClipboardCheck, Award, Wallet, FileDown, LogOut, ChevronLeft, ChevronRight } from 'lucide-react';
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

export default function Sidebar({ collapsed, setCollapsed }) {
  const { user, logout } = useAuth();
  const location = useLocation();

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
    </TooltipProvider>
  );
}
