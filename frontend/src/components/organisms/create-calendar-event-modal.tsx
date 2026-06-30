import { useState } from 'react';
import {
  Calendar,
  MapPin,
  Users,
  Clock,
  Bell,
  Sun,
} from 'lucide-react';
import { Modal } from '../molecules/modal';
import { Input } from '../atoms/input';
import { Button } from '../atoms/button';
import toast from 'react-hot-toast';
import { useCreateCalendarEvent } from '../../api/sync';
import type { CalendarEventCreatePayload } from '../../types';

interface CreateCalendarEventModalProps {
  open: boolean;
  onClose: () => void;
  /** Pre-fill entity linking */
  defaultEntityType?: string;
  defaultEntityId?: string;
}

const TIMEZONES = [
  'UTC',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Berlin',
  'Europe/Paris',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Asia/Kolkata',
  'Australia/Sydney',
  'Pacific/Auckland',
];

function getDefaultEnd(start: string): string {
  if (!start) return '';
  try {
    const d = new Date(start);
    if (isNaN(d.getTime())) return '';
    d.setHours(d.getHours() + 1);
    return d.toISOString().slice(0, 16);
  } catch {
    return '';
  }
}

export function CreateCalendarEventModal({
  open,
  onClose,
  defaultEntityType,
  defaultEntityId,
}: CreateCalendarEventModalProps) {
  const createEvent = useCreateCalendarEvent();

  // Form state
  const [title, setTitle] = useState('');
  const [date, setDate] = useState(() => {
    const now = new Date();
    return now.toISOString().slice(0, 10);
  });
  const [startTime, setStartTime] = useState(() => {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(Math.ceil(now.getMinutes() / 15) * 15).padStart(2, '0');
    return `${h}:${m}`;
  });
  const [duration, setDuration] = useState('60');
  const [allDay, setAllDay] = useState(false);
  const [location, setLocation] = useState('');
  const [attendeeInput, setAttendeeInput] = useState('');
  const [attendees, setAttendees] = useState<{ email: string; displayName?: string }[]>([]);
  const [timezone, setTimezone] = useState(Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC');
  const [description, setDescription] = useState('');
  const [reminder, setReminder] = useState('15');

  const handleAddAttendee = () => {
    const email = attendeeInput.trim();
    if (!email) return;
    if (!email.includes('@')) {
      toast.error('Enter a valid email address');
      return;
    }
    if (attendees.some((a) => a.email === email)) {
      toast.error('Attendee already added');
      return;
    }
    setAttendees((prev) => [...prev, { email, displayName: email.split('@')[0] }]);
    setAttendeeInput('');
  };

  const handleRemoveAttendee = (email: string) => {
    setAttendees((prev) => prev.filter((a) => a.email !== email));
  };

  const handleSubmit = async () => {
    if (!title.trim()) {
      toast.error('Title is required');
      return;
    }

    const startDateTime = new Date(`${date}T${startTime}:00`);
    const endDateTime = allDay
      ? new Date(new Date(date).getTime() + 86400000)
      : new Date(startDateTime.getTime() + parseInt(duration, 10) * 60000);

    const payload: CalendarEventCreatePayload & Record<string, unknown> = {
      summary: title.trim(),
      start: startDateTime.toISOString(),
      end: endDateTime.toISOString(),
      timezone,
      all_day: allDay,
      location: location.trim() || undefined,
      description: description.trim() || undefined,
      attendees: attendees.length > 0 ? attendees : undefined,
      remind_before_minutes: parseInt(reminder, 10) || 15,
    };

    if (defaultEntityType && defaultEntityId) {
      payload.source_entity_type = defaultEntityType;
      payload.source_entity_id = defaultEntityId;
    }

    try {
      await createEvent.mutateAsync(payload);
      toast.success('Calendar event created!');
      onClose();
      // Reset form
      setTitle('');
      setLocation('');
      setAttendees([]);
      setDescription('');
    } catch (err: any) {
      const msg = err?.response?.data?.error || err?.message || 'Failed to create event';
      if (err?.response?.data?.requires_upgrade) {
        toast.error('Google Calendar write access required. Go to Settings → Integrations to upgrade.');
      } else {
        toast.error(msg);
      }
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Create Calendar Event"
      description="Schedule a meeting that will be synced to your Google Calendar."
      size="lg"
      footer={
        <div className="flex gap-3">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            loading={createEvent.isPending}
            icon={<Calendar className="h-4 w-4" />}
          >
            Create Event
          </Button>
        </div>
      }
    >
      <div className="space-y-5">
        {/* Title */}
        <Input
          label="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Q3 Review with Alice"
          required
        />

        {/* Date & Time */}
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            iconLeft={<Calendar className="h-4 w-4" />}
          />

          {!allDay && (
            <>
              <Input
                label="Start Time"
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                iconLeft={<Clock className="h-4 w-4" />}
              />
              <Input
                label="Duration (min)"
                type="number"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                min={5}
                step={5}
              />
            </>
          )}
        </div>

        {/* All-day toggle */}
        <label className="flex items-center gap-2.5 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={allDay}
            onChange={(e) => setAllDay(e.target.checked)}
            className="h-4 w-4 rounded border-border text-brand-600 focus:ring-brand-500 dark:border-dark-border dark:bg-dark-surface-secondary"
          />
          <span className="text-text-primary dark:text-dark-text-primary">All-day event</span>
        </label>

        {/* Timezone */}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary">
            Timezone
          </label>
          <div className="relative">
            <Sun className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-tertiary dark:text-dark-text-tertiary" />
            <select
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="w-full rounded-lg border border-border bg-white pl-10 pr-3 py-2.5 text-sm text-text-primary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary"
            >
              {TIMEZONES.map((tz) => (
                <option key={tz} value={tz}>{tz}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Location */}
        <Input
          label="Location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="Conference Room A or Google Meet link"
          iconLeft={<MapPin className="h-4 w-4" />}
        />

        {/* Attendees */}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary">
            Attendees
          </label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Users className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-tertiary dark:text-dark-text-tertiary" />
              <input
                type="email"
                value={attendeeInput}
                onChange={(e) => setAttendeeInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddAttendee();
                  }
                }}
                placeholder="alice@company.com"
                className="w-full rounded-lg border border-border bg-white pl-10 pr-3 py-2.5 text-sm text-text-primary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 placeholder:text-text-tertiary dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary"
              />
            </div>
            <Button size="sm" variant="secondary" onClick={handleAddAttendee}>
              Add
            </Button>
          </div>
          {attendees.length > 0 && (
            <div className="mt-2 space-y-1.5">
              {attendees.map((a) => (
                <div
                  key={a.email}
                  className="flex items-center gap-2 rounded-lg border border-border dark:border-dark-border px-3 py-1.5 text-sm"
                >
                  <Users className="h-3.5 w-3.5 text-text-tertiary dark:text-dark-text-tertiary shrink-0" />
                  <span className="flex-1 text-text-primary dark:text-dark-text-primary">{a.email}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveAttendee(a.email)}
                    className="text-xs text-red-500 hover:text-red-600 dark:text-red-400 dark:hover:text-red-300"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Description */}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Meeting agenda, notes, or additional details..."
            rows={3}
            className="w-full rounded-lg border border-border bg-white px-3 py-2.5 text-sm text-text-primary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 placeholder:text-text-tertiary resize-none dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary"
          />
        </div>

        {/* Reminder */}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-text-primary dark:text-dark-text-primary">
            Reminder
          </label>
          <div className="relative max-w-[200px]">
            <Bell className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-tertiary dark:text-dark-text-tertiary" />
            <select
              value={reminder}
              onChange={(e) => setReminder(e.target.value)}
              className="w-full rounded-lg border border-border bg-white pl-10 pr-3 py-2.5 text-sm text-text-primary focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-dark-border dark:bg-transparent dark:text-dark-text-primary"
            >
              <option value="0">No reminder</option>
              <option value="5">5 minutes before</option>
              <option value="15">15 minutes before</option>
              <option value="30">30 minutes before</option>
              <option value="60">1 hour before</option>
              <option value="1440">1 day before</option>
            </select>
          </div>
        </div>
      </div>
    </Modal>
  );
}