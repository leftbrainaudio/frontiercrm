import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

// ── Shared mock state for useAuthStore ────────────────────────────────────

let mockMembership: Record<string, any> | null = null;

vi.mock('../../store/auth', () => ({
  useAuthStore: vi.fn((sel?: unknown) => {
    const state = { membership: mockMembership };
    return typeof sel === 'function' ? sel(state) : state;
  }),
}));

import { RoleGate } from '../../components/molecules/role-gate';

describe('RoleGate', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockMembership = null;
  });

  it('renders children when no permission props are given (allowed = true)', () => {
    mockMembership = { is_admin: false, permissions: {} };
    render(
      <RoleGate>
        <div data-testid="content">Visible</div>
      </RoleGate>,
    );
    expect(screen.getByTestId('content')).toBeInTheDocument();
  });

  it('renders children when user has the required single permission', () => {
    mockMembership = {
      is_admin: false, role_name: 'Viewer',
      permissions: { 'contacts.view': true },
    };
    render(
      <RoleGate permission="contacts.view">
        <div data-testid="content">Visible</div>
      </RoleGate>,
    );
    expect(screen.getByTestId('content')).toBeInTheDocument();
  });

  it('renders fallback when user lacks the required single permission', () => {
    mockMembership = {
      is_admin: false, role_name: 'Viewer',
      permissions: { 'contacts.view': true },
    };
    render(
      <RoleGate permission="contacts.delete" fallback={<div data-testid="fallback">Denied</div>}>
        <div data-testid="content">Visible</div>
      </RoleGate>,
    );
    expect(screen.queryByTestId('content')).not.toBeInTheDocument();
    expect(screen.getByTestId('fallback')).toBeInTheDocument();
  });

  it('renders children when user has any of the anyPermission array', () => {
    mockMembership = {
      is_admin: false, role_name: 'Sales Rep',
      permissions: { 'deals.create': true },
    };
    render(
      <RoleGate anyPermission={['deals.create', 'deals.edit']}>
        <div data-testid="content">Visible</div>
      </RoleGate>,
    );
    expect(screen.getByTestId('content')).toBeInTheDocument();
  });

  it('renders fallback when user has none of the anyPermission array', () => {
    mockMembership = {
      is_admin: false, role_name: 'Viewer',
      permissions: { 'contacts.view': true },
    };
    render(
      <RoleGate anyPermission={['deals.create', 'deals.edit']} fallback={<div data-testid="fallback">Denied</div>}>
        <div data-testid="content">Visible</div>
      </RoleGate>,
    );
    expect(screen.queryByTestId('content')).not.toBeInTheDocument();
    expect(screen.getByTestId('fallback')).toBeInTheDocument();
  });

  it('renders children when user has all of the allPermissions array', () => {
    mockMembership = {
      is_admin: false, role_name: 'Sales Rep',
      permissions: { 'deals.view': true, 'deals.create': true, 'deals.edit': true },
    };
    render(
      <RoleGate allPermissions={['deals.view', 'deals.create']}>
        <div data-testid="content">Visible</div>
      </RoleGate>,
    );
    expect(screen.getByTestId('content')).toBeInTheDocument();
  });

  it('renders fallback when user lacks any of the allPermissions array', () => {
    mockMembership = {
      is_admin: false, role_name: 'Viewer',
      permissions: { 'contacts.view': true },
    };
    render(
      <RoleGate allPermissions={['contacts.view', 'deals.view']} fallback={<div data-testid="fallback">Denied</div>}>
        <div data-testid="content">Visible</div>
      </RoleGate>,
    );
    expect(screen.queryByTestId('content')).not.toBeInTheDocument();
    expect(screen.getByTestId('fallback')).toBeInTheDocument();
  });

  it('admin short-circuit: renders children even without explicit permissions', () => {
    mockMembership = {
      is_admin: true, role_name: 'Admin', permissions: {},
    };
    render(
      <RoleGate permission="contacts.delete">
        <div data-testid="content">Admin Always Sees</div>
      </RoleGate>,
    );
    expect(screen.getByTestId('content')).toBeInTheDocument();
  });

  it('admin short-circuit works with anyPermission', () => {
    mockMembership = {
      is_admin: true, role_name: 'Admin', permissions: {},
    };
    render(
      <RoleGate anyPermission={['nonexistent.one', 'nonexistent.two']}>
        <div data-testid="content">Admin Always Sees</div>
      </RoleGate>,
    );
    expect(screen.getByTestId('content')).toBeInTheDocument();
  });

  it('admin short-circuit works with allPermissions', () => {
    mockMembership = {
      is_admin: true, role_name: 'Admin', permissions: {},
    };
    render(
      <RoleGate allPermissions={['nonexistent.one', 'nonexistent.two']}>
        <div data-testid="content">Admin Always Sees</div>
      </RoleGate>,
    );
    expect(screen.getByTestId('content')).toBeInTheDocument();
  });

  it('default fallback is null (renders nothing) when permission denied', () => {
    mockMembership = {
      is_admin: false, role_name: 'Viewer',
      permissions: { 'contacts.view': true },
    };
    const { container } = render(
      <RoleGate permission="deals.create">
        <div data-testid="content">Secret</div>
      </RoleGate>,
    );
    expect(screen.queryByTestId('content')).not.toBeInTheDocument();
    expect(container.innerHTML).toBe('');
  });

  it('prefers permission over anyPermission over allPermissions (first match wins)', () => {
    mockMembership = {
      is_admin: false, role_name: 'Viewer',
      permissions: { 'contacts.view': true },
    };
    // permission is set, anyPermission and allPermissions are ignored
    render(
      <RoleGate permission="contacts.view" anyPermission={['deals.create']}>
        <div data-testid="content">Uses permission prop</div>
      </RoleGate>,
    );
    expect(screen.getByTestId('content')).toBeInTheDocument();
  });

  it('prefers anyPermission over allPermissions when permission is unset', () => {
    mockMembership = {
      is_admin: false, role_name: 'Viewer',
      permissions: { 'contacts.view': true },
    };
    // anyPermission is checked before allPermissions
    render(
      <RoleGate anyPermission={['contacts.view']} allPermissions={['contacts.view', 'nonexistent']}>
        <div data-testid="content">Uses anyPermission</div>
      </RoleGate>,
    );
    expect(screen.getByTestId('content')).toBeInTheDocument();
  });
});
