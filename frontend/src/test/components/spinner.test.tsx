import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Spinner } from '../../components/ui/spinner';

describe('Spinner', () => {
  it('renders basic spinner', () => {
    render(<Spinner />);
    const spinner = screen.getByRole('status');
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveAttribute('aria-label', 'Loading');
  });

  it('renders all sizes', () => {
    const sizes = ['xs', 'sm', 'md', 'lg'] as const;
    for (const size of sizes) {
      const { unmount } = render(<Spinner size={size} />);
      const spinner = screen.getByRole('status');
      expect(spinner).toBeInTheDocument();
      unmount();
    }
  });

  it('renders all variants', () => {
    const variants = ['brand', 'white', 'muted'] as const;
    for (const variant of variants) {
      const { unmount } = render(<Spinner variant={variant} />);
      const spinner = screen.getByRole('status');
      expect(spinner).toBeInTheDocument();
      unmount();
    }
  });

  it('uses custom label', () => {
    render(<Spinner label="Please wait" />);
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Please wait');
  });

  it('renders fullPage overlay', () => {
    render(<Spinner fullPage />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveAttribute('aria-busy', 'true');
    expect(screen.getByText('Loading')).toBeInTheDocument();
  });

  it('renders custom label in fullPage', () => {
    render(<Spinner fullPage label="Saving..." />);
    expect(screen.getByText('Saving...')).toBeInTheDocument();
  });

  it('renders spinner without fullPage', () => {
    const { container } = render(<Spinner />);
    expect(container.firstChild).toHaveClass('animate-spin');
  });

  it('passes additional className', () => {
    const { container } = render(<Spinner className="extra" />);
    expect(container.firstChild).toHaveClass('extra');
  });

  it('fullPage overlay has backdrop blur', () => {
    render(<Spinner fullPage />);
    const overlay = screen.getByRole('alert');
    expect(overlay).toHaveClass('backdrop-blur-sm');
  });

  it('defaults to md size', () => {
    const { container } = render(<Spinner />);
    expect(container.firstChild).toHaveClass('h-6', 'w-6');
  });

  it('defaults to brand variant', () => {
    const { container } = render(<Spinner />);
    expect(container.firstChild).toHaveClass(/text-brand-600/);
  });
});