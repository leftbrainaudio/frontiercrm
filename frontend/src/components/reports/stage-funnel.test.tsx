import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StageFunnel } from './stage-funnel';

describe('StageFunnel', () => {
  const sampleData = [
    { from_stage: 'Lead', to_stage: 'Qualified', conversion_rate: 0.6, deals_entered: 50, deals_converted: 30 },
    { from_stage: 'Qualified', to_stage: 'Proposal', conversion_rate: 0.5, deals_entered: 30, deals_converted: 15 },
  ];

  it('renders loading skeleton', () => {
    const { container } = render(<StageFunnel data={[]} loading={true} />);
    expect(screen.getByText('Stage Conversion Funnel')).toBeInTheDocument();
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders empty state when no data', () => {
    render(<StageFunnel data={[]} />);
    expect(screen.getByText('No conversion data available')).toBeInTheDocument();
  });

  it('renders stage names', () => {
    render(<StageFunnel data={sampleData} />);
    expect(screen.getByText('Lead')).toBeInTheDocument();
    expect(screen.getByText('Qualified')).toBeInTheDocument();
  });

  it('renders conversion rates as percentages', () => {
    render(<StageFunnel data={sampleData} />);
    expect(screen.getByText('60%')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('renders deals_entered counts', () => {
    render(<StageFunnel data={sampleData} />);
    expect(screen.getByText('50 deals')).toBeInTheDocument();
    expect(screen.getByText('30 deals')).toBeInTheDocument();
  });

  it('renders last stage to_stage name and deals_converted', () => {
    render(<StageFunnel data={sampleData} />);
    expect(screen.getByText('Proposal')).toBeInTheDocument();
    expect(screen.getByText('15 deals')).toBeInTheDocument();
  });

  it('renders down arrows between stages', () => {
    const { container } = render(<StageFunnel data={sampleData} />);
    // The down arrow ↓ renders as text
    expect(container.textContent).toContain('↓');
  });
});