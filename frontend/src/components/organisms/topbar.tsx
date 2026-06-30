import {
  Search,
  Bell,
  Moon,
  Sun,
  MoreHorizontal,
  Users,
  Briefcase,
  Building2,
  FileText,
  Mail,
  Loader2,
} from 'lucide-react';
import { useThemeStore } from '../../store/theme';
import { useAuth } from '../../hooks/useAuth';
import { MobileMenuButton } from './sidebar';
import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDebouncedSearch, useSearch, groupResults } from '../../api/search';

const typeIcon: Record<string, typeof Users> = {
  contact: Users,
  deal: Briefcase,
  account: Building2,
  note: FileText,
  email: Mail,
};

const typeColors: Record<string, string> = {
  contact: 'text-blue-500 bg-blue-50 dark:bg-blue-900/30',
  deal: 'text-green-500 bg-green-50 dark:bg-green-900/30',
  account: 'text-purple-500 bg-purple-50 dark:bg-purple-900/30',
  note: 'text-amber-500 bg-amber-50 dark:bg-amber-900/30',
  email: 'text-cyan-500 bg-cyan-50 dark:bg-cyan-900/30',
};

interface TopBarProps {
  onMenuClick: () => void;
}

export function TopBar({ onMenuClick }: TopBarProps) {
  const { theme, toggle } = useThemeStore();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [profileOpen, setProfileOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);

  // ── Search state ──
  const { rawQuery, setRawQuery, debouncedQuery } = useDebouncedSearch(300);
  const { data, isLoading, isFetching } = useSearch(debouncedQuery);
  const [open, setOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const groups = data?.results ? groupResults(data.results) : [];
  // Flatten all selectable items with their group index
  const flatItems = groups.flatMap((g) => g.items);

  // Reset selected index when results change
  useEffect(() => {
    setSelectedIndex(-1);
  }, [data]);

  // Close on click outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
        setRawQuery('');
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [setRawQuery]);

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!open && e.key === 'Escape') {
        inputRef.current?.blur();
        return;
      }

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((prev) => (prev < flatItems.length - 1 ? prev + 1 : 0));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : flatItems.length - 1));
          break;
        case 'Enter':
          e.preventDefault();
          if (selectedIndex >= 0 && selectedIndex < flatItems.length) {
            const item = flatItems[selectedIndex];
            navigate(item.url);
            setOpen(false);
            setRawQuery('');
            inputRef.current?.blur();
          } else if (flatItems.length > 0) {
            // Navigate to first result
            navigate(flatItems[0].url);
            setOpen(false);
            setRawQuery('');
            inputRef.current?.blur();
          }
          break;
        case 'Escape':
          e.preventDefault();
          setOpen(false);
          setRawQuery('');
          inputRef.current?.blur();
          break;
      }
    },
    [open, flatItems, selectedIndex, navigate, setRawQuery],
  );

  // Scroll selected item into view
  useEffect(() => {
    if (selectedIndex < 0) return;
    const el = dropdownRef.current?.querySelector(`[data-idx="${selectedIndex}"]`);
    el?.scrollIntoView({ block: 'nearest' });
  }, [selectedIndex]);

  const showDropdown = open && rawQuery.trim().length >= 2;

  return (
    <header className="h-16 border-b border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 flex items-center justify-between px-4 lg:px-6">
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <MobileMenuButton onClick={onMenuClick} />

        {/* Search */}
        <div className="relative flex-1 max-w-[200px] sm:max-w-md">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            <input
              ref={inputRef}
              type="text"
              placeholder="Search contacts, deals..."
              className="w-40 md:w-64 lg:w-80 pl-9 pr-4 py-2 text-sm rounded-lg border border-gray-200 dark:border-slate-600 bg-gray-50 dark:bg-slate-800 text-gray-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
              value={rawQuery}
              onChange={(e) => {
                setRawQuery(e.target.value);
                if (e.target.value.trim().length >= 2) setOpen(true);
              }}
              onFocus={() => {
                if (rawQuery.trim().length >= 2) setOpen(true);
              }}
              onKeyDown={handleKeyDown}
              autoComplete="off"
              aria-label="Search contacts, deals"
              aria-expanded={showDropdown}
              aria-haspopup="listbox"
              role="combobox"
            />
            {/* Loading spinner */}
            {(isLoading || isFetching) && showDropdown && (
              <Loader2 size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 animate-spin" />
            )}
          </div>

          {/* Dropdown */}
          {showDropdown && (
            <div
              ref={dropdownRef}
              className="absolute left-0 right-0 top-full mt-1 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-gray-200 dark:border-slate-700 z-50 max-h-96 overflow-y-auto animate-slide-up"
              role="listbox"
            >
              {/* Loading */}
              {isLoading && (
                <div className="flex items-center gap-3 px-4 py-8 text-sm text-gray-400 justify-center">
                  <Loader2 size={18} className="animate-spin" />
                  Searching...
                </div>
              )}

              {/* Results */}
              {!isLoading && data && data.results.length > 0 && (
                <div className="py-1">
                  {groups.map((group) => (
                    <div key={group.type}>
                      {/* Group header */}
                      <div className="flex items-center gap-2 px-4 py-1.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        {group.label}
                      </div>
                      {group.items.map((item) => {
                        const globalIdx = flatItems.indexOf(item);
                        const Icon = typeIcon[item.type] || Search;
                        const isSelected = selectedIndex === globalIdx;
                        return (
                          <button
                            key={item.id}
                            data-idx={globalIdx}
                            className={`w-full flex items-start gap-3 px-4 py-2 text-left transition-colors ${
                              isSelected
                                ? 'bg-brand-50 dark:bg-brand-900/20'
                                : 'hover:bg-gray-50 dark:hover:bg-slate-700/50'
                            }`}
                            onClick={() => {
                              if (item.url) navigate(item.url);
                              setOpen(false);
                              setRawQuery('');
                              inputRef.current?.blur();
                            }}
                            onMouseEnter={() => setSelectedIndex(globalIdx)}
                            role="option"
                            aria-selected={isSelected}
                          >
                            <div
                              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md ${typeColors[item.type] || 'text-gray-400 bg-gray-100'}`}
                            >
                              <Icon size={14} />
                            </div>
                            <div className="min-w-0 flex-1">
                              <div className="text-sm font-medium text-gray-900 dark:text-slate-100 truncate">
                                {item.title}
                              </div>
                              {item.subtitle && (
                                <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                                  {item.subtitle}
                                </div>
                              )}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  ))}
                </div>
              )}

              {/* No results */}
              {!isLoading && data && data.results.length === 0 && (
                <div className="px-4 py-8 text-center">
                  <Search size={24} className="mx-auto mb-2 text-gray-300 dark:text-gray-600" />
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    No results for &ldquo;{data.query}&rdquo;
                  </p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                    Try a different search term
                  </p>
                </div>
              )}

              {/* Recent items placeholder (empty input) - only shows via open flag */}
              {rawQuery.trim().length < 2 && (
                <div className="px-4 py-8 text-center">
                  <Search size={24} className="mx-auto mb-2 text-gray-300 dark:text-gray-600" />
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Type at least 2 characters to search
                  </p>
                </div>
              )}

              {/* Hint */}
              <div className="border-t border-gray-100 dark:border-slate-700 px-4 py-1.5 text-xs text-gray-400 dark:text-gray-500 flex items-center gap-4">
                <span>
                  <kbd className="inline-flex items-center justify-center rounded border border-gray-300 dark:border-slate-600 bg-gray-50 dark:bg-slate-700 px-1.5 font-mono text-[10px] text-gray-500 dark:text-gray-400">
                    ↑↓
                  </kbd>{' '}
                  Navigate
                </span>
                <span>
                  <kbd className="inline-flex items-center justify-center rounded border border-gray-300 dark:border-slate-600 bg-gray-50 dark:bg-slate-700 px-1.5 font-mono text-[10px] text-gray-500 dark:text-gray-400">
                    ⏎
                  </kbd>{' '}
                  Open
                </span>
                <span>
                  <kbd className="inline-flex items-center justify-center rounded border border-gray-300 dark:border-slate-600 bg-gray-50 dark:bg-slate-700 px-1.5 font-mono text-[10px] text-gray-500 dark:text-gray-400">
                    Esc
                  </kbd>{' '}
                  Close
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-1 sm:gap-2 shrink-0">
        {/* Secondary actions - visible on md+, in dropdown on mobile */}
        <div className="hidden md:flex items-center gap-1">
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
        </div>

        {/* Mobile more dropdown */}
        <div className="relative md:hidden">
          <button
            onClick={() => setMoreOpen(!moreOpen)}
            className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
            aria-label="More actions"
          >
            <MoreHorizontal size={18} />
          </button>
          {moreOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setMoreOpen(false)} />
              <div className="absolute right-0 top-full mt-1 w-44 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-gray-200 dark:border-slate-700 py-1 z-20">
                <button
                  onClick={() => { toggle(); setMoreOpen(false); }}
                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-700"
                >
                  {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
                  {theme === 'dark' ? 'Light mode' : 'Dark mode'}
                </button>
                <button
                  onClick={() => { setMoreOpen(false); }}
                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-700"
                >
                  <Bell size={16} />
                  Notifications
                </button>
              </div>
            </>
          )}
        </div>

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