import { Search, Bell, Moon, Sun } from 'lucide-react';
import { useThemeStore } from '../../store/theme';
import { useAuth } from '../../hooks/useAuth';
import { MobileMenuButton } from './sidebar';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface TopBarProps {
  onMenuClick: () => void;
}

export function TopBar({ onMenuClick }: TopBarProps) {
  const { theme, toggle } = useThemeStore();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchOpen, setSearchOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  return (
    <header className="h-16 border-b border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 flex items-center justify-between px-4 lg:px-6">
      <div className="flex items-center gap-3">
        <MobileMenuButton onClick={onMenuClick} />
        {/* Search */}
        <div className="hidden sm:flex relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search contacts, deals..."
            className="w-64 lg:w-80 pl-9 pr-4 py-2 text-sm rounded-lg border border-gray-200 dark:border-slate-600 bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
            onFocus={() => navigate('/contacts')}
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* Theme toggle */}
        <button
          onClick={toggle}
          className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* Notifications */}
        <button className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors relative">
          <Bell size={18} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-500" />
        </button>

        {/* Profile dropdown */}
        <div className="relative">
          <button
            onClick={() => setProfileOpen(!profileOpen)}
            className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 dark:bg-brand-900/50 text-brand-700 dark:text-brand-300 text-sm font-medium">
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </div>
            <span className="hidden md:block text-sm font-medium text-gray-700 dark:text-slate-300">
              {user?.first_name}
            </span>
          </button>

          {profileOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setProfileOpen(false)} />
              <div className="absolute right-0 top-full mt-1 w-48 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-gray-200 dark:border-slate-700 py-1 z-20 animate-slide-up">
                <button
                  onClick={() => { navigate('/settings'); setProfileOpen(false); }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-700"
                >
                  Settings
                </button>
                <button
                  onClick={() => { logout(); setProfileOpen(false); }}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-50 dark:hover:bg-slate-700"
                >
                  Sign out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}