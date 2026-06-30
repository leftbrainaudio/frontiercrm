import { describe, it, expect, vi } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Modal } from '../../components/molecules/modal';

describe('Modal', () => {
  const onClose = vi.fn();

  afterEach(() => {
    cleanup();
    onClose.mockClear();
  });

  it('returns null when not open', () => {
    const { container } = render(
      <Modal open={false} onClose={onClose}>
        Content
      </Modal>,
    );
    expect(container.innerHTML).toBe('');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders when open', () => {
    render(
      <Modal open={true} onClose={onClose}>
        Content
      </Modal>,
    );
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('renders title and description', () => {
    render(
      <Modal open={true} onClose={onClose} title="My Title" description="My Description">
        Content
      </Modal>,
    );
    expect(screen.getByText('My Title')).toBeInTheDocument();
    expect(screen.getByText('My Description')).toBeInTheDocument();
  });

  it('renders children', () => {
    render(
      <Modal open={true} onClose={onClose}>
        <p data-testid="child">Child content</p>
      </Modal>,
    );
    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('renders footer', () => {
    render(
      <Modal open={true} onClose={onClose} footer={<button>Save</button>}>
        Content
      </Modal>,
    );
    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
  });

  it('renders close button when title or description is present', () => {
    render(
      <Modal open={true} onClose={onClose} title="Title">
        Content
      </Modal>,
    );
    expect(screen.getByRole('button', { name: /close dialog/i })).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <Modal open={true} onClose={onClose} title="Title">
        Content
      </Modal>,
    );
    await user.click(screen.getByRole('button', { name: /close dialog/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when backdrop is clicked', async () => {
    const user = userEvent.setup();
    render(
      <Modal open={true} onClose={onClose} closeOnBackdrop={true} title="Title">
        Content
      </Modal>,
    );
    const dialog = screen.getByRole('dialog');
    const backdrop = dialog.firstChild as HTMLElement;
    await user.click(backdrop);
    expect(onClose).toHaveBeenCalled();
  });

  it('does not call onClose when backdrop click is disabled', async () => {
    const user = userEvent.setup();
    render(
      <Modal open={true} onClose={onClose} closeOnBackdrop={false} title="Title">
        Content
      </Modal>,
    );
    const dialog = screen.getByRole('dialog');
    const backdrop = dialog.firstChild as HTMLElement;
    await user.click(backdrop);
    expect(onClose).not.toHaveBeenCalled();
  });

  it('sets aria-modal on dialog', () => {
    render(
      <Modal open={true} onClose={onClose}>
        Content
      </Modal>,
    );
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
  });

  it('sets aria-labelledby when title is present', () => {
    render(
      <Modal open={true} onClose={onClose} title="Accessible Title">
        Content
      </Modal>,
    );
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-labelledby', 'modal-title');
  });

  it('sets aria-describedby when description is present', () => {
    render(
      <Modal open={true} onClose={onClose} description="Accessible Desc">
        Content
      </Modal>,
    );
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-describedby', 'modal-desc');
  });

  it('renders all sizes', () => {
    const sizes = ['sm', 'md', 'lg', 'xl', 'full'] as const;
    for (const size of sizes) {
      const { unmount } = render(
        <Modal open={true} onClose={onClose} size={size}>
          {size}
        </Modal>,
      );
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      unmount();
    }
  });

  it('locks body scroll when open', () => {
    render(
      <Modal open={true} onClose={onClose}>
        Content
      </Modal>,
    );
    expect(document.body.style.overflow).toBe('hidden');
  });

  it('restores body scroll when closed', () => {
    const { rerender } = render(
      <Modal open={true} onClose={onClose}>
        Content
      </Modal>,
    );
    rerender(
      <Modal open={false} onClose={onClose}>
        Content
      </Modal>,
    );
    expect(document.body.style.overflow).toBeFalsy();
  });
});