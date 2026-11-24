import { Link } from 'react-router-dom'
import type { ScreeningResult } from '../../../api/types'
import { DomainResults } from '../../../components/DomainResults'
import { text } from '../../../i18n/hi'

/** UC-3 result for the family, plus what happens next: referral (UC-4) and home plan (UC-5). */
export function ScreeningResultView({
  result,
  childId,
}: {
  result: ScreeningResult
  childId: string
}) {
  const { referral, homePlan } = result
  return (
    <div className="stack">
      <h1>{text.result.title}</h1>
      <DomainResults outcome={result.screening.outcome} />
      {referral && (
        <section className="card card-red">
          <h2>{text.result.referralTitle}</h2>
          <p>
            <strong>{text.result.goTo}:</strong> {referral.facilityName}
          </p>
          <p>
            <strong>{text.result.why}:</strong> {referral.reasonsHi.join('; ')}
          </p>
        </section>
      )}
      {homePlan && (
        <section className="card card-yellow">
          <h2>{text.result.homePlanTitle}</h2>
          <p>{text.result.homePlanBody}</p>
        </section>
      )}
      <p className="muted small">{text.result.noDiagnosis}</p>
      <Link to={`/field/children/${childId}`} className="button button-secondary">
        {text.childDetail.parentLink}
      </Link>
      <Link to="/field" className="button button-ghost">
        {text.result.done}
      </Link>
    </div>
  )
}
