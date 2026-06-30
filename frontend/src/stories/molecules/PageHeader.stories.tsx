import type { Meta, StoryObj } from '@storybook/react';
import { PageHeader } from '../../components/molecules/page-header';
import { Button } from '../../components/atoms/button';
import { Plus, Download } from 'lucide-react';

const meta: Meta<typeof PageHeader> = {
  title: 'Molecules/PageHeader',
  component: PageHeader,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof PageHeader>;

export const Default: Story = {
  args: {
    title: 'Dashboard',
    description: 'Your sales overview at a glance.',
  },
};

export const WithActions: Story = {
  args: {
    title: 'Contacts',
    description: 'Manage your contacts and accounts.',
    actions: (
      <>
        <Button variant="secondary" size="sm" icon={<Download className="h-4 w-4" />}>
          Export
        </Button>
        <Button size="sm" icon={<Plus className="h-4 w-4" />}>
          Add Contact
        </Button>
      </>
    ),
  },
};

export const WithBreadcrumbs: Story = {
  args: {
    title: 'Enterprise Plan',
    description: 'Deal details and activity history.',
    breadcrumbs: [
      { label: 'Deals', href: '#deals' },
      { label: 'Enterprise Plan' },
    ],
    actions: (
      <Button size="sm" variant="outline">
        Edit Deal
      </Button>
    ),
  },
};

export const DeepBreadcrumbs: Story = {
  args: {
    title: 'Settings',
    description: 'Manage your account and team preferences.',
    breadcrumbs: [
      { label: 'Dashboard', href: '#dashboard' },
      { label: 'Settings', href: '#settings' },
      { label: 'Team' },
    ],
  },
};

export const TitleOnly: Story = {
  args: {
    title: 'Reports',
  },
};

export const WithActionsAndBreadcrumbs: Story = {
  args: {
    title: 'Create Report',
    description: 'Build a custom report with filters and metrics.',
    breadcrumbs: [
      { label: 'Reports', href: '#reports' },
      { label: 'Create' },
    ],
    actions: (
      <>
        <Button variant="ghost" size="sm">
          Cancel
        </Button>
        <Button size="sm">
          Save Report
        </Button>
      </>
    ),
  },
};