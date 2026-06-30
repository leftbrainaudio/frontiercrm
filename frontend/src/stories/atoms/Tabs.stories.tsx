import type { Meta, StoryObj } from '@storybook/react';
import { Tabs } from '../../components/ui/tabs';
import { Mail, Settings, Bell } from 'lucide-react';

const meta: Meta<typeof Tabs> = {
  title: 'Atoms/Tabs',
  component: Tabs,
  tags: ['autodocs'],
  argTypes: {
    orientation: { control: 'select', options: ['horizontal', 'vertical'] },
  },
};

export default meta;
type Story = StoryObj<typeof Tabs>;

export const Default: Story = {
  args: {
    tabs: [
      { id: 'tab1', label: 'Tab 1' },
      { id: 'tab2', label: 'Tab 2' },
      { id: 'tab3', label: 'Tab 3' },
    ],
    children: (activeIndex) => (
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Content for tab {activeIndex + 1}
      </div>
    ),
  },
};

export const WithBadges: Story = {
  args: {
    tabs: [
      { id: 'inbox', label: 'Inbox', badge: 12 },
      { id: 'sent', label: 'Sent' },
      { id: 'spam', label: 'Spam', badge: 3 },
    ],
    children: (activeIndex) => (
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Tab {activeIndex + 1} content
      </div>
    ),
  },
};

export const WithIcons: Story = {
  args: {
    tabs: [
      { id: 'mail', label: 'Mail', icon: <Mail className="h-4 w-4" /> },
      { id: 'settings', label: 'Settings', icon: <Settings className="h-4 w-4" /> },
      { id: 'notifications', label: 'Notifications', icon: <Bell className="h-4 w-4" /> },
    ],
    children: (activeIndex) => (
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Content for {['Mail', 'Settings', 'Notifications'][activeIndex]}
      </div>
    ),
  },
};

export const Vertical: Story = {
  args: {
    orientation: 'vertical',
    tabs: [
      { id: 'profile', label: 'Profile' },
      { id: 'account', label: 'Account' },
      { id: 'security', label: 'Security' },
    ],
    children: (activeIndex) => (
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Settings content for tab {activeIndex + 1}
      </div>
    ),
  },
};

export const DisabledTab: Story = {
  args: {
    tabs: [
      { id: 'a', label: 'Active' },
      { id: 'b', label: 'Disabled', disabled: true },
      { id: 'c', label: 'Tab 3' },
    ],
    children: (activeIndex) => (
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Content {activeIndex + 1}
      </div>
    ),
  },
};