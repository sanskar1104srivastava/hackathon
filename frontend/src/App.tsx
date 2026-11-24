import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { DashboardPage } from './features/dashboard/DashboardPage'
import { ReferralDetailPage } from './features/doctor/ReferralDetailPage'
import { ReferralInboxPage } from './features/doctor/ReferralInboxPage'
import { AlertsPage } from './features/field/AlertsPage'
import { ChildDetailPage } from './features/field/ChildDetailPage'
import { ChildListPage } from './features/field/ChildListPage'
import { RegisterChildPage } from './features/field/RegisterChildPage'
import { ScreeningPage } from './features/field/screening/ScreeningPage'
import { RolePickerPage } from './features/home/RolePickerPage'
import { ParentPage } from './features/parent/ParentPage'

const router = createBrowserRouter([
  {
    element: <AppShell />,
    children: [
      { path: '/', element: <RolePickerPage /> },
      { path: '/field', element: <ChildListPage /> },
      { path: '/field/register', element: <RegisterChildPage /> },
      { path: '/field/alerts', element: <AlertsPage /> },
      { path: '/field/children/:childId', element: <ChildDetailPage /> },
      { path: '/field/children/:childId/screen', element: <ScreeningPage /> },
      { path: '/doctor', element: <ReferralInboxPage /> },
      { path: '/doctor/children/:childId/referrals/:referralId', element: <ReferralDetailPage /> },
      { path: '/dashboard', element: <DashboardPage /> },
      { path: '/parent/:childId', element: <ParentPage /> },
    ],
  },
])

export function App() {
  return <RouterProvider router={router} />
}
