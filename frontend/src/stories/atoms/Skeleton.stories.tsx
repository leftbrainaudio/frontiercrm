import type { Meta, StoryObj } from '@storybook/react';
import { Skeleton } from '../../components/atoms/skeleton';

const meta: Meta<typeof Skeleton> = {
  title: 'Atoms/Skeleton',
  component: Skeleton,
  tags: ['autodocs'],
  argTypes: {
    variant: { control: 'select', options: ['text', 'circular', 'rectangular'] },
    count: { control: { type: 'number', min: 1, max: 8 } },
    noAnimation: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof Skeleton>;

export const Default: Story = {
  args: {
    width: 200,
  },
};

export const Variants: Story = {
  render: () => (
    <div className="flex flex-col gap-4">
      <div>
        <p className="mb-1 text-xs text-gray-500">Text</p>
        <Skeleton variant="text" width={200} />
      </div>
      <div>
        <p className="mb-1 text-xs text-gray-500">Circular</p>
        <Skeleton variant="circular" width={40} height={40} />
      </div>
      <div>
        <p className="mb-1 text-xs text-gray-500">Rectangular</p>
        <Skeleton variant="rectangular" width={200} height={100} />
      </div>
    </div>
  ),
};

export const TextLines: Story = {
  args: {
    variant: 'text',
    width: 300,
    count: 4,
  },
};

export const CardSkeleton: Story = {
  render: () => (
    <div className="w-72 rounded-lg border border-gray-200 p-4 space-y-3">
      <div className="flex items-center gap-3">
        <Skeleton variant="circular" width={40} height={40} />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="text" width="40%" />
        </div>
      </div>
      <Skeleton variant="rectangular" width="100%" height={80} />
      <Skeleton variant="text" width="80%" />
    </div>
  ),
};

export const NoAnimation: Story = {
  args: {
    width: 200,
    noAnimation: true,
  },
};