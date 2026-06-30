import type { Meta, StoryObj } from '@storybook/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppLayout } from '../../components/templates/app-layout';

/**
 * The AppLayout template provides the primary authenticated application
 * shell with the Sidebar (left panel), TopBar (header), and a main
 * content outlet. It handles auth gate, loading state, and mobile
 * responsive sidebar behaviour.
 */
const meta: Meta<typeof AppLayout> = {
  title: 'Templates/AppLayout',
  component: AppLayout,
  tags: ['autodocs'],
  decorators: [
    (Story) => {
      const queryClient = new QueryClient();
      return (
        <BrowserRouter>
          <QueryClientProvider client={queryClient}>
            <div className="h-screen">
              <Story />
            </div>
          </QueryClientProvider>
        </BrowserRouter>
      );
    },
  ],
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<typeof AppLayout>;

export const Default: Story = {
  render: () => <AppLayout />,
};