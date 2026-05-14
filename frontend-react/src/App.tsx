import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { Toaster } from 'sonner'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/Layout/AppLayout'
import Login from '@/pages/Login'
import Dashboard from '@/pages/Dashboard'
import Analysis from '@/pages/Analysis'
import Reports from '@/pages/Reports'
import ReportDetail from '@/pages/ReportDetail'
import Tasks from '@/pages/Tasks'
import Favorites from '@/pages/Favorites'
import WatchlistSchedule from '@/pages/WatchlistSchedule'
import Settings from '@/pages/Settings'
import About from '@/pages/About'

function ProtectedRoute() {
  // TODO: reconnect auth after backend is ready
  return <Outlet />
  // const { isAuthenticated } = useAuthStore()
  // if (!isAuthenticated) return <Navigate to="/login" replace />
  // return <Outlet />
}

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/login" element={<Login />} />

        {/* Protected layout with sidebar/header */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="analysis" element={<Analysis />} />
            <Route path="reports" element={<Reports />} />
            <Route path="reports/:id" element={<ReportDetail />} />
            <Route path="tasks" element={<Tasks />} />
            <Route path="favorites" element={<Favorites />} />
            <Route path="watchlist-schedule" element={<WatchlistSchedule />} />
            <Route path="settings" element={<Settings />} />
            <Route path="about" element={<About />} />
          </Route>
        </Route>
      </Routes>

      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: 'rgba(17, 25, 39, 0.95)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: '#fff',
          },
        }}
      />
    </>
  )
}
