import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { AppShell } from './components/AppShell'
import { HomePage } from './pages/HomePage'
import { DiscoverPage } from './pages/DiscoverPage'
import { AuthPage } from './pages/AuthPage'
import { PublishPage } from './pages/PublishPage'
import { ContentPage } from './pages/ContentPage'
import { ProfilePage } from './pages/ProfilePage'
import { TagPage } from './pages/TagPage'
import { WorkPage } from './pages/WorkPage'
import { NotFoundPage } from './pages/NotFoundPage'

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
      <Route path="/discover" element={<DiscoverPage />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route
        path="/publish"
        element={
          <ProtectedRoute>
            <PublishPage />
          </ProtectedRoute>
        }
      />
      <Route path="/content/:contentId" element={<ContentPage />} />
      <Route path="/profile/:userId" element={<ProfilePage />} />
      <Route path="/tag/:tagName" element={<TagPage />} />
      <Route path="/work/:workId" element={<WorkPage />} />
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
