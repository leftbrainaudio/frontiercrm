import type { Meta, StoryObj } from '@storybook/react';
import { Select } from '../../components/atoms/select';

const meta: Meta<typeof Select> = {
  title: 'Atoms/Select',
  component: Select,
  tags: ['autodocs'],
  argTypes: {
    size: { control: 'select', options: ['sm', 'md'] },
    variant: { control: 'select', options: ['outline', 'filled'] },
    disabled: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof Select>;

const sampleOptions = (
  <>
    <option value="option1">Option 1</option>
    <option value="option2">Option 2</option>
    <option value="option3">Option 3</option>
  </>
);

export const Default: Story = {
  args: {
    children: sampleOptions,
    placeholder: 'Select an option',
  },
};

export const WithLabel: Story = {
  args: {
    label: 'Priority',
    children: sampleOptions,
    placeholder: 'Select priority',
  },
};

export const WithError: Story = {
  args: {
    label: 'Status',
    error: 'Please select a status',
    children: sampleOptions,
  },
};

export const WithHelperText: Story = {
  args: {
    label: 'Department',
    helperText: 'Choose your team department',
    children: sampleOptions,
  },
};

export const Sizes: Story = {
  render: () => (
    <div className="flex flex-col gap-3 max-w-sm">
      <Select size="sm" label="Small" placeholder="Small select">
        {sampleOptions}
      </Select>
      <Select size="md" label="Medium" placeholder="Medium select">
        {sampleOptions}
      </Select>
    </div>
  ),
};

export const Variants: Story = {
  render: () => (
    <div className="flex flex-col gap-3 max-w-sm">
      <Select variant="outline" label="Outline" placeholder="Outline">
        {sampleOptions}
      </Select>
      <Select variant="filled" label="Filled" placeholder="Filled">
        {sampleOptions}
      </Select>
    </div>
  ),
};

export const Disabled: Story = {
  args: {
    label: 'Disabled',
    children: sampleOptions,
    disabled: true,
  },
};