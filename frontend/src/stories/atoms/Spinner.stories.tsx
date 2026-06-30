import type { Meta, StoryObj } from '@storybook/react';
import { Spinner } from '../../components/ui/spinner';

const meta: Meta<typeof Spinner> = {
  title: 'Atoms/Spinner',
  component: Spinner,
  tags: ['autodocs'],
  argTypes: {
    size: { control: 'select', options: ['xs', 'sm', 'md', 'lg'] },
    variant: { control: 'select', options: ['brand', 'white', 'muted'] },
    fullPage: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof Spinner>;

export const Default: Story = {
  args: {},
};

export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-3">
      <Spinner size="xs" />
      <Spinner size="sm" />
      <Spinner size="md" />
      <Spinner size="lg" />
    </div>
  ),
};

export const Variants: Story = {
  render: () => (
    <div className="flex items-center gap-4">
      <Spinner variant="brand" />
      <Spinner variant="muted" />
      <div className="bg-gray-900 p-4 rounded-lg">
        <Spinner variant="white" />
      </div>
    </div>
  ),
};

export const WithLabel: Story = {
  args: {
    label: 'Loading data...',
  },
};