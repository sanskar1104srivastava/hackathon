import { useState } from 'react'
import { api } from '../../api/endpoints'
import { COUNTER_KEYS, type CounterKey, type DashboardRow } from '../../api/types'
import { ErrorMessage, Loading } from '../../components/StatusViews'
import { useAsync } from '../../hooks/useAsync'
import { text } from '../../i18n/hi'

const TABLE_COLUMNS: CounterKey[] = [
  'screened',
  'flaggedDefects',
  'flaggedDeficiencies',
  'flaggedDiseases',
  'flaggedDevelopment',
  'referred',
  'reached',
  'improving',
  'alerts',
]

const percent = (part: number, whole: number) => (whole ? Math.round((100 * part) / whole) : 0)

/** UC-8: counts by district, or by block inside one district. No names or phone numbers reach this page. */
export function DashboardPage() {
  const [district, setDistrict] = useState<{ code: number; name: string } | null>(null)
  const summary = useAsync(() => api.getDashboard(district?.code), [district?.code])
  const [skipping, setSkipping] = useState(false)

  async function skipWeek() {
    setSkipping(true)
    try {
      await api.skipWeek()
      summary.reload()
    } finally {
      setSkipping(false)
    }
  }

  const totals = summary.data?.totals
  return (
    <div className="stack">
      <div>
        <h1>{text.dashboard.title}</h1>
        <p className="muted">{text.dashboard.subtitle}</p>
      </div>
      <div className="row wrap between">
        <nav className="row">
          <button
            type="button"
            className="button button-ghost button-small"
            onClick={() => setDistrict(null)}
          >
            {text.dashboard.state}
          </button>
          {district && <strong>› {district.name}</strong>}
        </nav>
        <button
          type="button"
          className="button button-secondary button-small"
          disabled={skipping}
          onClick={() => void skipWeek()}
        >
          ⏩ {text.dashboard.skipWeek}
        </button>
      </div>
      {summary.loading && <Loading />}
      {summary.error && <ErrorMessage error={summary.error} onRetry={summary.reload} />}
      {totals && (
        <div className="tiles">
          {COUNTER_KEYS.map((key) => (
            <div key={key} className="tile">
              <span className="tile-value">{totals[key].toLocaleString('hi-IN')}</span>
              <span className="tile-label">{text.dashboard.counters[key]}</span>
            </div>
          ))}
          <div className="tile tile-highlight">
            <span className="tile-value">{percent(totals.reached, totals.referred)}%</span>
            <span className="tile-label">
              {text.dashboard.counters.reached} / {text.dashboard.counters.referred}
            </span>
          </div>
        </div>
      )}
      {summary.data && (
        <div className="table-scroll">
          <table className="table">
            <thead>
              <tr>
                <th>
                  {summary.data.level === 'state' ? text.dashboard.district : text.area.block}
                </th>
                {TABLE_COLUMNS.map((key) => (
                  <th key={key}>{text.dashboard.counters[key]}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {summary.data.rows.map((row: DashboardRow) => (
                <tr key={row.code}>
                  <td>
                    {summary.data!.level === 'state' ? (
                      <button
                        type="button"
                        className="link"
                        onClick={() => setDistrict({ code: row.code, name: row.name })}
                      >
                        {row.name}
                      </button>
                    ) : (
                      row.name
                    )}
                  </td>
                  {TABLE_COLUMNS.map((key) => (
                    <td key={key} className="numeric">
                      {row[key]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
