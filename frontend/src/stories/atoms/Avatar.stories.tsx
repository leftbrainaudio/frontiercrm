import type { Meta, StoryObj } from '@storybook/react';
import { Avatar } from '../../components/atoms/avatar';

const meta: Meta<typeof Avatar> = {
  title: 'Atoms/Avatar',
  component: Avatar,
  tags: ['autodocs'],
  argTypes: {
    size: { control: 'select', options: ['xs', 'sm', 'md', 'lg', 'xl'] },
    shape: { control: 'select', options: ['circle', 'square'] },
    online: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof Avatar>;

export const Default: Story = {
  args: {
    fallback: 'John Doe',
  },
};

export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <Avatar size="xs" fallback="JD" />
      <Avatar size="sm" fallback="JD" />
      <Avatar size="md" fallback="JD" />
      <Avatar size="lg" fallback="JD" />
      <Avatar size="xl" fallback="JD" />
    </div>
  ),
};

export const WithImage: Story = {
  args: {
    src: 'https://i.pravatar.cc/150?u=john',
    alt: 'John Doe',
    fallback: 'JD',
  },
};

export const OnlineIndicator: Story = {
  render: () => (
    <div className="flex items-center gap-4">
      <Avatar fallback="Alice" online />
      <Avatar fallback="Bob" size="lg" online />
      <Avatar src="https://i.pravatar.cc/150?u=carol" alt="Carol" fallback="CL" online />
    </div>
  ),
};

export const SquareShape: Story = {
  args: {
    shape: 'square',
    fallback: 'Team',
  },
};