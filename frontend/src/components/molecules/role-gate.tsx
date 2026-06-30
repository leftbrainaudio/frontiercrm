import type { ReactNode } from 'react';
import { useRole } from '../../hooks/useRole';

interface RoleGateProps {
  permission?: string;
  anyPermission?: string[];
  allPermissions?: string[];
  fallback?: ReactNode;
  children: ReactNode;
}

export function RoleGate({
  permission,
  anyPermission,
  allPermissions,
  fallback = null,
  children,
}: RoleGateProps) {
  const { hasPermission, hasAnyPermission, hasAllPermissions } = useRole();

  let allowed = false;

  if (permission) {
    allowed = hasPermission(permission);
  } else if (anyPermission) {
    allowed = hasAnyPermission(anyPermission);
  } else if (allPermissions) {
    allowed = hasAllPermissions(allPermissions);
  } else {
    allowed = true;
  }

  return <>{allowed ? children : fallback}</>;
}