import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import type { Capabilities } from '@/lib/capabilities'
import AppLayout from '@/components/layout/AppLayout'
import OnboardingLayout from '@/components/layout/OnboardingLayout'
import LoginPage from '@/pages/LoginPage'
import InboxPage from '@/pages/InboxPage'
import ContactsPage from '@/pages/ContactsPage'
import AdminUsersPage from '@/pages/AdminUsersPage'
import AdminCompaniesPage from '@/pages/AdminCompaniesPage'
import AdminAuditLogsPage from '@/pages/AdminAuditLogsPage'
import AdminSecurityPage from '@/pages/AdminSecurityPage'
import AdminChannelsPage from '@/pages/AdminChannelsPage'
import ChatbotPage from '@/pages/ChatbotPage'
import AIProvidersPage from '@/pages/AIProvidersPage'
import TeamsPage from '@/pages/TeamsPage'
import FunnelPage from '@/pages/FunnelPage'
import FunnelKanbanPage from '@/pages/FunnelKanbanPage'
import ProfilePage from '@/pages/ProfilePage'
import HomePage from '@/pages/HomePage'
import PrivacyPolicyPage from '@/pages/PrivacyPolicyPage'
import CookieConsentBanner from '@/components/layout/CookieConsentBanner'
import PrivacyAcceptanceModal from '@/components/layout/PrivacyAcceptanceModal'
import OnboardingHomePage from '@/pages/OnboardingHomePage'

function CapabilityRoute({
  capability,
  children,
}: {
  capability: keyof Capabilities
  children: React.ReactNode
}) {
  const hasCapability = useAuthStore((s) => s.hasCapability(capability))
  if (!hasCapability) return <Navigate to="/" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <>
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/privacy" element={<PrivacyPolicyPage />} />
      <Route path="/setup-2fa" element={<Navigate to="/profile" replace />} />

      <Route element={<OnboardingLayout />}>
        <Route path="/onboarding" element={<OnboardingHomePage />} />
      </Route>

      <Route element={<AppLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route
          path="/inbox"
          element={
            <CapabilityRoute capability="access_inbox">
              <InboxPage />
            </CapabilityRoute>
          }
        />
        <Route path="/profile" element={<ProfilePage />} />
        <Route
          path="/contacts"
          element={
            <CapabilityRoute capability="view_contacts">
              <ContactsPage />
            </CapabilityRoute>
          }
        />
        <Route
          path="/admin/companies"
          element={
            <CapabilityRoute capability="manage_companies">
              <AdminCompaniesPage />
            </CapabilityRoute>
          }
        />
        <Route
          path="/admin/security"
          element={
            <CapabilityRoute capability="view_security">
              <AdminSecurityPage />
            </CapabilityRoute>
          }
        />
        <Route
          path="/admin/audit-logs"
          element={
            <CapabilityRoute capability="view_audit">
              <AdminAuditLogsPage />
            </CapabilityRoute>
          }
        />
        <Route
          path="/admin/users"
          element={
            <CapabilityRoute capability="manage_users">
              <AdminUsersPage />
            </CapabilityRoute>
          }
        />
        <Route
          path="/admin/chatbot"
          element={
            <CapabilityRoute capability="manage_automation">
              <ChatbotPage />
            </CapabilityRoute>
          }
        />
        <Route
          path="/admin/teams"
          element={
            <CapabilityRoute capability="manage_teams">
              <TeamsPage />
            </CapabilityRoute>
          }
        />
        <Route
          path="/admin/ai"
          element={
            <CapabilityRoute capability="use_ai">
              <AIProvidersPage />
            </CapabilityRoute>
          }
        />
        <Route path="/admin/deepseek" element={<Navigate to="/admin/ai" replace />} />
        <Route
          path="/funnel"
          element={
            <CapabilityRoute capability="access_inbox">
              <FunnelKanbanPage />
            </CapabilityRoute>
          }
        />
        <Route
          path="/admin/funnel"
          element={
            <CapabilityRoute capability="manage_teams">
              <FunnelPage />
            </CapabilityRoute>
          }
        />
        <Route
          path="/admin/channels"
          element={
            <CapabilityRoute capability="manage_channels">
              <AdminChannelsPage />
            </CapabilityRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    <CookieConsentBanner />
    <PrivacyAcceptanceModal />
    </>
  )
}
