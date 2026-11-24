import { useEffect, useState } from 'react'
import { Link, Outlet } from 'react-router-dom'
import { text } from '../i18n/hi'
import { subscribeToQueue } from '../offline/syncQueue'

function useOnline(): boolean {
  const [online, setOnline] = useState(navigator.onLine)
  useEffect(() => {
    const update = () => setOnline(navigator.onLine)
    window.addEventListener('online', update)
    window.addEventListener('offline', update)
    return () => {
      window.removeEventListener('online', update)
      window.removeEventListener('offline', update)
    }
  }, [])
  return online
}

export function AppShell() {
  const online = useOnline()
  const [pending, setPending] = useState(0)
  useEffect(() => subscribeToQueue(setPending), [])

  return (
    <div className="shell">
      <header className="topbar">
        <Link to="/" className="brand">
          {text.appTitle}
        </Link>
        <div className="row">
          {pending > 0 && <span className="pill pill-warn">{text.pendingSync(pending)}</span>}
          {!online && <span className="pill pill-offline">{text.offline}</span>}
        </div>
      </header>
      <main className="page">
        <Outlet />
      </main>
    </div>
  )
}
