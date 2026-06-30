import type { Meta, StoryObj } from '@storybook/react';
import { ActivityCard } from '../../pages/activities/activity-card';
import type { TimelineEntry } from '../../types';

const sampleActivity: TimelineEntry = {
  id: '1',
  activity_type: 'note',
  title: 'Follow-up call completed',
  description: 'Discussed next quarter plans and budget allocation. Client expressed interest in enterprise tier.',
  created_at: new Date().toISOString(),
  actor: { id: 'u1', name: 'Alice Johnson', avatar_url: '' },
  entity: { id: 'e1', name: 'Acme Corp', url: '/contacts/e1', type: 'contact' },
  metadata: {},
};

const meta: Meta<typeof ActivityCard> = {
  title: 'Organisms/ActivityCard',
  component: ActivityCard,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof ActivityCard>;

export const Default: Story = {
  args: {
    activity: sampleActivity,
  },
};

export const EmailActivity: Story = {
  args: {
    activity: {
      ...sampleActivity,
      activity_type: 'email',
      title: 'Proposal sent',
      description: 'Sent Q3 proposal with pricing breakdown and implementation timeline.',
    },
  },
};

export const MeetingActivity: Story = {
  args: {
    activity: {
      ...sampleActivity,
      activity_type: 'meeting',
      title: 'Product demo',
      description: 'Demonstrated new features including pipeline forecasting and CSV export.',
    },
  },
};

export const DealStageChange: Story = {
  args: {
    activity: {
      ...sampleActivity,
      activity_type: 'deal_stage_change',
      title: 'Deal moved to Negotiation',
      description: 'Deal progressed from Proposal to Negotiation stage.',
    },
  },
};

export const CallActivity: Story = {
  args: {
    activity: {
      ...sampleActivity,
      activity_type: 'call',
      title: 'Discovery call',
      description: 'Initial call with prospect to understand requirements.',
    },
  },
};

export const NoActor: Story = {
  args: {
    activity: {
      ...sampleActivity,
      actor: { id: 'system', name: '', avatar_url: '' },
    },
  },
};

export const NoEntity: Story = {
  args: {
    activity: {
      ...sampleActivity,
      entity: { id: '', name: '', url: '', type: '' },
    },
  },
};