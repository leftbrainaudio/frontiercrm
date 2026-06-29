import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Input } from '../../components/ui/input';

describe('Input', () => {
  it('renders basic input', () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
  });

  it('renders with label', () => {
    render(<Input label="Email" />);
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
  });

  it('renders all sizes', () => {
    const sizes = ['sm', 'md'] as const;
    for (const size of sizes) {
      const { unmount } = render(<Input label={`Size ${size}`} size={size} />);
      expect(screen.getByLabelText(`Size ${size}`)).toBeInTheDocument();
      unmount();
    }
  });

  it('renders all variants', () => {
    const variants = ['outline', 'filled'] as const;
    for (const variant of variants) {
      const { unmount } = render(<Input label={`Variant ${variant}`} variant={variant} />);
      expect(screen.getByLabelText(`Variant ${variant}`)).toBeInTheDocument();
      unmount();
    }
  });

  it('shows error message', () => {
    render(<Input label="Name" error="This field is required" />);
    expect(screen.getByRole('alert')).toHaveTextContent('This field is required');
    expect(screen.getByLabelText('Name')).toHaveAttribute('aria-invalid', 'true');
  });

  it('shows helper text', () => {
    render(<Input label="Name" helperText="Enter your full name" />);
    expect(screen.getByText('Enter your full name')).toBeInTheDocument();
  });

  it('does not show helper text when error is present', () => {
    render(<Input label="Name" error="Error!" helperText="Helper" />);
    expect(screen.getByRole('alert')).toHaveTextContent('Error!');
    expect(screen.queryByText('Helper')).not.toBeInTheDocument();
  });

  it('renders iconLeft', () => {
    render(<Input label="Search" iconLeft={<span data-testid="left-icon">🔍</span>} />);
    expect(screen.getByTestId('left-icon')).toBeInTheDocument();
  });

  it('renders iconRight', () => {
    render(<Input label="Password" iconRight={<span data-testid="right-icon">👁</span>} />);
    expect(screen.getByTestId('right-icon')).toBeInTheDocument();
  });

  it('disables the input', () => {
    render(<Input label="Disabled" disabled />);
    expect(screen.getByLabelText('Disabled')).toBeDisabled();
  });

  it('sets readOnly on input', () => {
    render(<Input label="Read Only" readOnly />);
    expect(screen.getByLabelText('Read Only')).toHaveAttribute('readOnly');
  });

  it('fires onChange when typing', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<Input label="Test" onChange={onChange} />);
    await user.type(screen.getByLabelText('Test'), 'a');
    expect(onChange).toHaveBeenCalled();
  });

  it('generates id from label', () => {
    render(<Input label="My Field" />);
    expect(screen.getByLabelText('My Field')).toHaveAttribute('id', 'my-field');
  });

  it('renders with ref', () => {
    const ref = { current: null } as React.RefObject<HTMLInputElement>;
    render(<Input ref={ref} label="Ref" />);
    expect(ref.current).toBeInstanceOf(HTMLInputElement);
  });

  it('accepts custom id', () => {
    render(<Input label="Label" id="custom-id" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('id', 'custom-id');
  });

  it('has correct aria-describedby for error', () => {
    render(<Input label="Email" error="Invalid email" />);
    const input = screen.getByLabelText('Email');
    const errorId = input.getAttribute('aria-describedby');
    expect(errorId).toMatch(/-error$/);
  });

  it('has correct aria-describedby for helper', () => {
    render(<Input label="Email" helperText="Enter your email" />);
    const input = screen.getByLabelText('Email');
    const helperId = input.getAttribute('aria-describedby');
    expect(helperId).toMatch(/-helper$/);
  });
});