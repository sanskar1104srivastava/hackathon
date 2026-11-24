import { Link } from 'react-router-dom'
import { api } from '../../api/endpoints'
import { ErrorMessage, Loading } from '../../components/StatusViews'
import { useAsync } from '../../hooks/useAsync'
import { formatDate } from '../../lib/dates'
import { preferences } from '../../lib/preferences'
import { text } from '../../i18n/hi'

/** The ASHA's task list: re-checks, referrals not reached, and parents asking for a call back (UC-6). */
export function AlertsPage() {
  const districtCode = preferences.getArea()?.districtCode
  const alerts = useAsync(
    () => (districtCode ? api.listAlerts(districtCode) : Promise.resolve([])),
    [districtCode],
  )

  async function close(childId: string, alertId: string) {
    await api.closeAlert(childId, alertId)
    alerts.reload()
  }

  return (
    <div className="stack">
      <h1>{text.alerts.title}</h1>
      {alerts.loading && <Loading />}
      {alerts.error && <ErrorMessage error={alerts.error} onRetry={alerts.reload} />}
      {alerts.data?.length === 0 && <p className="muted">{text.alerts.empty}</p>}
      {alerts.data?.map((alert) => (
        <section key={alert.alertId} className="card card-yellow">
          <header className="row between">
            <strong>{text.alerts.kinds[alert.kind]}</strong>
            <span className="muted">{formatDate(alert.createdAt)}</span>
          </header>
          <p>{alert.messageHi}</p>
          <p className="muted">
            {alert.blockName} ·{' '}
            <a href={`tel:${alert.guardianPhone}`} className="link">
              📞 {alert.guardianPhone}
            </a>
          </p>
          <div className="row wrap">
            <Link
              to={`/field/children/${alert.childId}`}
              className="button button-secondary button-small"
            >
              {alert.childName}
            </Link>
            <button
              type="button"
              className="button button-ghost button-small"
              onClick={() => void close(alert.childId, alert.alertId)}
            >
              ✓ {text.alerts.close}
            </button>
          </div>
        </section>
      ))}
    </div>
  )
}
