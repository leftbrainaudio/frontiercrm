import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MetricCardsRow } from './metric-cards-row';

describe('MetricCardsRow', () => {
  const sampleCards = [
    { title: 'Pipeline Value', value: '$100,000', change: '+12.5%', positive: true, icon: <span data-testid="icon-pv">$</span> },
    { title: 'Win Rate', value: '45%', change: null, positive: true, icon: <span data-testid="icon-wr">%</span> },
    { title: 'Active Deals', value: '23', change: '+3', positive: true, icon: <span data-testid="icon-ad">#</span> },
    { title: 'Avg Days', value: '32d', change: '-2d', positive: true, icon: <span data-testid="icon-ad2">!</span> },
  ];

  it('renders correct number of cards', () => {
    render(<MetricCardsRow cards={sampleCards} />);
    expect(screen.getByText('$100,000')).toBeInTheDocument();
    expect(screen.getByText('45%')).toBeInTheDocument();
    expect(screen.getByText('23')).toBeInTheDocument();
    expect(screen.getByText('32d')).toBeInTheDocument();
    expect(screen.getByText('Pipeline Value')).toBeInTheDocument();
    expect(screen.getByText('Win Rate')).toBeInTheDocument();
    expect(screen.getByText('Active Deals')).toBeInTheDocument();
    expect(screen.getByText('Avg Days')).toBeInTheDocument();
  });

  it('renders change indicators when present', () => {
    render(<MetricCardsRow cards={sampleCards} />);
    expect(screen.getByText('+12.5%')).toBeInTheDocument();
    expect(screen.getByText('+3')).toBeInTheDocument();
  });

  it('does not render change badges when change is null', () => {
    render(<MetricCardsRow cards={sampleCards} />);
    // Win Rate has change=null — we should see only 3 ▲ indicators (not 4)
    // for Pipeline Value (+12.5%), Active Deals (+3), Avg Days (-2d)
    expect(screen.queryAllByText('▲').length).toBe(3);
    expect(screen.queryByText('▼')).not.toBeInTheDocument();
  });

  it('returns null when empty array', () => {
    const { container } = render(<MetricCardsRow cards={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders icons for each card', () => {
    render(<MetricCardsRow cards={sampleCards} />);
    expect(screen.getByTestId('icon-pv')).toBeInTheDocument();
    expect(screen.getByTestId('icon-wr')).toBeInTheDocument();
    expect(screen.getByTestId('icon-ad')).toBeInTheDocument();
  });

  it('applies default columns=4', () => {
    const { container } = render(<MetricCardsRow cards={sampleCards} />);
    const gridDiv = container.firstChild as HTMLElement;
    expect(gridDiv.className).toContain('grid');
  });

  it('renders with columns=6 class pattern', () => {
    const { container } = render(<MetricCardsRow cards={sampleCards} columns={6} />);
    const gridDiv = container.firstChild as HTMLElement;
    expect(gridDiv.className).toContain('xl:grid-cols-6');
  });
});