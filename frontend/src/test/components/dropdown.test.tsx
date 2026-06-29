import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Dropdown } from '../../components/ui/dropdown';

describe('Dropdown', () => {
  const defaultItems = [
    { label: 'Edit', onClick: vi.fn() },
    { label: 'Delete', onClick: vi.fn(), danger: true },
    { label: 'Separator', divider: true } as const,
    { label: 'Export', onClick: vi.fn(), disabled: true },
  ];

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders trigger element', () => {
    render(
      <Dropdown trigger={<button>Open</button>} items={[defaultItems[0]]} />,
    );
    expect(screen.getByRole('button', { name: /open/i })).toBeInTheDocument();
  });

  it('opens menu when trigger is clicked', async () => {
    const user = userEvent.setup();
    render(
      <Dropdown trigger={<button>Open</button>} items={[defaultItems[0]]} />,
    );
    await user.click(screen.getByRole('button', { name: /open/i }));
    expect(screen.getByRole('menu')).toBeInTheDocument();
    expect(screen.getByText('Edit')).toBeInTheDocument();
  });

  it('calls item onClick when menu item is clicked', async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(
      <Dropdown trigger={<button>Open</button>} items={[{ label: 'Edit', onClick }]} />,
    );
    await user.click(screen.getByRole('button', { name: /open/i }));
    await user.click(screen.getByText('Edit'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('closes menu after item click', async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(
      <Dropdown trigger={<button>Open</button>} items={[{ label: 'Edit', onClick }]} />,
    );
    await user.click(screen.getByRole('button', { name: /open/i }));
    await user.click(screen.getByText('Edit'));
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });

  it('renders disabled menu items', async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(
      <Dropdown
        trigger={<button>Open</button>}
        items={[{ label: 'Disabled Item', disabled: true, onClick }]}
      />,
    );
    await user.click(screen.getByRole('button', { name: /open/i }));
    const menuItem = screen.getByText('Disabled Item');
    expect(menuItem.closest('button')).toBeDisabled();
  });

  it('renders danger menu items', async () => {
    const user = userEvent.setup();
    render(
      <Dropdown trigger={<button>Open</button>} items={[{ label: 'Delete', danger: true, onClick: vi.fn() }]} />,
    );
    await user.click(screen.getByRole('button', { name: /open/i }));
    const menuItem = screen.getByText('Delete');
    expect(menuItem.closest('button')).toHaveClass(/text-red-600/);
  });

  it('renders divider', async () => {
    const user = userEvent.setup();
    render(
      <Dropdown
        trigger={<button>Open</button>}
        items={[
          { label: 'Edit', onClick: vi.fn() },
          { divider: true } as const,
          { label: 'Delete', onClick: vi.fn() },
        ]}
      />,
    );
    await user.click(screen.getByRole('button', { name: /open/i }));
    expect(screen.getByRole('separator')).toBeInTheDocument();
  });

  it('renders align end', async () => {
    const user = userEvent.setup();
    render(
      <Dropdown trigger={<button>Open</button>} items={[defaultItems[0]]} align="end" />,
    );
    await user.click(screen.getByRole('button', { name: /open/i }));
    const menu = screen.getByRole('menu');
    expect(menu).toHaveClass('right-0');
  });

  it('supports controlled open state', () => {
    const { rerender } = render(
      <Dropdown trigger={<button>Open</button>} items={[defaultItems[0]]} open={false} />,
    );
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    rerender(
      <Dropdown trigger={<button>Open</button>} items={[defaultItems[0]]} open={true} />,
    );
    expect(screen.getByRole('menu')).toBeInTheDocument();
  });

  it('calls onOpenChange when controlled', async () => {
    const onOpenChange = vi.fn();
    const user = userEvent.setup();
    render(
      <Dropdown
        trigger={<button>Open</button>}
        items={[defaultItems[0]]}
        onOpenChange={onOpenChange}
      />,
    );
    await user.click(screen.getByRole('button', { name: /open/i }));
    expect(onOpenChange).toHaveBeenCalledWith(true);
  });

  it('sets aria attributes on trigger', async () => {
    const user = userEvent.setup();
    render(
      <Dropdown trigger={<button>Open</button>} items={[defaultItems[0]]} />,
    );
    const trigger = screen.getByRole('button', { name: /open/i });
    expect(trigger).toHaveAttribute('aria-haspopup', 'menu');
    expect(trigger).toHaveAttribute('aria-expanded', 'false');
    await user.click(trigger);
    expect(trigger).toHaveAttribute('aria-expanded', 'true');
  });

  it('renders submenu', async () => {
    const user = userEvent.setup();
    render(
      <Dropdown
        trigger={<button>Open</button>}
        items={[
          {
            label: 'More',
            submenu: [
              { label: 'Option 1', onClick: vi.fn() },
              { label: 'Option 2', onClick: vi.fn() },
            ],
          },
        ]}
      />,
    );
    await user.click(screen.getByRole('button', { name: /open/i }));
    expect(screen.getByText('More')).toBeInTheDocument();
  });

  it('renders items with icons', async () => {
    const user = userEvent.setup();
    render(
      <Dropdown
        trigger={<button>Open</button>}
        items={[{ label: 'Save', icon: <span data-testid="save-icon">💾</span>, onClick: vi.fn() }]}
      />,
    );
    await user.click(screen.getByRole('button', { name: /open/i }));
    expect(screen.getByTestId('save-icon')).toBeInTheDocument();
  });

  it('renders items with chevron icon', async () => {
    const user = userEvent.setup();
    render(
      <Dropdown
        trigger={<button>Open</button>}
        items={[
          {
            label: 'More',
            submenu: [{ label: 'Option', onClick: vi.fn() }],
          },
        ]}
      />,
    );
    await user.click(screen.getByRole('button', { name: /open/i }));
    const menuItem = screen.getByText('More');
    const chevron = menuItem.nextElementSibling;
    expect(chevron).toBeInTheDocument();
  });

  it('accepts additional className', () => {
    const { container } = render(
      <Dropdown trigger={<button>Open</button>} items={[defaultItems[0]]} className="extra" />,
    );
    expect(container.firstChild).toHaveClass('extra');
  });
});