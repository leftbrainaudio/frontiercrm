import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';

// ── Shared mock state ────────────────────────────────────────────────────

let mockMembership: Record<string, any> | null = null;

vi.mock('../../store/auth', () => ({
  useAuthStore: vi.fn((sel?: unknown) => {
    const state = { membership: mockMembership, user: null, tokens: null, isAuthenticated: false, isLoading: false };
    return typeof sel === 'function' ? sel(state) : state;
  }),
}));

import { useRole } from '../../hooks/useRole';

describe('useRole', () => {
  beforeEach(() => {
    mockMembership = null;
  });

  it('returns roleName from membership', () => {
    mockMembership = { role_name: 'Admin', is_admin: true, is_owner: true, permissions: {} };
    const { result } = renderHook(() => useRole());
    expect(result.current.roleName).toBe('Admin');
  });

  it('returns isAdmin true when membership is_admin is true', () => {
    mockMembership = { role_name: 'Admin', is_admin: true, is_owner: false, permissions: {} };
    const { result } = renderHook(() => useRole());
    expect(result.current.isAdmin).toBe(true);
  });

  it('returns isOwner true when membership is_owner is true', () => {
    mockMembership = { role_name: 'Admin', is_admin: true, is_owner: true, permissions: {} };
    const { result } = renderHook(() => useRole());
    expect(result.current.isOwner).toBe(true);
  });

  it('returns null roleName when no membership', () => {
    mockMembership = null;
    const { result } = renderHook(() => useRole());
    expect(result.current.roleName).toBeNull();
    expect(result.current.isAdmin).toBe(false);
    expect(result.current.isOwner).toBe(false);
    expect(result.current.permissions).toEqual({});
  });

  it('returns empty permissions when membership has none', () => {
    mockMembership = { role_name: null, is_admin: false, is_owner: false, permissions: undefined };
    const { result } = renderHook(() => useRole());
    expect(result.current.permissions).toEqual({});
  });

  it('hasPermission returns true for a key the user has', () => {
    mockMembership = {
      role_name: 'Viewer', is_admin: false, is_owner: false,
      permissions: { 'contacts.view': true, 'deals.view': true },
    };
    const { result } = renderHook(() => useRole());
    expect(result.current.hasPermission('contacts.view')).toBe(true);
    expect(result.current.hasPermission('deals.view')).toBe(true);
  });

  it('hasPermission returns false for a key the user lacks', () => {
    mockMembership = {
      role_name: 'Viewer', is_admin: false, is_owner: false,
      permissions: { 'contacts.view': true },
    };
    const { result } = renderHook(() => useRole());
    expect(result.current.hasPermission('deals.create')).toBe(false);
    expect(result.current.hasPermission('contacts.edit')).toBe(false);
  });

  it('hasPermission returns true for any key when user is admin', () => {
    mockMembership = {
      role_name: 'Admin', is_admin: true, is_owner: true, permissions: {},
    };
    const { result } = renderHook(() => useRole());
    expect(result.current.hasPermission('contacts.delete')).toBe(true);
    expect(result.current.hasPermission('team.manage_roles')).toBe(true);
    expect(result.current.hasPermission('nonexistent')).toBe(true);
  });

  it('hasAnyPermission returns true when user has at least one of the keys', () => {
    mockMembership = {
      role_name: 'Viewer', is_admin: false, is_owner: false,
      permissions: { 'contacts.view': true },
    };
    const { result } = renderHook(() => useRole());
    expect(result.current.hasAnyPermission(['contacts.view', 'deals.create'])).toBe(true);
    expect(result.current.hasAnyPermission(['deals.create', 'deals.edit'])).toBe(false);
  });

  it('hasAnyPermission returns true for admin even with empty keys', () => {
    mockMembership = {
      role_name: 'Admin', is_admin: true, is_owner: true, permissions: {},
    };
    const { result } = renderHook(() => useRole());
    expect(result.current.hasAnyPermission([])).toBe(true);
  });

  it('hasAllPermissions returns true when user has all the keys', () => {
    mockMembership = {
      role_name: 'Sales Rep', is_admin: false, is_owner: false,
      permissions: { 'deals.view': true, 'deals.create': true, 'deals.edit': true },
    };
    const { result } = renderHook(() => useRole());
    expect(result.current.hasAllPermissions(['deals.view', 'deals.create'])).toBe(true);
    expect(result.current.hasAllPermissions(['deals.view', 'deals.delete'])).toBe(false);
  });

  it('hasAllPermissions returns true for admin even without explicit permissions', () => {
    mockMembership = {
      role_name: 'Admin', is_admin: true, is_owner: true, permissions: {},
    };
    const { result } = renderHook(() => useRole());
    expect(result.current.hasAllPermissions(['contacts.delete', 'team.manage_roles', 'audit.log'])).toBe(true);
  });

  it('permissions object is stable via useMemo (same reference between renders)', () => {
    mockMembership = {
      role_name: 'Viewer', is_admin: false, is_owner: false,
      permissions: { 'contacts.view': true },
    };
    const { result, rerender } = renderHook(() => useRole());
    const firstPerms = result.current.permissions;
    rerender();
    expect(result.current.permissions).toBe(firstPerms);
  });

  it('hasPermission is stable via useMemo', () => {
    mockMembership = {
      role_name: 'Viewer', is_admin: false, is_owner: false,
      permissions: { 'contacts.view': true },
    };
    const { result, rerender } = renderHook(() => useRole());
    const firstFn = result.current.hasPermission;
    rerender();
    expect(result.current.hasPermission).toBe(firstFn);
  });
});
