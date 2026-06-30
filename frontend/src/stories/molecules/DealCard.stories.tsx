import type { Meta, StoryObj } from '@storybook/react';
import { DealCard } from '../../components/molecules/deal-card';
import type { DealCardData } from '../../components/molecules/deal-card';

const sampleDeal: DealCardData = {
  id: '1',
  name: 'Enterprise Plan - Acme Corp',
  value: 50000,
  currency: 'USD',
  contact_name: 'Alice Johnson',
  account_name: 'Acme Corp',
  stage_name: 'Negotiation',
  expected_close_date: '2026-08-15',
  win_probability: 80,
};

const meta: Meta<typeof DealCard> = {
  title: 'Molecules/DealCard',
  component: DealCard,
  tags: ['autodocs'],
  argTypes: {
    loading: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof DealCard>;

export const Default: Story = {
  args: {
    deal: sampleDeal,
  },
};

export const HighProbability: Story = {
  args: {
    deal: {
      ...sampleDeal,
      name: 'Annual Subscription',
      value: 12000,
      win_probability: 90,
      stage_name: 'Closed Won',
    },
  },
};

export const MediumProbability: Story = {
  args: {
    deal: {
      ...sampleDeal,
      name: 'Pro Upgrade - BetaCorp',
      value: 8000,
      win_probability: 50,
      stage_name: 'Proposal',
    },
  },
};

export const LowProbability: Story = {
  args: {
    deal: {
      ...sampleDeal,
      name: 'Starter Package',
      value: 2000,
      win_probability: 15,
      stage_name: 'Lead',
    },
  },
};

export const Minimal: Story = {
  args: {
    deal: {
      id: '2',
      name: 'Quick Deal',
      value: 5000,
    },
  },
};

export const Loading: Story = {
  args: {
    deal: sampleDeal,
    loading: true,
  },
};

export const DealList: Story = {
  render: () => (
    <div className="flex flex-col gap-3 max-w-sm">
      <DealCard
        deal={{
          id: '1',
          name: 'Enterprise Plan - Acme Corp',
          value: 50000,
          contact_name: 'Alice Johnson',
          stage_name: 'Negotiation',
          win_probability: 80,
        }}
      />
      <DealCard
        deal={{
          id: '2',
          name: 'Pro Upgrade - BetaCorp',
          value: 12000,
          contact_name: 'Bob Smith',
          stage_name: 'Proposal',
          win_probability: 45,
        }}
      />
      <DealCard
        deal={{
          id: '3',
          name: 'Starter Package - Gamma LLC',
          value: 3000,
          stage_name: 'Lead',
          win_probability: 20,
        }}
      />
    </div>
  ),
};