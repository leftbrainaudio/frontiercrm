import type { Meta, StoryObj } from '@storybook/react';
import { Star } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '../../lib/utils';

/* ── EmailRow (recreated to match the inline component from email-page.tsx) ── */

interface EmailMessage {
  id: string;
  subject?: string;
  from_email: string;
  to_emails?: string[];
  cc_emails?: string[];
  body_text?: string;
  body_html?: string;
  is_read: boolean;
  is_starred: boolean;
  direction: 'inbound' | 'outbound';
  sent_at?: string;
  created_at: string;
}

interface EmailRowProps {
  email: EmailMessage;
  selected: boolean;
  onClick?: () => void;
}

function EmailRow({ email, selected, onClick }: EmailRowProps) {
  const from = email.direction === 'inbound' ? email.from_email : email.to_emails?.[0] || 'Unknown';
  const preview = email.body_text?.replace(/\n/g, ' ').slice(0, 80) || 'No preview';

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-full text-left transition-colors',
        'border-b border-border dark:border-dark-border last:border-b-0',
        selected && 'bg-brand-50 dark:bg-brand-900/20',
        !selected && 'hover:bg-surface-secondary dark:hover:bg-dark-surface-secondary',
      )}
    >
      <div className="flex items-start gap-3 px-4 py-3">
        <div className="mt-1.5 shrink-0">
          {!email.is_read ? (
            <div className="h-2.5 w-2.5 rounded-full bg-brand-500 dark:bg-brand-400" aria-label="Unread" />
          ) : (
            <div className="h-2.5 w-2.5" aria-hidden="true" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className={cn('text-sm truncate', !email.is_read ? 'font-semibold text-text-primary dark:text-dark-text-primary' : 'text-text-secondary dark:text-dark-text-secondary')}>
              {from}
            </span>
            <span className="shrink-0 text-xs text-text-tertiary dark:text-dark-text-tertiary">
              {formatDistanceToNow(new Date(email.sent_at || email.created_at), { addSuffix: true })}
            </span>
          </div>
          <p className={cn('text-sm truncate mt-0.5', !email.is_read ? 'font-medium text-text-primary dark:text-dark-text-primary' : 'text-text-secondary dark:text-dark-text-secondary')}>
            {email.subject || '(no subject)'}
          </p>
          <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary truncate mt-0.5">{preview}</p>
        </div>
        <button
          type="button"
          className="shrink-0 mt-1 rounded p-1 text-text-tertiary hover:text-amber-500 dark:text-dark-text-tertiary dark:hover:text-amber-400 transition-colors"
          aria-label={email.is_starred ? 'Unstar email' : 'Star email'}
          onClick={(e) => e.stopPropagation()}
        >
          <Star className={cn('h-4 w-4', email.is_starred && 'fill-amber-500 text-amber-500 dark:fill-amber-400 dark:text-amber-400')} />
        </button>
      </div>
    </button>
  );
}

/* ── Story ── */

const meta: Meta<typeof EmailRow> = {
  title: 'Organisms/EmailRow',
  component: EmailRow,
  tags: ['autodocs'],
  argTypes: {
    selected: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof EmailRow>;

function createEmail(overrides: Partial<EmailMessage>): EmailMessage {
  return {
    id: '1',
    subject: 'Q3 Proposal Review',
    from_email: 'alice@example.com',
    to_emails: ['me@company.com'],
    body_text: 'Please find attached the Q3 proposal with updated pricing and implementation timeline...',
    is_read: false,
    is_starred: false,
    direction: 'inbound',
    created_at: new Date().toISOString(),
    ...overrides,
  };
}

export const Unread: Story = {
  args: {
    email: createEmail({}),
    selected: false,
  },
};

export const Read: Story = {
  args: {
    email: createEmail({ is_read: true }),
    selected: false,
  },
};

export const Starred: Story = {
  args: {
    email: createEmail({ is_read: true, is_starred: true }),
    selected: false,
  },
};

export const Selected: Story = {
  args: {
    email: createEmail({}),
    selected: true,
  },
};

export const Outbound: Story = {
  args: {
    email: createEmail({
      direction: 'outbound',
      to_emails: ['bob@client.com'],
      subject: 'Re: Contract terms',
    }),
    selected: false,
  },
};

export const NoSubjectOrBody: Story = {
  args: {
    email: createEmail({
      subject: '',
      body_text: '',
      is_read: true,
    }),
    selected: false,
  },
};