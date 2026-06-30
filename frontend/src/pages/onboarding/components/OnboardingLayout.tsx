import { Outlet } from 'react-router-dom';

export function OnboardingLayout() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 flex flex-col">
      <Outlet />
    </div>
  );
}
