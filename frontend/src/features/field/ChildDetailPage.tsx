import { QRCodeSVG } from 'qrcode.react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../../api/endpoints'
import { ColourBadge } from '../../components/ColourBadge'
import { ErrorMessage, Loading } from '../../components/StatusViews'
import { useAsync } from '../../hooks/useAsync'
import { ageInMonths, formatDate } from '../../lib/dates'
import { referralStatusLabels, text } from '../../i18n/hi'
import { loadWithOfflineCopy } from '../../offline/offlineCache'

export function ChildDetailPage() {
  const { childId = '' } = useParams()
  const detail = useAsync(
    () => loadWithOfflineCopy(`child:${childId}`, () => api.getChildDetail(childId)),
    [childId],
  )

  if (detail.loading) return <Loading />
  if (detail.error || !detail.data)
    return <ErrorMessage error={detail.error!} onRetry={detail.reload} />

  const { child, screenings, referrals, homePlan } = detail.data
  const parentUrl = child.parentLinkPath ? `${window.location.origin}${child.parentLinkPath}` : null

  return (
    <div className="stack">
      <div>
        <h1>{child.name}</h1>
        <p className="muted">
          {text.children.years(ageInMonths(child.dateOfBirth))} · {child.guardianName} ·{' '}
          {child.blockName}, {child.districtName}
        </p>
      </div>
      <Link to={`/field/children/${childId}/screen`} className="button button-primary">
        {text.childDetail.startScreening}
      </Link>

      {referrals.length > 0 && (
        <section className="card">
          <h2>{text.childDetail.referrals}</h2>
          {referrals.map((referral) => (
            <p key={referral.referralId} className="row between">
              <span>{referral.facilityName}</span>
              <span className="pill">{referralStatusLabels[referral.status]}</span>
            </p>
          ))}
        </section>
      )}
      {homePlan && <p className="notice">{text.childDetail.homePlan}</p>}

      <section className="card">
        <h2>{text.childDetail.history}</h2>
        {screenings.length === 0 && <p className="muted">{text.childDetail.noScreenings}</p>}
        {screenings.map((screening) => (
          <p key={screening.screeningId} className="row between">
            <span>{formatDate(screening.screenedAt)}</span>
            <ColourBadge colour={screening.outcome.overall} />
          </p>
        ))}
      </section>

      {parentUrl && (
        <section className="card center">
          <h2>{text.childDetail.parentLink}</h2>
          <QRCodeSVG value={parentUrl} size={192} className="qr" />
          <p className="muted">{text.childDetail.parentLinkHint}</p>
        </section>
      )}
    </div>
  )
}
