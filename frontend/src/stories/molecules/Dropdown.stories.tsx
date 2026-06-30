import type { Meta, StoryObj } from '@storybook/react';
import { Dropdown } from '../../components/molecules/dropdown';
import { Button } from '../../components/atoms/button';
import { Edit, Trash2, Copy, Share2, Download, Archive } from 'lucide-react';

const meta: Meta<typeof Dropdown> = {
  title: 'Molecules/Dropdown',
  component: Dropdown,
  tags: ['autodocs'],
  argTypes: {
    align: { control: 'select', options: ['start', 'end'] },
  },
};

export default meta;
type Story = StoryObj<typeof Dropdown>;

export const Default: Story = {
  args: {
    trigger: <Button variant="secondary">Actions</Button>,
    items: [
      { label: 'Edit', onClick: () => alert('Edit') },
      { label: 'Copy', onClick: () => alert('Copy') },
      { label: 'Delete', onClick: () => alert('Delete') },
    ],
  },
};

export const WithIcons: Story = {
  args: {
    trigger: <Button variant="secondary">Actions</Button>,
    items: [
      { label: 'Edit', icon: <Edit className="h-4 w-4" />, onClick: () => alert('Edit') },
      { label: 'Duplicate', icon: <Copy className="h-4 w-4" />, onClick: () => alert('Duplicate') },
      { label: 'Share', icon: <Share2 className="h-4 w-4" />, onClick: () => alert('Share') },
    ],
  },
};

export const WithDividers: Story = {
  args: {
    trigger: <Button variant="secondary">More</Button>,
    items: [
      { label: 'Edit', icon: <Edit className="h-4 w-4" />, onClick: () => alert('Edit') },
      { label: 'Duplicate', icon: <Copy className="h-4 w-4" />, onClick: () => alert('Duplicate') },
      { label: '', divider: true },
      { label: 'Export', icon: <Download className="h-4 w-4" />, onClick: () => alert('Export') },
      { label: '', divider: true },
      { label: 'Archive', icon: <Archive className="h-4 w-4" />, onClick: () => alert('Archive') },
      { label: 'Delete', icon: <Trash2 className="h-4 w-4" />, danger: true, onClick: () => alert('Delete') },
    ],
  },
};

export const AlignEnd: Story = {
  render: () => (
    <div className="flex justify-end">
      <Dropdown
        align="end"
        trigger={<Button variant="secondary">End Aligned</Button>}
        items={[
          { label: 'Option A' },
          { label: 'Option B' },
          { label: 'Option C' },
        ]}
      />
    </div>
  ),
};

export const WithSubmenu: Story = {
  args: {
    trigger: <Button variant="secondary">File</Button>,
    items: [
      { label: 'New File', icon: <Edit className="h-4 w-4" /> },
      {
        label: 'Export As',
        icon: <Download className="h-4 w-4" />,
        submenu: [
          { label: 'PDF', onClick: () => alert('Export as PDF') },
          { label: 'CSV', onClick: () => alert('Export as CSV') },
          { label: 'JSON', onClick: () => alert('Export as JSON') },
        ],
      },
      { label: '', divider: true },
      { label: 'Delete', icon: <Trash2 className="h-4 w-4" />, danger: true },
    ],
  },
};