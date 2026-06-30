import type { Meta, StoryObj } from '@storybook/react';
import { Modal } from '../../components/molecules/modal';
import type { ModalProps } from '../../components/molecules/modal';
import { Button } from '../../components/atoms/button';
import { useState } from 'react';

const meta: Meta<typeof Modal> = {
  title: 'Atoms/Modal',
  component: Modal,
  tags: ['autodocs'],
  argTypes: {
    size: { control: 'select', options: ['sm', 'md', 'lg', 'xl', 'full'] },
    closeOnBackdrop: { control: 'boolean' },
    closeOnEscape: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof Modal>;

function ModalWrapper(props: Partial<ModalProps>) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Button onClick={() => setOpen(true)}>Open Modal</Button>
      <Modal open={open} onClose={() => setOpen(false)} {...props} />
    </>
  );
}

export const Default: Story = {
  render: () => (
    <ModalWrapper
      title="Modal Title"
      description="This is a description for the modal dialog."
    >
      <p className="text-sm text-gray-600 dark:text-gray-400">
        Modal content goes here. You can put any React components inside.
      </p>
    </ModalWrapper>
  ),
};

export const WithFooter: Story = {
  render: () => {
    const [open, setOpen] = useState(false);
    return (
      <>
        <Button onClick={() => setOpen(true)}>Open with Footer</Button>
        <Modal
          open={open}
          onClose={() => setOpen(false)}
          title="Confirm Action"
          description="Are you sure you want to proceed?"
          footer={
            <>
              <Button variant="ghost" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button onClick={() => { setOpen(false); alert('Confirmed!'); }}>
                Confirm
              </Button>
            </>
          }
        >
          <p className="text-sm text-gray-600 dark:text-gray-400">
            This action cannot be undone.
          </p>
        </Modal>
      </>
    );
  },
};

export const Sizes: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      {(['sm', 'md', 'lg', 'xl', 'full'] as const).map((size) => (
        <ModalWrapper key={size} size={size} title={`Size: ${size}`}>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            This modal uses the {size} size.
          </p>
        </ModalWrapper>
      ))}
    </div>
  ),
};

export const NoDescription: Story = {
  render: () => (
    <ModalWrapper title="Simple Modal">
      <p className="text-sm text-gray-600 dark:text-gray-400">
        This modal has no description, just a title.
      </p>
    </ModalWrapper>
  ),
};