import type { Meta, StoryObj } from '@storybook/react';
import { StatCard } from '../../components/molecules/stat-card';
import { BarChart3, Activity } from 'lucide-react';

const meta: Meta<typeof StatCard> = {
  title: 'Molecules/StatCard',
  component: StatCard,
  tags: ['autodocs'],
  argTypes: {
    loading: { control: 'boolean' },
    columns: { control: 'select', options: [2, 3, 4] },
  },
};

export default meta;
type Story = StoryObj<typeof StatCard>;

export const Default: Story = {
  args: {
    title: 'Revenue Summary',
    stats: [
      { label: 'Total Revenue', value: '$1.2M', trend: '+12%', trendUp: true },
      { label: 'Won Deals', value: '$850K', trend: '+8%', trendUp: true },
      { label: 'Active Pipeline', value: '$350K', trend: '-5%', trendUp: false },
    ],
  },
};

export const WithIcon: Story = {
  args: {
    title: 'Pipeline Overview',
    icon: <BarChart3 className="h-4 w-4" />,
    stats: [
      { label: 'Total Pipeline', value: '$2.4M', trend: '+18%', trendUp: true },
      { label: 'Weighted Pipeline', value: '$1.8M' },
      { label: 'Avg Deal Size', value: '$52K' },
    ],
  },
};

export const TwoColumns: Story = {
  args: {
    columns: 2,
    stats: [
      { label: 'Active Deals', value: '48', trend: '+6', trendUp: true },
      { label: 'Win Rate', value: '72%', trend: '+5%', trendUp: true },
    ],
  },
};

export const FourColumns: Story = {
  args: {
    title: 'Activity Metrics',
    icon: <Activity className="h-4 w-4" />,
    columns: 4,
    stats: [
      { label: 'Calls', value: '128', trend: '+15%', trendUp: true },
      { label: 'Emails', value: '342', trend: '+22%', trendUp: true },
      { label: 'Meetings', value: '56', trend: '-8%', trendUp: false },
      { label: 'Tasks', value: '89', trend: '+3%', trendUp: true },
    ],
  },
};

export const WithoutTrend: Story = {
  args: {
    title: 'Quick Stats',
    stats: [
      { label: 'Open Deals', value: '24' },
      { label: 'Contacts', value: '1,247' },
      { label: 'Accounts', value: '89' },
    ],
  },
};

export const Loading: Story = {
  args: {
    title: 'Loading...',
    loading: true,
    stats: [],
  },
};

export const NoTitle: Story = {
  args: {
    stats: [
      { label: 'Emails Sent', value: '2,847' },
      { label: 'Open Rate', value: '68%', trend: '+3%', trendUp: true },
      { label: 'Click Rate', value: '24%', trend: '-1%', trendUp: false },
    ],
  },
};