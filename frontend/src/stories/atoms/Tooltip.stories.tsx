import type { Meta, StoryObj } from '@storybook/react';
import { Tooltip } from '../../components/ui/tooltip';
import { Button } from '../../components/atoms/button';

const meta: Meta<typeof Tooltip> = {
  title: 'Atoms/Tooltip',
  component: Tooltip,
  tags: ['autodocs'],
  argTypes: {
    position: { control: 'select', options: ['top', 'bottom', 'left', 'right'] },
    arrow: { control: 'boolean' },
    showDelay: { control: 'number' },
    hideDelay: { control: 'number' },
  },
};

export default meta;
type Story = StoryObj<typeof Tooltip>;

export const Default: Story = {
  args: {
    content: 'This is a tooltip',
    children: <Button variant="secondary">Hover me</Button>,
  },
};

export const Positions: Story = {
  render: () => (
    <div className="flex items-center justify-center gap-8 p-16">
      <Tooltip content="Top tooltip" position="top">
        <Button variant="secondary">Top</Button>
      </Tooltip>
      <Tooltip content="Bottom tooltip" position="bottom">
        <Button variant="secondary">Bottom</Button>
      </Tooltip>
      <Tooltip content="Left tooltip" position="left">
        <Button variant="secondary">Left</Button>
      </Tooltip>
      <Tooltip content="Right tooltip" position="right">
        <Button variant="secondary">Right</Button>
      </Tooltip>
    </div>
  ),
};

export const WithoutArrow: Story = {
  args: {
    content: 'No arrow indicator',
    children: <Button variant="secondary">No arrow</Button>,
    arrow: false,
  },
};

export const LongContent: Story = {
  args: {
    content: 'This is a much longer tooltip with detailed information to demonstrate how it handles wrapping and longer text content',
    children: <Button variant="secondary">Long tooltip</Button>,
  },
};