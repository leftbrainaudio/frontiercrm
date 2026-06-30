import type { Meta, StoryObj } from '@storybook/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TopBar } from '../../components/organisms/topbar';

const queryClient = new QueryClient();

const meta: Meta<typeof TopBar> = {
  title: 'Organisms/TopBar',
  component: TopBar,
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <Story />
        </QueryClientProvider>
      </BrowserRouter>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof TopBar>;

export const Default: Story = {
  args: {
    onMenuClick: () => {},
  },
};