import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout, AuthLayout } from '../components/layout/app-layout';
import { LoginPage, SignupPage, MagicLinkPage } from '../pages/auth';
import { DashboardPage } from '../pages/dashboard';
import { ReportsPage } from '../pages/reports';
import { ContactListPage } from '../pages/contacts/contact-list';
import { ContactDetailPage } from '../pages/contacts/contact-detail';
import { PipelinePage } from '../pages/pipeline/pipeline-page';
import { ActivityPage } from '../pages/activities/activity-page';
import { EmailPage } from '../pages/email/email-page';
import { SettingsPage } from '../pages/settings/settings-page';
import { OnboardingPage } from '../pages/onboarding';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AuthLayout />,
    children: [
      { index: true, element: <Navigate to="/login" replace /> },
      { path: 'login', element: <LoginPage /> },
      { path: 'signup', element: <SignupPage /> },
      { path: 'magic-link', element: <MagicLinkPage /> },
      { path: 'auth/callback', element: <MagicLinkPage /> },
    ],
  },
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'reports', element: <ReportsPage /> },
      { path: 'contacts', element: <ContactListPage /> },
      { path: 'contacts/:id', element: <ContactDetailPage /> },
      { path: 'pipeline', element: <PipelinePage /> },
      { path: 'activities', element: <ActivityPage /> },
      { path: 'email', element: <EmailPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: 'onboarding', element: <OnboardingPage /> },
    ],
  },
]);