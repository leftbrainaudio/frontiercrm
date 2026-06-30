import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Card } from '../../components/molecules/card';

describe('Card', () => {
  it('renders with children', () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('renders all variants', () => {
    const variants = ['default', 'elevated', 'outline', 'interactive'] as const;
    for (const variant of variants) {
      const { unmount } = render(<Card variant={variant}>Variant</Card>);
      expect(screen.getByText('Variant')).toBeInTheDocument();
      unmount();
    }
  });

  it('renders all padding sizes', () => {
    const paddings = ['none', 'sm', 'md', 'lg'] as const;
    for (const padding of paddings) {
      const { unmount } = render(<Card padding={padding}>Pad</Card>);
      expect(screen.getByText('Pad')).toBeInTheDocument();
      unmount();
    }
  });

  it('renders title and subtitle', () => {
    render(<Card title="Card Title" subtitle="Card Subtitle"><p>Body</p></Card>);
    expect(screen.getByText('Card Title')).toBeInTheDocument();
    expect(screen.getByText('Card Subtitle')).toBeInTheDocument();
  });

  it('renders header slot', () => {
    render(<Card header={<div data-testid="header">Custom Header</div>}>Body</Card>);
    expect(screen.getByTestId('header')).toBeInTheDocument();
  });

  it('renders footer slot', () => {
    render(<Card footer={<div data-testid="footer">Custom Footer</div>}>Body</Card>);
    expect(screen.getByTestId('footer')).toBeInTheDocument();
  });

  it('does not render header/footer when not provided', () => {
    const { container } = render(<Card>Body only</Card>);
    expect(container.querySelector('.border-b')).toBeNull();
    expect(container.querySelector('.border-t')).toBeNull();
  });

  it('renders title as h3', () => {
    render(<Card title="My Title">Body</Card>);
    const heading = screen.getByRole('heading', { name: /my title/i });
    expect(heading.tagName).toBe('H3');
  });

  it('accepts additional className', () => {
    const { container } = render(<Card className="my-card">Body</Card>);
    expect(container.firstChild).toHaveClass('my-card');
  });

  it('passes additional HTML attributes', () => {
    const { container } = render(<Card data-testid="card-test">Body</Card>);
    expect(container.firstChild).toHaveAttribute('data-testid', 'card-test');
  });

  it('renders as a div', () => {
    const { container } = render(<Card>Body</Card>);
    expect(container.firstChild?.nodeName).toBe('DIV');
  });
});