import type { Meta, StoryObj } from '@storybook/react';
import { Table } from '../../components/ui/table';
import { Badge } from '../../components/atoms/badge';

type Contact = {
  name: string;
  email: string;
  role: string;
  status: string;
};

const columns = [
  { header: 'Name', accessor: 'name' as const, sortable: true },
  { header: 'Email', accessor: 'email' as const, sortable: true },
  { header: 'Role', accessor: 'role' as const },
  {
    header: 'Status',
    accessor: 'status' as const,
    cell: (row: Contact) => (
      <Badge variant={row.status === 'Active' ? 'success' : 'neutral'}>{row.status}</Badge>
    ),
  },
];

const data: Contact[] = [
  { name: 'Alice Johnson', email: 'alice@example.com', role: 'Admin', status: 'Active' },
  { name: 'Bob Smith', email: 'bob@example.com', role: 'Editor', status: 'Active' },
  { name: 'Carol White', email: 'carol@example.com', role: 'Viewer', status: 'Inactive' },
  { name: 'Dan Brown', email: 'dan@example.com', role: 'Editor', status: 'Active' },
  { name: 'Eva Green', email: 'eva@example.com', role: 'Admin', status: 'Active' },
];

const meta: Meta<typeof Table> = {
  title: 'Molecules/Table',
  component: Table,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Table<Contact>>;

export const Default: Story = {
  render: () => <Table columns={columns} data={data} />,
};

export const Sortable: Story = {
  render: () => <Table columns={columns} data={data} rowKey={(r) => r.email} />,
};

export const Loading: Story = {
  render: () => <Table columns={columns} data={[]} loading skeletonRows={4} />,
};

export const Empty: Story = {
  render: () => (
    <Table
      columns={columns}
      data={[]}
      emptyContent={<div className="text-gray-500 py-4">No contacts found</div>}
    />
  ),
};

export const Striped: Story = {
  render: () => <Table columns={columns} data={data} striped rowKey={(r) => r.email} />,
};

export const Bordered: Story = {
  render: () => <Table columns={columns} data={data} bordered rowKey={(r) => r.email} />,
};

export const ClickableRows: Story = {
  render: () => (
    <Table
      columns={columns}
      data={data}
      onRowClick={(row) => alert(`Clicked: ${row.name}`)}
      rowKey={(r) => r.email}
    />
  ),
};

export const Selectable: Story = {
  render: () => {
    const selectedKeys = new Set<string>(['alice@example.com']);
    return (
      <Table
        columns={columns}
        data={data}
        selectable
        selectedKeys={selectedKeys}
        onSelectionChange={(keys) => console.log('Selected:', keys)}
        rowKey={(r) => r.email}
      />
    );
  },
};