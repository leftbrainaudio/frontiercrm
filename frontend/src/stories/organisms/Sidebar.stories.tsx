import type { Meta, StoryObj } from '@storybook/react';
import { Sidebar } from '../../components/organisms/sidebar';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

const meta: Meta<typeof Sidebar> = {
  title: 'Organisms/Sidebar',
  component: Sidebar,
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <div className="h-screen flex">
            <Story />
          </div>
        </QueryClientProvider>
      </BrowserRouter>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof Sidebar>;

export const Expanded: Story = {
  args: {
    collapsed: false,
    mobileOpen: false,
    onToggle: () => {},
    onMobileClose: () => {},
  },
};

export const Collapsed: Story = {
  args: {
    collapsed: true,
    mobileOpen: false,
    onToggle: () => {},
    onMobileClose: () => {},
  },
};