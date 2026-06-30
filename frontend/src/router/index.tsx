import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout, AuthLayout } from '../components/templates/app-layout';
import { LoginPage, SignupPage, MagicLinkPage, SocialCallbackPage, SamlCallbackPage } from '../pages/auth';
import { DashboardPage } from '../pages/dashboard';
import { ReportsPage } from '../pages/reports';
import { ForecastPage } from '../pages/forecast';
import { ContactListPage } from '../pages/contacts/contact-list';
import { ContactDetailPage } from '../pages/contacts/contact-detail';
import { PipelinePage } from '../pages/pipeline/pipeline-page';
import { TimelinePage } from '../pages/activities';
import { EmailPage } from '../pages/email/email-page';
import { EmailTemplatesPage } from '../pages/email/templates';
import { SettingsPage } from '../pages/settings/settings-page';
import { SlackSettingsPage } from '../pages/settings/slack-page';
import CustomFieldsSettingsPage from '../pages/settings/custom-fields-page';
import UsersPage from '../pages/settings/users-page';
import AuditLogPage from '../pages/settings/audit-log-page';
import { OnboardingWizard, OnboardingLayout } from '../pages/onboarding';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AuthLayout />,
    children: [
      { index: true, element: <Navigate to="/login" replace /> },
      { path: 'login', element: <LoginPage /> },
      { path: 'signup', element: <SignupPage /> },
      { path: 'magic-link', element: <MagicLinkPage /> },
      { path: 'auth/callback', element: <SocialCallbackPage /> },
      { path: 'auth/saml/callback', element: <SamlCallbackPage /> },
    ],
  },
  // — Onboarding route (no sidebar, no topbar) —
  {
    path: '/onboarding',
    element: <OnboardingLayout />,
    children: [
      { index: true, element: <OnboardingWizard /> },
    ],
  },
  // — App routes (with sidebar) —
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'reports', element: <ReportsPage /> },
      { path: 'forecast', element: <ForecastPage /> },
      { path: 'contacts', element: <ContactListPage /> },
      { path: 'contacts/:id', element: <ContactDetailPage /> },
      { path: 'pipeline', element: <PipelinePage /> },
      { path: 'activities', element: <TimelinePage /> },
      { path: 'timeline', element: <TimelinePage /> },
      { path: 'email', element: <EmailPage /> },
      { path: 'email/templates', element: <EmailTemplatesPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: 'settings/users', element: <UsersPage /> },
      { path: 'settings/integrations/slack', element: <SlackSettingsPage /> },
      { path: 'settings/custom-fields', element: <CustomFieldsSettingsPage /> },
      { path: 'settings/audit-log', element: <AuditLogPage /> },
    ],
  },
]);