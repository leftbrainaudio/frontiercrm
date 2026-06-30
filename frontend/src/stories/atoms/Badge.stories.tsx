import type { Meta, StoryObj } from '@storybook/react';
import { Badge } from '../../components/atoms/badge';

const meta: Meta<typeof Badge> = {
  title: 'Atoms/Badge',
  component: Badge,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'success', 'warning', 'danger', 'info', 'neutral'],
    },
    size: { control: 'select', options: ['sm', 'md'] },
    dot: { control: 'boolean' },
    outline: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof Badge>;

export const Default: Story = {
  args: {
    children: 'Badge',
    variant: 'default',
  },
};

export const Variants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Badge variant="default">Default</Badge>
      <Badge variant="success">Success</Badge>
      <Badge variant="warning">Warning</Badge>
      <Badge variant="danger">Danger</Badge>
      <Badge variant="info">Info</Badge>
      <Badge variant="neutral">Neutral</Badge>
    </div>
  ),
};

export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <Badge size="sm">Small</Badge>
      <Badge size="md">Medium</Badge>
    </div>
  ),
};

export const Outline: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Badge variant="default" outline>Default</Badge>
      <Badge variant="success" outline>Success</Badge>
      <Badge variant="danger" outline>Danger</Badge>
      <Badge variant="neutral" outline>Neutral</Badge>
    </div>
  ),
};

export const Dot: Story = {
  render: () => (
    <div className="flex items-center gap-3">
      <Badge variant="success" dot />
      <Badge variant="warning" dot />
      <Badge variant="danger" dot />
      <Badge variant="neutral" dot />
      <Badge variant="default" dot />
    </div>
  ),
};

export const Removable: Story = {
  args: {
    children: 'Tag',
    onRemove: () => alert('Removed!'),
  },
};