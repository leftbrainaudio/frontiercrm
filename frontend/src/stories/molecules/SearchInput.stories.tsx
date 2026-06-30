import type { Meta, StoryObj } from '@storybook/react';
import { SearchInput } from '../../components/molecules/search-input';
import { useState } from 'react';

const meta: Meta<typeof SearchInput> = {
  title: 'Molecules/SearchInput',
  component: SearchInput,
  tags: ['autodocs'],
  argTypes: {
    size: { control: 'select', options: ['sm', 'md'] },
    disabled: { control: 'boolean' },
    loading: { control: 'boolean' },
    placeholder: { control: 'text' },
  },
};

export default meta;
type Story = StoryObj<typeof SearchInput>;

export const Default: Story = {
  args: {
    placeholder: 'Search contacts, deals...',
  },
};

export const WithValue: Story = {
  render: () => {
    const [value, setValue] = useState('Acme Corp');
    return (
      <SearchInput
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onClear={() => setValue('')}
        placeholder="Search..."
      />
    );
  },
};

export const Loading: Story = {
  args: {
    loading: true,
    placeholder: 'Searching...',
  },
};

export const Disabled: Story = {
  args: {
    disabled: true,
    placeholder: 'Search disabled',
    value: '',
  },
};

export const Sizes: Story = {
  render: () => (
    <div className="flex flex-col gap-3 max-w-sm">
      <SearchInput size="sm" placeholder="Small search" />
      <SearchInput size="md" placeholder="Medium search (default)" />
    </div>
  ),
};

export const ControlledInteractive: Story = {
  render: () => {
    const [value, setValue] = useState('');
    return (
      <div className="max-w-sm space-y-2">
        <SearchInput
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onClear={() => setValue('')}
          placeholder="Type to search..."
        />
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Current value: {value || '(empty)'}
        </p>
      </div>
    );
  },
};