import { useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { api } from '../../api/endpoints'
import type { Activity, PictureCard } from '../../api/types'
import { DomainResults } from '../../components/DomainResults'
import { SpeakButton } from '../../components/SpeakButton'
import { ErrorMessage, Loading } from '../../components/StatusViews'
import { useAsync } from '../../hooks/useAsync'
import { useAudioRecorder } from '../../hooks/useAudioRecorder'
import { ageInMonths, formatDate } from '../../lib/dates'
import { blobToBase64 } from '../../lib/media'
import { referralStatusLabels, text } from '../../i18n/hi'

const SPEECH_CARDS = 5

/** UC-5: the parent's own page from the QR code. Shows the result, the referral and today's home activities. */
export function ParentPage() {
  const { childId = '' } = useParams()
  const token = useSearchParams()[0].get('token') ?? ''
  const view = useAsync(async () => {
    const parentView = await api.getParentView(childId, token)
    const checks = await api.getChecks(ageInMonths(parentView.child.dateOfBirth))
    return { parentView, pictureCards: checks.pictureCards.slice(0, SPEECH_CARDS) }
  }, [childId, token])

  if (view.loading) return <Loading />
  if (view.error || !view.data)
    return <p className="notice notice-error">{text.parent.invalidLink}</p>

  const { parentView, pictureCards } = view.data
  const { child, latestResult, referral, homePlan } = parentView
  return (
    <div className="stack">
      <h1>{text.parent.greeting(child.name)}</h1>
      {referral && (
        <section className="card card-red">
          <h2>{referral.facilityName}</h2>
          <p>{referral.reasonsHi.join('; ')}</p>
          <span className="pill">{referralStatusLabels[referral.status]}</span>
          {referral.carePlan?.careInstructionsHi && (
            <p className="advice">{referral.carePlan.careInstructionsHi}</p>
          )}
        </section>
      )}
      <section className="stack">
        <h2>{text.parent.todaysActivities}</h2>
        {!homePlan && <p className="muted">{text.parent.noPlan}</p>}
        {homePlan?.todaysActivities.map((activity) => (
          <ActivityCard
            key={activity.id}
            activity={activity}
            pictureCards={pictureCards}
            onDone={(score) => api.recordProgress(childId, token, activity.id, score)}
          />
        ))}
      </section>
      {latestResult && (
        <section className="stack">
          <h2>
            {text.parent.latestResult} · {formatDate(latestResult.screenedAt)}
          </h2>
          <DomainResults outcome={latestResult.outcome} />
        </section>
      )}
    </div>
  )
}

interface ActivityCardProps {
  activity: Activity
  pictureCards: PictureCard[]
  onDone: (score: number) => Promise<unknown>
}

/** One home activity. Speaking games are recorded and the AI counts the pictures the child named. */
function ActivityCard({ activity, pictureCards, onDone }: ActivityCardProps) {
  const recorder = useAudioRecorder()
  const [done, setDone] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  async function finish(score: number) {
    try {
      await onDone(score)
      setDone(true)
    } catch (caught) {
      setError(caught as Error)
    }
  }

  async function stopAndScore() {
    const recording = await recorder.stop()
    const cardIds = pictureCards.map((card) => card.id)
    try {
      const result = await api.checkSpeech(
        await blobToBase64(recording.blob),
        recording.mimeType,
        cardIds,
      )
      await finish(result.namedCount / result.shownCount)
    } catch {
      await finish(1)
    }
  }

  return (
    <section className="card">
      <header className="row between">
        <h3>{activity.titleHi}</h3>
        <SpeakButton say={`${activity.titleHi}. ${activity.stepsHi}`} />
      </header>
      <p>{activity.stepsHi}</p>
      {activity.checkMethod === 'voice' && !done && (
        <>
          <div className="picture-grid">
            {pictureCards.map((card) => (
              <span key={card.id} className="picture-card">
                <span className="picture-symbol" aria-hidden="true">
                  {card.symbol}
                </span>
              </span>
            ))}
          </div>
          <button
            type="button"
            className="button button-secondary"
            onClick={() => void (recorder.isRecording ? stopAndScore() : recorder.start())}
          >
            {recorder.isRecording
              ? `⏹ ${text.screening.stopRecording}`
              : `🎙 ${text.parent.recordSpeech}`}
          </button>
        </>
      )}
      {error && <ErrorMessage error={error} />}
      {done ? (
        <p className="notice notice-ok">{text.parent.doneThanks}</p>
      ) : (
        <button type="button" className="button button-primary" onClick={() => void finish(1)}>
          ✓ {text.parent.done}
        </button>
      )}
    </section>
  )
}
