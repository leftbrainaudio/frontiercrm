import type { Meta, StoryObj } from '@storybook/react';
import { Input } from '../../components/atoms/input';
import { Search, Mail } from 'lucide-react';

const meta: Meta<typeof Input> = {
  title: 'Atoms/Input',
  component: Input,
  tags: ['autodocs'],
  argTypes: {
    size: { control: 'select', options: ['sm', 'md'] },
    variant: { control: 'select', options: ['outline', 'filled'] },
    disabled: { control: 'boolean' },
    readOnly: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof Input>;

export const Default: Story = {
  args: {
    placeholder: 'Enter text...',
  },
};

export const WithLabel: Story = {
  args: {
    label: 'Email',
    placeholder: 'you@example.com',
    type: 'email',
  },
};

export const WithError: Story = {
  args: {
    label: 'Password',
    type: 'password',
    error: 'Password must be at least 8 characters',
  },
};

export const WithHelperText: Story = {
  args: {
    label: 'Username',
    placeholder: 'johndoe',
    helperText: 'This will be your display name',
  },
};

export const Sizes: Story = {
  render: () => (
    <div className="flex flex-col gap-3 max-w-sm">
      <Input size="sm" placeholder="Small input" />
      <Input size="md" placeholder="Medium input (default)" />
    </div>
  ),
};

export const Variants: Story = {
  render: () => (
    <div className="flex flex-col gap-3 max-w-sm">
      <Input variant="outline" placeholder="Outline variant (default)" />
      <Input variant="filled" placeholder="Filled variant" />
    </div>
  ),
};

export const WithIcons: Story = {
  render: () => (
    <div className="flex flex-col gap-3 max-w-sm">
      <Input iconLeft={<Search className="h-4 w-4" />} placeholder="Search..." />
      <Input iconRight={<Mail className="h-4 w-4" />} placeholder="Email" />
      <Input iconLeft={<Search className="h-4 w-4" />} iconRight={<Mail className="h-4 w-4" />} placeholder="Both icons" />
    </div>
  ),
};

export const Disabled: Story = {
  args: {
    label: 'Disabled',
    value: 'Cannot edit this',
    disabled: true,
  },
};

export const ReadOnly: Story = {
  args: {
    label: 'Read Only',
    value: 'Pre-filled value',
    readOnly: true,
  },
};