import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  TrendingUp,
  Calendar,
  Mail,
  Settings,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  BarChart3,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useAuth } from '../../hooks/useAuth';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/contacts', icon: Users, label: 'Contacts' },
  { to: '/pipeline', icon: TrendingUp, label: 'Pipeline' },
  { to: '/activities', icon: Calendar, label: 'Activities' },
  { to: '/email', icon: Mail, label: 'Email' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }: SidebarProps) {
  const location = useLocation();
  const { user } = useAuth();

  const sidebarContent = (
    <div className="flex h-full flex-col bg-white dark:bg-slate-900 border-r border-gray-200 dark:border-slate-700">
      {/* Logo area */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-gray-200 dark:border-slate-700">
        <Link to="/dashboard" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white font-bold text-sm">
            F
          </div>
          {!collapsed && (
            <span className="font-semibold text-gray-900 dark:text-slate-100 text-base">
              FrontierCRM
            </span>
          )}
        </Link>
        <button
          onClick={onToggle}
          className="hidden lg:flex h-8 w-8 items-center justify-center rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-slate-800"
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Nav items */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        {navItems.map((item) => {
          const isActive = location.pathname.startsWith(item.to);
          return (
            <Link
              key={item.to}
              to={item.to}
              onClick={onMobileClose}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300'
                  : 'text-gray-600 hover:bg-gray-100 dark:text-slate-400 dark:hover:bg-slate-800'
              )}
            >
              <item.icon size={20} className={cn(isActive ? 'text-brand-600 dark:text-brand-400' : '')} />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* User area */}
      {!collapsed && user && (
        <div className="p-4 border-t border-gray-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 dark:bg-brand-900/50 text-brand-700 dark:text-brand-300 text-sm font-medium">
              {user.first_name?.[0]}{user.last_name?.[0]}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-gray-900 dark:text-slate-100 truncate">
                {user.first_name} {user.last_name}
              </p>
              <p className="text-xs text-gray-500 dark:text-slate-400 truncate">{user.email}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={cn(
          'hidden lg:flex h-screen flex-col transition-all duration-200',
          collapsed ? 'w-16' : 'w-64'
        )}
      >
        {sidebarContent}
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={onMobileClose} />
          <aside className="absolute left-0 top-0 h-full w-72 bg-white dark:bg-slate-900 shadow-xl z-10">
            <div className="flex justify-end p-2">
              <button
                onClick={onMobileClose}
                className="p-2 rounded-md text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
}

export function MobileMenuButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="lg:hidden p-2 rounded-md text-gray-500 hover:bg-gray-100 dark:hover:bg-slate-800"
      aria-label="Open menu"
    >
      <Menu size={20} />
    </button>
  );
}