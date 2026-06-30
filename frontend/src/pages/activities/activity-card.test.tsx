import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ActivityCard, ACTIVITY_ICONS, ACTIVITY_COLORS } from './activity-card';
import type { TimelineEntry } from '../../types';

// Mock the lucide-react icons (they're large and just SVG)
vi.mock('lucide-react', () => ({
  FileText: () => <span data-testid="icon-file-text">FT</span>,
  Phone: () => <span data-testid="icon-phone">P</span>,
  Mail: () => <span data-testid="icon-mail">M</span>,
  Calendar: () => <span data-testid="icon-calendar">C</span>,
  CheckSquare: () => <span data-testid="icon-check-square">CS</span>,
  TrendingUp: () => <span data-testid="icon-trending-up">TU</span>,
  Inbox: () => <span data-testid="icon-inbox">I</span>,
  ArrowUpRight: () => <span data-testid="icon-arrow-up-right">AUR</span>,
}));

// Mock date-fns
vi.mock('date-fns', () => ({
  formatDistanceToNow: vi.fn(() => '2 days ago'),
}));

const baseEntry: TimelineEntry = {
  id: 'a1',
  activity_type: 'note',
  title: 'Test note',
  description: 'Test description',
  created_at: '2026-06-28T12:00:00Z',
  actor: { id: 'u1', name: 'Alice', avatar_url: '' },
  entity: { type: 'contact', id: 'c1', name: 'Bob', url: '/contacts/c1' },
  metadata: {},
};

describe('ActivityCard', () => {
  it('renders activity title', () => {
    render(<ActivityCard activity={baseEntry} />);
    expect(screen.getByText('Test note')).toBeInTheDocument();
  });

  it('renders fallback title from activity_type when title is empty', () => {
    const entry = { ...baseEntry, title: '' };
    render(<ActivityCard activity={entry} />);
    expect(screen.getByText('note activity')).toBeInTheDocument();
  });

  it('renders description when present', () => {
    render(<ActivityCard activity={baseEntry} />);
    expect(screen.getByText('Test description')).toBeInTheDocument();
  });

  it('renders relative time using date-fns', () => {
    render(<ActivityCard activity={baseEntry} />);
    expect(screen.getByText('2 days ago')).toBeInTheDocument();
  });

  it('renders actor name and avatar fallback', () => {
    render(<ActivityCard activity={baseEntry} />);
    expect(screen.getByText('Alice')).toBeInTheDocument();
  });

  it('renders entity link with name', () => {
    render(<ActivityCard activity={baseEntry} />);
    expect(screen.getByText('Bob')).toBeInTheDocument();
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/contacts/c1');
  });

  it('does not render entity link when entity name is empty', () => {
    const entry = { ...baseEntry, entity: { ...baseEntry.entity, name: '' } };
    render(<ActivityCard activity={entry} />);
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });

  it('does not render entity link when entity name is undefined', () => {
    const entry = { ...baseEntry, entity: { type: 'contact', id: 'c1', name: '', url: '' } };
    render(<ActivityCard activity={entry} />);
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });

  it('shows icon matching activity_type', () => {
    const entry = { ...baseEntry, activity_type: 'call' as const };
    render(<ActivityCard activity={entry} />);
    expect(screen.getByTestId('icon-phone')).toBeInTheDocument();
  });

  it('shows email icon for email type', () => {
    const entry = { ...baseEntry, activity_type: 'email' as const };
    render(<ActivityCard activity={entry} />);
    expect(screen.getByTestId('icon-mail')).toBeInTheDocument();
  });

  it('shows default inbox icon for unknown type', () => {
    const entry = { ...baseEntry, activity_type: 'unknown_type' as any };
    render(<ActivityCard activity={entry} />);
    expect(screen.getByTestId('icon-inbox')).toBeInTheDocument();
  });

  it('does not render actor section when actor name is empty', () => {
    const entry = { ...baseEntry, actor: { id: '', name: '', avatar_url: '' } };
    render(<ActivityCard activity={entry} />);
    expect(screen.queryByText('Alice')).not.toBeInTheDocument();
  });

  it('renders description as whitespace-pre-wrap for multiline content', () => {
    const entry = { ...baseEntry, description: 'Line 1\nLine 2\nLine 3' };
    const { container } = render(<ActivityCard activity={entry} />);
    const descEl = container.querySelector('.line-clamp-2');
    expect(descEl).toBeInTheDocument();
    expect(descEl).toHaveClass('whitespace-pre-wrap');
  });

  it('handses metadata field gracefully', () => {
    const entry = { ...baseEntry, metadata: { duration: 30, call_outcome: 'completed' } };
    render(<ActivityCard activity={entry} />);
    // Card should still render the title even with rich metadata
    expect(screen.getByText('Test note')).toBeInTheDocument();
  });
});

describe('ACTIVITY_ICONS map', () => {
  it('has entries for all expected activity types', () => {
    const types = [
      'note', 'call', 'email', 'meeting', 'task',
      'deal', 'deal_stage_change', 'deal_status_change', 'file_upload', 'system',
    ];
    for (const t of types) {
      expect(ACTIVITY_ICONS).toHaveProperty(t);
    }
  });
});

describe('ACTIVITY_COLORS map', () => {
  it('has entries for all expected activity types', () => {
    const types = [
      'note', 'call', 'email', 'meeting', 'task',
      'deal', 'deal_stage_change', 'deal_status_change', 'file_upload',
    ];
    for (const t of types) {
      expect(ACTIVITY_COLORS).toHaveProperty(t);
    }
  });

  it('has color strings containing bg and text classes', () => {
    for (const [, color] of Object.entries(ACTIVITY_COLORS)) {
      expect(color).toContain('bg-');
      expect(color).toContain('text-');
    }
  });
});