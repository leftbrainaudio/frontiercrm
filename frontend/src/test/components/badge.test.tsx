import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Badge } from '../../components/atoms/badge';

describe('Badge', () => {
  it('renders badge with children', () => {
    render(<Badge>New</Badge>);
    expect(screen.getByText('New')).toBeInTheDocument();
    expect(screen.getByText('New').tagName).toBe('SPAN');
  });

  it('renders all color variants', () => {
    const variants = ['default', 'success', 'warning', 'danger', 'info', 'neutral'] as const;
    for (const variant of variants) {
      const { unmount } = render(<Badge variant={variant}>{variant}</Badge>);
      expect(screen.getByText(variant)).toBeInTheDocument();
      unmount();
    }
  });

  it('renders all sizes', () => {
    const sizes = ['sm', 'md'] as const;
    for (const size of sizes) {
      const { unmount } = render(<Badge size={size}>{size}</Badge>);
      expect(screen.getByText(size)).toBeInTheDocument();
      unmount();
    }
  });

  it('renders as dot indicator when dot is true', () => {
    const { container } = render(<Badge dot variant="success" />);
    const dot = container.firstChild as HTMLElement;
    expect(dot).toBeInTheDocument();
    expect(dot).toHaveClass('rounded-full');
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('dot has correct aria-label', () => {
    render(<Badge dot variant="success" />);
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Indicator');
  });

  it('renders outline style when outline is true', () => {
    render(<Badge outline variant="danger">Outline</Badge>);
    const badge = screen.getByText('Outline');
    expect(badge).toHaveClass('bg-transparent', 'border');
  });

  it('renders remove button when onRemove is provided', () => {
    const onRemove = vi.fn();
    render(<Badge onRemove={onRemove}>Removable</Badge>);
    expect(screen.getByRole('button', { name: /remove/i })).toBeInTheDocument();
  });

  it('calls onRemove when remove button is clicked', async () => {
    const onRemove = vi.fn();
    const user = userEvent.setup();
    render(<Badge onRemove={onRemove}>Removable</Badge>);
    await user.click(screen.getByRole('button', { name: /remove/i }));
    expect(onRemove).toHaveBeenCalledTimes(1);
  });

  it('remove button stops propagation', async () => {
    const onRemove = vi.fn();
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(
      <span onClick={onClick}>
        <Badge onRemove={onRemove}>Badge</Badge>
      </span>,
    );
    await user.click(screen.getByRole('button', { name: /remove/i }));
    expect(onRemove).toHaveBeenCalledTimes(1);
    expect(onClick).not.toHaveBeenCalled();
  });

  it('does not render remove button when onRemove is not provided', () => {
    render(<Badge>No Remove</Badge>);
    expect(screen.queryByRole('button', { name: /remove/i })).not.toBeInTheDocument();
  });

  it('passes additional className', () => {
    render(<Badge className="extra">Styled</Badge>);
    expect(screen.getByText('Styled')).toHaveClass('extra');
  });

  it('renders with default variant when none specified', () => {
    render(<Badge>Default</Badge>);
    expect(screen.getByText('Default')).toBeInTheDocument();
  });
});