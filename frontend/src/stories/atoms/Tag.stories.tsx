import type { Meta, StoryObj } from '@storybook/react';
import { Tag } from '../../components/atoms/tag';

const meta: Meta<typeof Tag> = {
  title: 'Atoms/Tag',
  component: Tag,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'success', 'warning', 'danger', 'info', 'neutral'],
    },
    size: { control: 'select', options: ['sm', 'md', 'lg'] },
  },
};

export default meta;
type Story = StoryObj<typeof Tag>;

export const Default: Story = {
  args: {
    children: 'Tag',
    variant: 'default',
  },
};

export const Variants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Tag variant="default">Default</Tag>
      <Tag variant="success">Success</Tag>
      <Tag variant="warning">Warning</Tag>
      <Tag variant="danger">Danger</Tag>
      <Tag variant="info">Info</Tag>
      <Tag variant="neutral">Neutral</Tag>
    </div>
  ),
};

export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <Tag size="sm">Small</Tag>
      <Tag size="md">Medium</Tag>
      <Tag size="lg">Large</Tag>
    </div>
  ),
};

export const Removable: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Tag variant="default" onRemove={() => alert('Removed!')}>Default</Tag>
      <Tag variant="success" onRemove={() => alert('Removed!')}>Success</Tag>
      <Tag variant="danger" onRemove={() => alert('Removed!')}>Danger</Tag>
      <Tag variant="info" onRemove={() => alert('Removed!')}>Info</Tag>
    </div>
  ),
};

export const InlineTags: Story = {
  render: () => (
    <div className="flex flex-wrap gap-1.5 max-w-md">
      <Tag variant="info">React</Tag>
      <Tag variant="success">TypeScript</Tag>
      <Tag variant="warning">WIP</Tag>
      <Tag variant="neutral">Documentation</Tag>
      <Tag variant="danger">Bug</Tag>
      <Tag variant="default">Feature</Tag>
    </div>
  ),
};