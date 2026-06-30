import { useMemo } from 'react';
import { useAuthStore } from '../store/auth';

interface RoleInfo {
  roleName: string | null;
  isAdmin: boolean;
  isOwner: boolean;
  permissions: Record<string, boolean>;
  hasPermission: (key: string) => boolean;
  hasAnyPermission: (keys: string[]) => boolean;
  hasAllPermissions: (keys: string[]) => boolean;
}

export function useRole(): RoleInfo {
  const membership = useAuthStore((s) => s.membership);

  return useMemo(() => {
    const perms = membership?.permissions ?? {};
    const isAdmin = membership?.is_admin ?? false;

    return {
      roleName: membership?.role_name ?? null,
      isAdmin,
      isOwner: membership?.is_owner ?? false,
      permissions: perms,
      hasPermission: (key: string) =>
        isAdmin ? true : !!perms[key],
      hasAnyPermission: (keys: string[]) =>
        keys.some((k) => perms[k] === true) || isAdmin,
      hasAllPermissions: (keys: string[]) =>
        keys.every((k) => perms[k] === true) || isAdmin,
    };
  }, [membership]);
}