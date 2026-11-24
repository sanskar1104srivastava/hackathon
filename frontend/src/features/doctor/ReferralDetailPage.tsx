import { useState, type FormEvent } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../../api/endpoints'
import type { Referral } from '../../api/types'
import { DomainResults } from '../../components/DomainResults'
import { ErrorMessage, Loading } from '../../components/StatusViews'
import { useAsync } from '../../hooks/useAsync'
import { ageInMonths, formatDate } from '../../lib/dates'
import { referralStatusLabels, text } from '../../i18n/hi'
import { DiagnosisForm, type DiagnosisInput } from './DiagnosisForm'

export function ReferralDetailPage() {
  const { childId = '', referralId = '' } = useParams()
  const detail = useAsync(() => api.getChildDetail(childId), [childId])
  const [actionError, setActionError] = useState<Error | null>(null)
  const [recordsStatus, setRecordsStatus] = useState<string | null>(null)

  if (detail.loading) return <Loading />
  if (detail.error || !detail.data)
    return <ErrorMessage error={detail.error!} onRetry={detail.reload} />

  const { child, screenings, referrals } = detail.data
  const referral: Referral | undefined = referrals.find((item) => item.referralId === referralId)
  if (!referral) return <ErrorMessage error={new Error('Referral not found')} />
  const screening =
    screenings.find((item) => item.screeningId === referral.screeningId) ?? screenings[0]

  async function run(action: () => Promise<unknown>) {
    setActionError(null)
    try {
      await action()
      detail.reload()
    } catch (error) {
      setActionError(error as Error)
    }
  }

  async function requestRecords(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    await run(() =>
      api.requestRecords(childId, referralId, {
        requesterName: String(form.get('requesterName')),
        requesterId: String(form.get('requesterId')),
      }),
    )
  }

  return (
    <div className="stack">
      <div>
        <h1>{child.name}</h1>
        <p className="muted">
          {text.children.years(ageInMonths(child.dateOfBirth))} · {child.guardianName} ·{' '}
          {child.guardianPhone}
        </p>
      </div>
      <section className="card card-red">
        <header className="row between">
          <h2>{referral.facilityName}</h2>
          <span className="pill">{referralStatusLabels[referral.status]}</span>
        </header>
        <p className="muted">{formatDate(referral.createdAt)}</p>
        <ul className="findings">
          {referral.reasonsEn.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      </section>
      {actionError && <ErrorMessage error={actionError} />}

      {referral.status === 'sent' && (
        <button
          type="button"
          className="button button-primary"
          onClick={() => void run(() => api.markArrived(childId, referralId))}
        >
          ✓ {text.doctor.markArrived}
        </button>
      )}
      {referral.status === 'underTreatment' ? (
        <section className="card card-green">
          <h2>{referral.doctorName}</h2>
          <p>{referral.diagnosisText}</p>
          <p className="advice">{referral.carePlan?.careInstructionsHi}</p>
        </section>
      ) : (
        <DiagnosisForm
          onSave={(input: DiagnosisInput) =>
            run(() => api.recordDiagnosis(childId, referralId, input))
          }
        />
      )}

      <section className="card stack">
        <h2>{text.doctor.recordsTitle}</h2>
        {!child.abhaAddress && <p className="muted">{text.doctor.noAbha}</p>}
        {child.abhaAddress && !referral.recordsStatus && (
          <form className="stack" onSubmit={(event) => void requestRecords(event)}>
            <label className="field">
              <span>{text.doctor.requesterName}</span>
              <input name="requesterName" required />
            </label>
            <label className="field">
              <span>{text.doctor.requesterId}</span>
              <input name="requesterId" required />
            </label>
            <button className="button button-secondary">{text.doctor.requestRecords}</button>
          </form>
        )}
        {referral.recordsStatus && (
          <div className="row between">
            <span className="pill">{recordsStatus ?? referral.recordsStatus}</span>
            <button
              type="button"
              className="button button-ghost button-small"
              onClick={() =>
                void api
                  .getRecords(childId, referralId)
                  .then((records) => setRecordsStatus(records.recordsStatus))
              }
            >
              {text.doctor.refreshRecords}
            </button>
          </div>
        )}
      </section>

      {screening && <DomainResults outcome={screening.outcome} />}
    </div>
  )
}
