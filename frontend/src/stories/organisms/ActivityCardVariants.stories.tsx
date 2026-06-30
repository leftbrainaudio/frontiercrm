import type { Meta, StoryObj } from '@storybook/react';
import { ActivityCard } from '../../pages/activities/activity-card';
import type { TimelineEntry } from '../../types';

/**
 * The ActivityCard component is used to display individual timeline
 * entries on the Activities and Timeline pages. Each card shows an
 * icon, title, description, timestamp, actor, and an optional link
 * to the related entity.
 */
const meta: Meta<typeof ActivityCard> = {
  title: 'Organisms/ActivityCard',
  component: ActivityCard,
  tags: ['autodocs'],
  parameters: {
    docs: {
      description: {
        component: 'Displays a single timeline activity entry with type-specific icon, actor info, and entity link.',
      },
    },
  },
};

export default meta;
type Story = StoryObj<typeof ActivityCard>;

function createActivity(overrides: Partial<TimelineEntry>): TimelineEntry {
  return {
    id: '1',
    activity_type: 'note',
    title: 'Activity title',
    description: 'Activity description goes here.',
    created_at: new Date().toISOString(),
    actor: { id: 'u1', name: 'Alice Johnson', avatar_url: '' },
    entity: { id: 'e1', name: 'Acme Corp', url: '/contacts/e1', type: 'contact' },
    metadata: {},
    ...overrides,
  };
}

export const Overview: Story = {
  render: () => (
    <div className="max-w-2xl">
      <ActivityCard activity={createActivity({})} />
    </div>
  ),
};

export const AllTypes: Story = {
  render: () => {
    const types: TimelineEntry['activity_type'][] = [
      'note', 'email', 'meeting', 'call', 'task',
      'deal_stage_change', 'deal_status_change', 'file_upload', 'system',
    ];
    return (
      <div className="max-w-2xl">
        {types.map((type) => (
          <ActivityCard
            key={type}
            activity={createActivity({
              id: type,
              activity_type: type,
              title: `${type.replace(/_/g, ' ')} activity`,
              description: 'This type has its own icon and color scheme.',
            })}
          />
        ))}
      </div>
    );
  },
};

export const LongDescription: Story = {
  render: () => (
    <div className="max-w-2xl">
      <ActivityCard
        activity={createActivity({
          activity_type: 'note',
          title: 'Detailed call notes',
          description:
            'During our hour-long discovery session, the client outlined their primary pain points including fragmented data across spreadsheets, lack of pipeline visibility for the sales team, and manual reporting that takes hours each week. They are evaluating CRM solutions with a decision expected by end of quarter. Key stakeholders include the VP of Sales, Head of Operations, and the IT director. Next steps include scheduling a technical deep-dive with their engineering team to review API integration requirements.',
        })}
      />
    </div>
  ),
};