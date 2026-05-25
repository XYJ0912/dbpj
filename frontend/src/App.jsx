import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { AppShell } from './components/AppShell'
import { HomePage } from './pages/HomePage'
import { AuthPage } from './pages/AuthPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { WorkspaceOverviewPage } from './pages/WorkspaceOverviewPage'
import { AssetsPage } from './pages/AssetsPage'
import { WorksPage } from './pages/WorksPage'
import { WorkEditorPage } from './pages/WorkEditorPage'
import { PublishCenterPage } from './pages/PublishCenterPage'
import { ProfileSettingsPage } from './pages/ProfileSettingsPage'

function ProtectedRoute({ children }) {
  const { user, bootstrapped } = useAuth()
  if (!bootstrapped) {
    return <div className="screen-state">Loading session...</div>
  }
  if (!user) {
    return <Navigate to="/auth" replace />
  }
  return children
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route
        path="/publish"
        element={
          <ProtectedRoute>
            <PublishCenterPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfileSettingsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workspace"
        element={
          <ProtectedRoute>
            <WorkspaceOverviewPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/assets"
        element={
          <ProtectedRoute>
            <AssetsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/works"
        element={
          <ProtectedRoute>
            <WorksPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/works/:workId"
        element={
          <ProtectedRoute>
            <WorkEditorPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell>
        <AppRoutes />
      </AppShell>
    </AuthProvider>
  )
}
