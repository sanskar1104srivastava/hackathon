import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/endpoints'
import { AreaPicker } from '../../components/AreaPicker'
import { ErrorMessage, Loading } from '../../components/StatusViews'
import { useAsync } from '../../hooks/useAsync'
import { ageInMonths } from '../../lib/dates'
import { preferences, type SavedArea } from '../../lib/preferences'
import { text } from '../../i18n/hi'
import { loadWithOfflineCopy } from '../../offline/offlineCache'

export function ChildListPage() {
  const [area, setArea] = useState<Partial<SavedArea>>(preferences.getArea() ?? {})
  const children = useAsync(
    () =>
      area.districtCode && area.blockCode
        ? loadWithOfflineCopy(`children:${area.districtCode}:${area.blockCode}`, () =>
            api.listChildren(area.districtCode!, area.blockCode),
          )
        : Promise.resolve([]),
    [area.districtCode, area.blockCode],
  )

  function changeArea(districtCode: number, blockCode: number | null) {
    const next = { districtCode, blockCode: blockCode ?? undefined }
    setArea(next)
    if (blockCode) preferences.setArea({ districtCode, blockCode })
  }

  return (
    <div className="stack">
      <div className="row between">
        <h1>{text.children.title}</h1>
        <Link to="/field/alerts" className="button button-ghost button-small">
          🔔 {text.children.alerts}
        </Link>
      </div>
      <AreaPicker
        districtCode={area.districtCode ?? null}
        blockCode={area.blockCode ?? null}
        onChange={changeArea}
      />
      <Link to="/field/register" className="button button-primary">
        + {text.children.register}
      </Link>
      {children.loading && <Loading />}
      {children.error && <ErrorMessage error={children.error} onRetry={children.reload} />}
      {children.data?.length === 0 && area.blockCode && (
        <p className="muted">{text.children.empty}</p>
      )}
      <ul className="list">
        {children.data?.map((child) => (
          <li key={child.childId}>
            <Link to={`/field/children/${child.childId}`} className="list-item">
              <strong>{child.name}</strong>
              <span className="muted">
                {text.children.years(ageInMonths(child.dateOfBirth))} · {child.guardianName}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
