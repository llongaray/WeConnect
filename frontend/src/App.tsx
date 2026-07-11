import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import AppLayout from '@/components/layout/AppLayout'
import LoginPage from '@/pages/LoginPage'
import InboxPage from '@/pages/InboxPage'
import ContactsPage from '@/pages/ContactsPage'
import AdminUsersPage from '@/pages/AdminUsersPage'
import AdminChannelsPage from '@/pages/AdminChannelsPage'
import ChatbotPage from '@/pages/ChatbotPage'
import DeepSeekPage from '@/pages/DeepSeekPage'
import TeamsPage from '@/pages/TeamsPage'

function AdminRoute({ children }: { children: React.ReactNode }) {
  const isAdmin = useAuthStore((s) => s.isAdmin())
  if (!isAdmin) return <Navigate to="/" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<AppLayout />}>
        <Route path="/" element={<InboxPage />} />
        <Route path="/contacts" element={<ContactsPage />} />
        <Route
          path="/admin/users"
          element={
            <AdminRoute>
              <AdminUsersPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/chatbot"
          element={
            <AdminRoute>
              <ChatbotPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/teams"
          element={
            <AdminRoute>
              <TeamsPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/deepseek"
          element={
            <AdminRoute>
              <DeepSeekPage />
            </AdminRoute>
          }
        />
        <Route
          path="/admin/channels"
          element={
            <AdminRoute>
              <AdminChannelsPage />
            </AdminRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
