import type { Meta, StoryObj } from '@storybook/react';
import { Pagination } from '../../components/ui/pagination';

const meta: Meta<typeof Pagination> = {
  title: 'Atoms/Pagination',
  component: Pagination,
  tags: ['autodocs'],
  argTypes: {
    pageCount: { control: { type: 'number', min: 1, max: 50 } },
    currentPage: { control: { type: 'number', min: 1 } },
    compact: { control: 'boolean' },
    showLabels: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof Pagination>;

export const Default: Story = {
  args: {
    pageCount: 10,
    currentPage: 3,
    onChange: (page) => console.log('Page:', page),
  },
};

export const ManyPages: Story = {
  args: {
    pageCount: 25,
    currentPage: 12,
    onChange: (page) => console.log('Page:', page),
  },
};

export const FirstPage: Story = {
  args: {
    pageCount: 8,
    currentPage: 1,
    onChange: (page) => console.log('Page:', page),
  },
};

export const LastPage: Story = {
  args: {
    pageCount: 8,
    currentPage: 8,
    onChange: (page) => console.log('Page:', page),
  },
};

export const Compact: Story = {
  args: {
    pageCount: 20,
    currentPage: 10,
    compact: true,
    onChange: (page) => console.log('Page:', page),
  },
};

export const WithLabels: Story = {
  args: {
    pageCount: 6,
    currentPage: 3,
    showLabels: true,
    onChange: (page) => console.log('Page:', page),
  },
};