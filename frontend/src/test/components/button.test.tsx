import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from '../../components/atoms/button';

describe('Button', () => {
  it('renders default button with children', () => {
    render(<Button>Click me</Button>);
    const btn = screen.getByRole('button', { name: /click me/i });
    expect(btn).toBeInTheDocument();
    expect(btn).not.toBeDisabled();
  });

  it('renders all variants', () => {
    const variants = ['primary', 'secondary', 'outline', 'ghost', 'danger'] as const;
    for (const variant of variants) {
      const { unmount } = render(<Button variant={variant}>{variant}</Button>);
      expect(screen.getByRole('button', { name: variant })).toBeInTheDocument();
      unmount();
    }
  });

  it('renders all sizes', () => {
    const sizes = ['sm', 'md', 'lg'] as const;
    for (const size of sizes) {
      const { unmount } = render(<Button size={size}>{size}</Button>);
      expect(screen.getByRole('button', { name: size })).toBeInTheDocument();
      unmount();
    }
  });

  it('shows loading spinner and disables when loading', () => {
    render(<Button loading>Loading</Button>);
    const btn = screen.getByRole('button', { name: /loading/i });
    expect(btn).toBeDisabled();
    expect(btn).toHaveAttribute('aria-busy', 'true');
  });

  it('disabled prop disables the button', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole('button', { name: /disabled/i })).toBeDisabled();
  });

  it('fullWidth adds w-full class', () => {
    const { container } = render(<Button fullWidth>Full</Button>);
    expect(container.firstChild).toHaveClass('w-full');
  });

  it('fires onClick when clicked', async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(<Button onClick={onClick}>Click</Button>);
    await user.click(screen.getByRole('button', { name: /click/i }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('does not fire onClick when disabled', async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(<Button onClick={onClick} disabled>Click</Button>);
    await user.click(screen.getByRole('button', { name: /click/i }));
    expect(onClick).not.toHaveBeenCalled();
  });

  it('renders icon when provided', () => {
    render(<Button icon={<span data-testid="icon">*</span>}>Icon</Button>);
    expect(screen.getByTestId('icon')).toBeInTheDocument();
  });

  it('renders as a button element', () => {
    render(<Button>Btn</Button>);
    expect(screen.getByRole('button').tagName).toBe('BUTTON');
  });

  it('passes type prop', () => {
    render(<Button type="submit">Submit</Button>);
    expect(screen.getByRole('button')).toHaveAttribute('type', 'submit');
  });

  it('accepts additional className', () => {
    const { container } = render(<Button className="extra-class">Styled</Button>);
    expect(container.firstChild).toHaveClass('extra-class');
  });

  it('renders with ref', () => {
    const ref = { current: null } as React.RefObject<HTMLButtonElement>;
    render(<Button ref={ref}>Ref</Button>);
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
  });

  it('renders and hides children properly', () => {
    render(<Button>Child</Button>);
    expect(screen.getByText('Child')).toBeInTheDocument();
  });
});