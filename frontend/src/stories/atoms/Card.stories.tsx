import type { Meta, StoryObj } from '@storybook/react';
import { Card } from '../../components/molecules/card';
import { Button } from '../../components/atoms/button';

const meta: Meta<typeof Card> = {
  title: 'Atoms/Card',
  component: Card,
  tags: ['autodocs'],
  argTypes: {
    variant: { control: 'select', options: ['default', 'elevated', 'outline', 'interactive'] },
    padding: { control: 'select', options: ['none', 'sm', 'md', 'lg'] },
  },
};

export default meta;
type Story = StoryObj<typeof Card>;

export const Default: Story = {
  args: {
    children: <p className="text-sm text-gray-700 dark:text-gray-300">Card content goes here.</p>,
  },
};

export const Variants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4">
      <Card variant="default" className="w-56">
        <p className="text-sm">Default</p>
      </Card>
      <Card variant="elevated" className="w-56">
        <p className="text-sm">Elevated</p>
      </Card>
      <Card variant="outline" className="w-56">
        <p className="text-sm">Outline</p>
      </Card>
      <Card variant="interactive" className="w-56">
        <p className="text-sm">Interactive</p>
      </Card>
    </div>
  ),
};

export const WithHeader: Story = {
  args: {
    title: 'Card Title',
    subtitle: 'Optional subtitle text',
    children: (
      <p className="text-sm text-gray-700 dark:text-gray-300">
        Main card body content with detailed information.
      </p>
    ),
  },
};

export const WithHeaderAndFooter: Story = {
  render: () => (
    <Card
      title="User Profile"
      subtitle="Personal information"
      footer={<Button size="sm">Edit Profile</Button>}
    >
      <div className="text-sm space-y-2 text-gray-700 dark:text-gray-300">
        <p><strong>Name:</strong> John Doe</p>
        <p><strong>Email:</strong> john@example.com</p>
      </div>
    </Card>
  ),
};

export const PaddingVariants: Story = {
  render: () => (
    <div className="flex flex-col gap-3 max-w-xs">
      <Card padding="none">
        <div className="bg-blue-100 p-2 text-sm">No padding</div>
      </Card>
      <Card padding="sm">
        <p className="text-sm">Small padding</p>
      </Card>
      <Card padding="md">
        <p className="text-sm">Medium padding (default)</p>
      </Card>
      <Card padding="lg">
        <p className="text-sm">Large padding</p>
      </Card>
    </div>
  ),
};