import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Avatar } from '../../components/ui/avatar';

describe('Avatar', () => {
  it('renders fallback initials when no src', () => {
    render(<Avatar fallback="John Doe" />);
    expect(screen.getByText('JD')).toBeInTheDocument();
  });

  it('renders image when src is provided', () => {
    render(<Avatar src="https://example.com/avatar.jpg" alt="User Avatar" />);
    const img = screen.getByAltText('User Avatar');
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('src', 'https://example.com/avatar.jpg');
  });

  it('renders fallback when both src and fallback are provided', () => {
    render(<Avatar src="https://example.com/avatar.jpg" fallback="Jane Doe" />);
    expect(screen.getByText('JD')).toBeInTheDocument();
  });

  it('renders all sizes', () => {
    const sizes = ['xs', 'sm', 'md', 'lg', 'xl'] as const;
    for (const size of sizes) {
      const { unmount } = render(<Avatar fallback="User" size={size} />);
      expect(screen.getByText('U')).toBeInTheDocument();
      unmount();
    }
  });

  it('renders online indicator', () => {
    render(<Avatar online fallback="User" />);
    expect(screen.getByRole('status', { name: /online/i })).toBeInTheDocument();
  });

  it('does not render online indicator when not online', () => {
    render(<Avatar fallback="User" />);
    expect(screen.queryByRole('status', { name: /online/i })).not.toBeInTheDocument();
  });

  it('renders circle shape by default', () => {
    const { container } = render(<Avatar fallback="User" />);
    const fallbackSpan = screen.getByText('U');
    expect(fallbackSpan).toHaveClass('rounded-full');
  });

  it('renders square shape', () => {
    const { container } = render(<Avatar fallback="User" shape="square" />);
    const fallbackSpan = screen.getByText('U');
    expect(fallbackSpan).toHaveClass('rounded-lg');
  });

  it('fallback has role="img" when no src', () => {
    render(<Avatar fallback="User" alt="User Avatar" />);
    expect(screen.getByRole('img')).toHaveAttribute('aria-label', 'User Avatar');
  });

  it('fallback is aria-hidden when src is present', () => {
    render(<Avatar src="https://example.com/avatar.jpg" fallback="User" />);
    const fallbackSpan = screen.getByText('U');
    expect(fallbackSpan).toHaveAttribute('aria-hidden', 'true');
  });

  it('computes initials from single name', () => {
    render(<Avatar fallback="Alice" />);
    expect(screen.getByText('A')).toBeInTheDocument();
  });

  it('computes initials from three names (takes first two)', () => {
    render(<Avatar fallback="John Michael Doe" />);
    expect(screen.getByText('JM')).toBeInTheDocument();
  });

  it('renders without fallback or src', () => {
    const { container } = render(<Avatar />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('passes additional className', () => {
    const { container } = render(<Avatar fallback="User" className="extra" />);
    expect(container.firstChild).toHaveClass('extra');
  });

  it('img has correct classes for object fit', () => {
    render(<Avatar src="https://example.com/avatar.jpg" alt="A" />);
    const img = screen.getByAltText('A');
    expect(img).toHaveClass('object-cover');
  });
});