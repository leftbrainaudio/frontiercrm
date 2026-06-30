import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { TimelineCard, TimelineGroup, groupTimelineByDate } from './timeline-card';
import type { TimelineEntry } from '../../types';

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  FileText: () => <span data-testid="icon-file-text">FT</span>,
  Phone: () => <span data-testid="icon-phone">P</span>,
  Mail: () => <span data-testid="icon-mail">M</span>,
  Calendar: () => <span data-testid="icon-calendar">C</span>,
  CheckSquare: () => <span data-testid="icon-check-square">CS</span>,
  TrendingUp: () => <span data-testid="icon-trending-up">TU</span>,
  Inbox: () => <span data-testid="icon-inbox">I</span>,
  ArrowUpRight: () => <span data-testid="icon-arrow-up-right">AUR</span>,
  Upload: () => <span data-testid="icon-upload">U</span>,
  History: () => <span data-testid="icon-history">H</span>,
  ChevronDown: () => <span data-testid="icon-chevron-down">CD</span>,
}));

const baseEntry: TimelineEntry = {
  id: 'a1',
  activity_type: 'note',
  title: 'Test note',
  description: 'Description',
  created_at: '2026-06-30T12:00:00Z',
  actor: { id: 'u1', name: 'Alice', avatar_url: '' },
  entity: { type: 'contact', id: 'c1', name: 'Bob', url: '/contacts/c1' },
  metadata: {},
};

function renderWithRouter(el: React.ReactElement) {
  return render(<MemoryRouter>{el}</MemoryRouter>);
}

describe('TimelineCard', () => {
  it('renders entry title', () => {
    renderWithRouter(<TimelineCard entry={baseEntry} />);
    expect(screen.getByText('Test note')).toBeInTheDocument();
  });

  it('renders fallback title when title is empty', () => {
    const entry = { ...baseEntry, title: '' };
    renderWithRouter(<TimelineCard entry={entry} />);
    expect(screen.getByText('note activity')).toBeInTheDocument();
  });

  it('renders description when present', () => {
    renderWithRouter(<TimelineCard entry={baseEntry} />);
    expect(screen.getByText('Description')).toBeInTheDocument();
  });

  it('does not render description when absent', () => {
    const entry = { ...baseEntry, description: '' };
    renderWithRouter(<TimelineCard entry={entry} />);
    expect(screen.queryByText('Description')).not.toBeInTheDocument();
  });

  it('renders actor name', () => {
    renderWithRouter(<TimelineCard entry={baseEntry} />);
    expect(screen.getByText('Alice')).toBeInTheDocument();
  });

  it('renders "Unknown" when actor name is empty', () => {
    const entry = { ...baseEntry, actor: { id: '', name: '', avatar_url: '' } };
    renderWithRouter(<TimelineCard entry={entry} />);
    expect(screen.getByText('Unknown')).toBeInTheDocument();
  });

  it('renders entity name as a clickable button', () => {
    renderWithRouter(<TimelineCard entry={baseEntry} />);
    expect(screen.getByText('Bob')).toBeInTheDocument();
  });

  it('does not render entity button when entity name is empty', () => {
    const entry = { ...baseEntry, entity: { ...baseEntry.entity, name: '' } };
    renderWithRouter(<TimelineCard entry={entry} />);
    expect(screen.queryByText('Bob')).not.toBeInTheDocument();
  });

  it('shows "Just now" for very recent entries', () => {
    const now = new Date().toISOString();
    const entry = { ...baseEntry, created_at: now };
    renderWithRouter(<TimelineCard entry={entry} />);
    expect(screen.getByText('Just now')).toBeInTheDocument();
  });

  it('shows "Xm ago" for entries minutes old', () => {
    const date = new Date(Date.now() - 5 * 60000).toISOString();
    const entry = { ...baseEntry, created_at: date };
    renderWithRouter(<TimelineCard entry={entry} />);
    expect(screen.getByText('5m ago')).toBeInTheDocument();
  });

  it('shows "Xh ago" for entries hours old', () => {
    const date = new Date(Date.now() - 3 * 3600000).toISOString();
    const entry = { ...baseEntry, created_at: date };
    renderWithRouter(<TimelineCard entry={entry} />);
    expect(screen.getByText('3h ago')).toBeInTheDocument();
  });

  it('shows "Xd ago" for entries days old', () => {
    const date = new Date(Date.now() - 3 * 86400000).toISOString();
    const entry = { ...baseEntry, created_at: date };
    renderWithRouter(<TimelineCard entry={entry} />);
    expect(screen.getByText('3d ago')).toBeInTheDocument();
  });
});

describe('TimelineGroup', () => {
  it('renders date label', () => {
    renderWithRouter(
      <TimelineGroup dateKey="2026-06-30" entries={[baseEntry]} />,
    );
    expect(screen.getByText(/today/i)).toBeInTheDocument();
  });

  it('renders all entries in the group', () => {
    const entry2 = { ...baseEntry, id: 'a2', title: 'Second entry' };
    renderWithRouter(
      <TimelineGroup dateKey="2026-06-30" entries={[baseEntry, entry2]} />,
    );
    expect(screen.getByText('Test note')).toBeInTheDocument();
    expect(screen.getByText('Second entry')).toBeInTheDocument();
  });
});

describe('groupTimelineByDate', () => {
  it('groups entries by date key', () => {
    const entries: TimelineEntry[] = [
      { ...baseEntry, id: 'a1', created_at: '2026-06-30T12:00:00Z' },
      { ...baseEntry, id: 'a2', created_at: '2026-06-30T14:00:00Z' },
      { ...baseEntry, id: 'a3', created_at: '2026-06-29T10:00:00Z' },
    ];
    const groups = groupTimelineByDate(entries);
    expect(groups.size).toBe(2);
    expect(groups.get('2026-06-30')).toHaveLength(2);
    expect(groups.get('2026-06-29')).toHaveLength(1);
  });

  it('returns empty map for empty array', () => {
    const groups = groupTimelineByDate([]);
    expect(groups.size).toBe(0);
  });

  it('handles single entry', () => {
    const groups = groupTimelineByDate([baseEntry]);
    expect(groups.size).toBe(1);
    expect(groups.get('2026-06-30')?.[0].id).toBe('a1');
  });
});