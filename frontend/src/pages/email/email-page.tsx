import { useState } from 'react';
import DOMPurify from 'dompurify';
import {
  Search,
  Star,
  Mail,
  MailOpen,
  Send,
  Inbox,
  AlertCircle,
  X,
  MessageSquare,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useEmails, useEmail, useToggleStar, useMarkRead, useSendEmail } from '../../api/email';
import { Button } from '../../components/ui/button';
import { Modal } from '../../components/ui/modal';
import { Input } from '../../components/ui/input';
import { Skeleton } from '../../components/ui/skeleton';
import { cn } from '../../lib/utils';
import type { EmailMessage } from '../../types';

type EmailTab = 'inbox' | 'sent' | 'starred';

function tabToParams(tab: EmailTab, search?: string): Record<string, string> {
  const params: Record<string, string> = {};
  if (search) params.search = search;
  if (tab === 'inbox') params.direction = 'inbound';
  else if (tab === 'sent') params.direction = 'outbound';
  else if (tab === 'starred') params.is_starred = 'true';
  return params;
}

function EmailListSkeleton() {
  return (
    <div className="space-y-2 p-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="flex items-start gap-3 rounded-lg p-3">
          <Skeleton variant="circular" width={32} height={32} />
          <div className="flex-1 space-y-2">
            <Skeleton width="70%" height={14} />
            <Skeleton width="40%" height={12} />
            <Skeleton width="90%" height={12} />
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState({ tab }: { tab: EmailTab }) {
  const messages: Record<EmailTab, { title: string; description: string }> = {
    inbox: { title: 'No emails yet', description: 'Your inbox is empty. Connect an email account to get started.' },
    sent: { title: 'No sent emails', description: 'Sent emails will appear here once you compose your first message.' },
    starred: { title: 'No starred emails', description: 'Star important emails to find them quickly.' },
  };
  const m = messages[tab];
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center px-4">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-surface-secondary dark:bg-dark-surface-secondary">
        <Mail className="h-8 w-8 text-text-tertiary dark:text-dark-text-tertiary" />
      </div>
      <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">{m.title}</h3>
      <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary max-w-sm">{m.description}</p>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center px-4">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-50 dark:bg-red-900/20">
        <AlertCircle className="h-8 w-8 text-red-500 dark:text-red-400" />
      </div>
      <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">Something went wrong</h3>
      <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary max-w-sm">{message}</p>
      <Button variant="secondary" className="mt-4" onClick={() => window.location.reload()}>
        Try again
      </Button>
    </div>
  );
}

interface EmailRowProps {
  email: EmailMessage;
  selected: boolean;
  onClick: () => void;
}

function EmailRow({ email, selected, onClick }: EmailRowProps) {
  const toggleStar = useToggleStar();

  const handleStar = (e: React.MouseEvent) => {
    e.stopPropagation();
    toggleStar.mutate(email.id);
  };

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
        {/* Read/unread dot */}
        <div className="mt-1.5 shrink-0">
          {!email.is_read ? (
            <div className="h-2.5 w-2.5 rounded-full bg-brand-500 dark:bg-brand-400" aria-label="Unread" />
          ) : (
            <div className="h-2.5 w-2.5" aria-hidden="true" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span
              className={cn(
                'text-sm truncate',
                !email.is_read
                  ? 'font-semibold text-text-primary dark:text-dark-text-primary'
                  : 'text-text-secondary dark:text-dark-text-secondary',
              )}
            >
              {from}
            </span>
            <span className="shrink-0 text-xs text-text-tertiary dark:text-dark-text-tertiary">
              {formatDistanceToNow(new Date(email.sent_at || email.created_at), { addSuffix: true })}
            </span>
          </div>
          <p
            className={cn(
              'text-sm truncate mt-0.5',
              !email.is_read
                ? 'font-medium text-text-primary dark:text-dark-text-primary'
                : 'text-text-secondary dark:text-dark-text-secondary',
            )}
          >
            {email.subject || '(no subject)'}
          </p>
          <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary truncate mt-0.5">
            {preview}
          </p>
        </div>

        {/* Star button */}
        <button
          type="button"
          onClick={handleStar}
          className="shrink-0 mt-1 rounded p-1 text-text-tertiary hover:text-amber-500 dark:text-dark-text-tertiary dark:hover:text-amber-400 transition-colors"
          aria-label={email.is_starred ? 'Unstar email' : 'Star email'}
        >
          <Star
            className={cn('h-4 w-4', email.is_starred && 'fill-amber-500 text-amber-500 dark:fill-amber-400 dark:text-amber-400')}
          />
        </button>
      </div>
    </button>
  );
}

function EmailDetail({ email, onClose }: { email: EmailMessage; onClose: () => void }) {
  const markRead = useMarkRead();

  const handleMarkRead = () => {
    if (!email.is_read) {
      markRead.mutate(email.id);
    }
  };

  const handleStar = () => {
    const toggleStar = useToggleStar();
    toggleStar.mutate(email.id);
  };

  // Mark as read when opening
  useState(() => {
    handleMarkRead();
  });

  return (
    <div className="flex h-full flex-col">
      {/* Detail header */}
      <div className="flex items-center justify-between border-b border-border dark:border-dark-border px-4 py-3">
        <h2 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary truncate">
          {email.subject || '(no subject)'}
        </h2>
        <button
          type="button"
          onClick={onClose}
          className="shrink-0 rounded-lg p-1.5 text-text-tertiary hover:text-text-primary hover:bg-surface-secondary transition-colors lg:hidden dark:text-dark-text-tertiary dark:hover:text-dark-text-primary dark:hover:bg-dark-surface-secondary"
          aria-label="Close detail"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* From / To / Date */}
      <div className="border-b border-border dark:border-dark-border px-4 py-3 space-y-1.5">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-sm font-medium text-text-primary dark:text-dark-text-primary">From:</span>{' '}
            <span className="text-sm text-text-secondary dark:text-dark-text-secondary">{email.from_email}</span>
          </div>
          <span className="text-xs text-text-tertiary dark:text-dark-text-tertiary">
            {formatDistanceToNow(new Date(email.sent_at || email.created_at), { addSuffix: true })}
          </span>
        </div>
        <div>
          <span className="text-sm font-medium text-text-primary dark:text-dark-text-primary">To:</span>{' '}
          <span className="text-sm text-text-secondary dark:text-dark-text-secondary">
            {email.to_emails?.join(', ') || '—'}
          </span>
        </div>
        {email.cc_emails && email.cc_emails.length > 0 && (
          <div>
            <span className="text-sm font-medium text-text-primary dark:text-dark-text-primary">Cc:</span>{' '}
            <span className="text-sm text-text-secondary dark:text-dark-text-secondary">
              {email.cc_emails.join(', ')}
            </span>
          </div>
        )}
        <div>
          <span className="text-sm font-medium text-text-primary dark:text-dark-text-primary">Date:</span>{' '}
          <span className="text-sm text-text-secondary dark:text-dark-text-secondary">
            {new Date(email.sent_at || email.created_at).toLocaleString()}
          </span>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex gap-2 border-b border-border dark:border-dark-border px-4 py-2">
        {email.is_read && (
          <Button size="sm" variant="ghost" icon={<Mail className="h-4 w-4" />} onClick={handleMarkRead}>
            Mark unread
          </Button>
        )}
        <Button
          size="sm"
          variant="ghost"
          icon={<Star className={cn('h-4 w-4', email.is_starred && 'fill-amber-500 text-amber-500')} />}
          onClick={handleStar}
        >
          {email.is_starred ? 'Starred' : 'Star'}
        </Button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {email.body_html ? (
          <div
            className="prose prose-sm max-w-none dark:prose-invert text-text-primary dark:text-dark-text-primary"
            dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(email.body_html) }}
          />
        ) : email.body_text ? (
          <pre className="whitespace-pre-wrap text-sm text-text-primary dark:text-dark-text-primary font-sans">
            {email.body_text}
          </pre>
        ) : (
          <p className="text-sm text-text-tertiary dark:text-dark-text-tertiary">No content</p>
        )}
      </div>
    </div>
  );
}

export function EmailPage() {
  const [activeTab, setActiveTab] = useState<EmailTab>('inbox');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
  const [composeOpen, setComposeOpen] = useState(false);
  const [composeTo, setComposeTo] = useState('');
  const [composeSubject, setComposeSubject] = useState('');
  const [composeBody, setComposeBody] = useState('');

  const params = tabToParams(activeTab, searchQuery || undefined);
  const { data, isLoading, isError, error } = useEmails(params);
  const { data: selectedEmail } = useEmail(selectedEmailId ?? undefined);
  const sendEmail = useSendEmail();
  const markRead = useMarkRead();

  const emails = data?.results ?? [];

  const handleSend = async () => {
    if (!composeTo.trim() || !composeSubject.trim()) return;
    try {
      await sendEmail.mutateAsync({
        to_emails: [composeTo],
        subject: composeSubject,
        body_text: composeBody,
        direction: 'outbound',
        from_email: '',
      } as any);
      setComposeTo('');
      setComposeSubject('');
      setComposeBody('');
      setComposeOpen(false);
    } catch {
      // error handled by toast
    }
  };

  const handleSelectEmail = (id: string) => {
    setSelectedEmailId(id);
    // Mark as read on mobile
    const email = emails.find((e) => e.id === id);
    if (email && !email.is_read) {
      markRead.mutate(id);
    }
  };

  const TABS: { key: EmailTab; label: string; icon: React.ReactNode }[] = [
    { key: 'inbox', label: 'Inbox', icon: <Inbox className="h-4 w-4" /> },
    { key: 'sent', label: 'Sent', icon: <Send className="h-4 w-4" /> },
    { key: 'starred', label: 'Starred', icon: <Star className="h-4 w-4" /> },
  ];

  return (
    <div className="flex h-full flex-col">
      {/* Top bar with search */}
      <div className="flex items-center gap-3 border-b border-border dark:border-dark-border px-4 py-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-tertiary dark:text-dark-text-tertiary pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search emails..."
            className="w-full rounded-lg border border-border bg-white pl-9 pr-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary dark:placeholder:text-dark-text-tertiary"
            aria-label="Search emails"
          />
        </div>
        <Button size="sm" icon={<MessageSquare className="h-4 w-4" />} onClick={() => setComposeOpen(true)}>
          Compose
        </Button>
      </div>

      {/* Tab bar */}
      <div className="flex border-b border-border dark:border-dark-border">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => {
              setActiveTab(tab.key);
              setSelectedEmailId(null);
            }}
            className={cn(
              'flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-brand-500',
              activeTab === tab.key
                ? 'border-brand-600 text-brand-600 dark:border-brand-400 dark:text-brand-400'
                : 'border-transparent text-text-secondary hover:text-text-primary dark:text-dark-text-secondary dark:hover:text-dark-text-primary',
            )}
            aria-current={activeTab === tab.key ? 'page' : undefined}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Email content area: split pane on desktop, single pane on mobile */}
      <div className="flex flex-1 overflow-hidden">
        {/* Email list - left pane */}
        <div
          className={cn(
            'flex flex-col overflow-y-auto border-r border-border dark:border-dark-border',
            // On mobile: hide list when an email is selected, on desktop always show
            selectedEmail && selectedEmailId ? 'hidden lg:flex lg:w-[380px] xl:w-[420px]' : 'flex-1 lg:w-[380px] xl:w-[420px] lg:flex-none',
          )}
        >
          {isLoading ? (
            <EmailListSkeleton />
          ) : isError ? (
            <ErrorState message={(error as any)?.message || 'Failed to load emails'} />
          ) : emails.length === 0 ? (
            <EmptyState tab={activeTab} />
          ) : (
            <div className="divide-y divide-border dark:divide-dark-border">
              {emails.map((email) => (
                <EmailRow
                  key={email.id}
                  email={email}
                  selected={selectedEmailId === email.id}
                  onClick={() => handleSelectEmail(email.id)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Email detail - right pane */}
        <div
          className={cn(
            'flex flex-col flex-1 overflow-hidden',
            // On mobile: hide detail unless an email is selected
            selectedEmailId ? 'flex' : 'hidden lg:flex',
          )}
        >
          {selectedEmail ? (
            <EmailDetail email={selectedEmail} onClose={() => setSelectedEmailId(null)} />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-surface-secondary dark:bg-dark-surface-secondary">
                <MailOpen className="h-8 w-8 text-text-tertiary dark:text-dark-text-tertiary" />
              </div>
              <h3 className="text-lg font-semibold text-text-primary dark:text-dark-text-primary">
                Select an email
              </h3>
              <p className="mt-1 text-sm text-text-secondary dark:text-dark-text-secondary max-w-sm">
                Choose a message from the list to read it here.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Compose Modal */}
      <Modal
        open={composeOpen}
        onClose={() => setComposeOpen(false)}
        title="Compose Email"
        size="lg"
        footer={
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setComposeOpen(false)}>
              Discard
            </Button>
            <Button onClick={handleSend} loading={sendEmail.isPending} disabled={!composeTo.trim() || !composeSubject.trim()}>
              Send
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <Input
            label="To"
            type="email"
            value={composeTo}
            onChange={(e) => setComposeTo(e.target.value)}
            placeholder="recipient@example.com"
            required
          />
          <Input
            label="Subject"
            value={composeSubject}
            onChange={(e) => setComposeSubject(e.target.value)}
            placeholder="Email subject"
            required
          />
          <div>
            <label
              htmlFor="compose-body"
              className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary"
            >
              Message
            </label>
            <textarea
              id="compose-body"
              value={composeBody}
              onChange={(e) => setComposeBody(e.target.value)}
              rows={10}
              className="w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary dark:placeholder:text-dark-text-tertiary"
              placeholder="Write your message..."
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}