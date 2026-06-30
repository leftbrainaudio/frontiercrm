import { useQuery } from '@tanstack/react-query';
import { useState, useEffect, useRef } from 'react';
import apiClient from './client';

export interface SearchResult {
  id: string;
  type: 'contact' | 'deal' | 'account' | 'note' | 'email';
  title: string;
  subtitle: string;
  url: string;
}

interface SimpleSearchResponse {
  results: SearchResult[];
  query: string;
  total: number;
}

/** Hook that provides debounced search state + query. */
export function useDebouncedSearch(delayMs = 300) {
  const [rawQuery, setRawQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setDebouncedQuery(rawQuery);
    }, delayMs);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [rawQuery, delayMs]);

  return { rawQuery, setRawQuery, debouncedQuery };
}

/** React Query hook — fetches search results from the simple ORM endpoint. */
export function useSearch(query: string) {
  const trimmed = query.trim();
  const enabled = trimmed.length >= 2;

  return useQuery({
    queryKey: ['search', trimmed],
    queryFn: () =>
      apiClient
        .get<SimpleSearchResponse>('/search/simple/', { params: { q: trimmed, limit: 10 } })
        .then((r) => r.data),
    enabled,
    staleTime: 30_000, // cache for 30s
    retry: false,
  });
}

/** Group search results by type for display. */
export function groupResults(results: SearchResult[]) {
  const groups: { type: string; label: string; icon: string; items: SearchResult[] }[] = [];
  const order = ['contact', 'deal', 'account', 'note', 'email'] as const;
  const labels: Record<string, string> = {
    contact: 'Contacts',
    deal: 'Deals',
    account: 'Accounts',
    note: 'Notes',
    email: 'Emails',
  };
  const icons: Record<string, string> = {
    contact: 'Users',
    deal: 'Briefcase',
    account: 'Building2',
    note: 'FileText',
    email: 'Mail',
  };

  for (const type of order) {
    const items = results.filter((r) => r.type === type);
    if (items.length > 0) {
      groups.push({ type, label: labels[type] || type, icon: icons[type] || 'Search', items });
    }
  }

  return groups;
}