import type { Meta, StoryObj } from '@storybook/react';
import { IconButton } from '../../components/atoms/icon-button';
import { Mail, Trash2, Settings, Bell, Sun, Edit } from 'lucide-react';

const meta: Meta<typeof IconButton> = {
  title: 'Atoms/IconButton',
  component: IconButton,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'outline', 'ghost', 'danger'],
    },
    size: { control: 'select', options: ['xs', 'sm', 'md', 'lg'] },
    loading: { control: 'boolean' },
    disabled: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof IconButton>;

export const Default: Story = {
  args: {
    icon: <Mail className="h-5 w-5" />,
    label: 'Send email',
    variant: 'ghost',
  },
};

export const Variants: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <IconButton icon={<Mail className="h-5 w-5" />} label="Primary" variant="primary" />
      <IconButton icon={<Mail className="h-5 w-5" />} label="Secondary" variant="secondary" />
      <IconButton icon={<Mail className="h-5 w-5" />} label="Outline" variant="outline" />
      <IconButton icon={<Mail className="h-5 w-5" />} label="Ghost" variant="ghost" />
      <IconButton icon={<Trash2 className="h-5 w-5" />} label="Danger" variant="danger" />
    </div>
  ),
};

export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <IconButton icon={<Settings className="h-4 w-4" />} label="XS" size="xs" />
      <IconButton icon={<Settings className="h-4 w-4" />} label="SM" size="sm" />
      <IconButton icon={<Settings className="h-5 w-5" />} label="MD" size="md" />
      <IconButton icon={<Settings className="h-6 w-6" />} label="LG" size="lg" />
    </div>
  ),
};

export const Loading: Story = {
  render: () => (
    <IconButton icon={<Mail className="h-5 w-5" />} label="Sending" loading variant="primary" />
  ),
};

export const Disabled: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <IconButton icon={<Bell className="h-5 w-5" />} label="Notifications" disabled />
      <IconButton icon={<Edit className="h-5 w-5" />} label="Edit" disabled variant="primary" />
      <IconButton icon={<Trash2 className="h-5 w-5" />} label="Delete" disabled variant="danger" />
    </div>
  ),
};

export const CommonActions: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <IconButton icon={<Sun className="h-5 w-5" />} label="Toggle theme" />
      <IconButton icon={<Bell className="h-5 w-5" />} label="Notifications" variant="secondary" />
      <IconButton icon={<Settings className="h-5 w-5" />} label="Settings" variant="secondary" />
      <IconButton icon={<Edit className="h-5 w-5" />} label="Edit" variant="primary" />
      <IconButton icon={<Trash2 className="h-5 w-5" />} label="Delete" variant="danger" />
    </div>
  ),
};