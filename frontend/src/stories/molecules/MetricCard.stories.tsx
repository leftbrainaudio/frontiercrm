import type { Meta, StoryObj } from '@storybook/react';
import { MetricCard } from '../../components/molecules/metric-card';
import { DollarSign, TrendingUp, Users, Target } from 'lucide-react';

const meta: Meta<typeof MetricCard> = {
  title: 'Molecules/MetricCard',
  component: MetricCard,
  tags: ['autodocs'],
  argTypes: {
    loading: { control: 'boolean' },
    trendUp: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof MetricCard>;

export const Default: Story = {
  args: {
    label: 'Total Pipeline Value',
    value: '$1,250,000',
    icon: <DollarSign className="h-5 w-5" />,
  },
};

export const WithTrend: Story = {
  args: {
    label: 'Win Rate',
    value: '68%',
    trend: '+12% vs last quarter',
    trendUp: true,
    icon: <TrendingUp className="h-5 w-5" />,
  },
};

export const NegativeTrend: Story = {
  args: {
    label: 'Avg Days to Close',
    value: '45',
    trend: '+8% vs last quarter',
    trendUp: false,
    icon: <Target className="h-5 w-5" />,
  },
};

export const WithSubtitle: Story = {
  args: {
    label: 'Active Deals',
    value: '24',
    subtitle: 'Across 6 stages',
    icon: <Users className="h-5 w-5" />,
  },
};

export const Loading: Story = {
  args: {
    label: 'Total Revenue',
    value: '$500,000',
    loading: true,
  },
};

export const NoIcon: Story = {
  args: {
    label: 'Tasks Due Today',
    value: '12',
    trend: '3 overdue',
    trendUp: false,
  },
};

export const DashboardRow: Story = {
  render: () => (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricCard
        label="Pipeline Value"
        value="$2.4M"
        trend="+8.2%"
        icon={<DollarSign className="h-5 w-5" />}
      />
      <MetricCard
        label="Win Rate"
        value="72%"
        trend="+5%"
        icon={<TrendingUp className="h-5 w-5" />}
      />
      <MetricCard
        label="Active Deals"
        value="48"
        subtitle="This quarter"
        icon={<Users className="h-5 w-5" />}
      />
      <MetricCard
        label="Avg Deal Size"
        value="$52K"
        trend="-3.1%"
        trendUp={false}
        icon={<Target className="h-5 w-5" />}
      />
    </div>
  ),
};