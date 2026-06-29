import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Skeleton } from '../../components/ui/skeleton';

describe('Skeleton', () => {
  it('renders single skeleton element', () => {
    render(<Skeleton />);
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Loading');
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders text variant by default', () => {
    const { container } = render(<Skeleton />);
    expect(container.firstChild).toHaveClass('rounded');
  });

  it('renders circular variant', () => {
    const { container } = render(<Skeleton variant="circular" />);
    expect(container.firstChild).toHaveClass('rounded-full');
  });

  it('renders rectangular variant', () => {
    const { container } = render(<Skeleton variant="rectangular" />);
    expect(container.firstChild).toHaveClass('rounded-lg');
  });

  it('renders multiple lines when count > 1 for text variant', () => {
    const { container } = render(<Skeleton variant="text" count={3} />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.children.length).toBeGreaterThanOrEqual(3);
  });

  it('applies custom width', () => {
    const { container } = render(<Skeleton width="200px" />);
    expect(container.firstChild).toHaveStyle({ width: '200px' });
  });

  it('applies custom height', () => {
    const { container } = render(<Skeleton height="100px" />);
    expect(container.firstChild).toHaveStyle({ height: '100px' });
  });

  it('converts numeric width/height to px', () => {
    const { container } = render(<Skeleton width={50} height={50} />);
    expect(container.firstChild).toHaveStyle({ width: '50px', height: '50px' });
  });

  it('disables animation when noAnimation is true', () => {
    const { container } = render(<Skeleton noAnimation />);
    expect(container.firstChild).not.toHaveClass('animate-pulse');
  });

  it('has animation by default', () => {
    const { container } = render(<Skeleton />);
    expect(container.firstChild).toHaveClass('animate-pulse');
  });

  it('renders sr-only text', () => {
    render(<Skeleton />);
    const srText = screen.getByText('Loading...');
    expect(srText).toHaveClass('sr-only');
  });

  it('passes additional className', () => {
    const { container } = render(<Skeleton className="extra" />);
    expect(container.firstChild).toHaveClass('extra');
  });

  it('renders aria-label on multi-line text', () => {
    render(<Skeleton variant="text" count={3} />);
    const wrapper = screen.getByRole('status');
    expect(wrapper).toHaveAttribute('aria-label', 'Loading');
  });
});