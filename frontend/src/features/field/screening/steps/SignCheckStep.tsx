import { useState } from 'react'
import { api } from '../../../../api/endpoints'
import type { AiOutcome, Check } from '../../../../api/types'
import { SpeakButton } from '../../../../components/SpeakButton'
import { text } from '../../../../i18n/hi'
import { photoToBase64, videoToFrames } from '../../../../lib/media'
import type { DraftChange, ScreeningDraft } from '../screeningDraft'

const OUTCOME_LABELS: Record<AiOutcome, string> = {
  seen: text.screening.outcomeSeen,
  notSeen: text.screening.outcomeNotSeen,
  unsure: text.screening.outcomeUnsure,
}

interface SignCheckStepProps {
  check: Check
  ageMonths: number
  draft: ScreeningDraft
  onChange: DraftChange
}

/** Photo or short video of one visible sign. Claude gives seen / not seen / unsure; offline the worker decides. */
export function SignCheckStep({ check, ageMonths, draft, onChange }: SignCheckStepProps) {
  const [checking, setChecking] = useState(false)
  const [manual, setManual] = useState(!navigator.onLine)
  const observation = draft.aiObservations[check.id]
  const isVideo = check.method === 'video'

  function record(outcome: AiOutcome, reasonHi = '') {
    onChange({
      aiObservations: {
        ...draft.aiObservations,
        [check.id]: { checkId: check.id, outcome, reasonHi },
      },
    })
  }

  async function analyse(file: File) {
    setChecking(true)
    try {
      const images = isVideo ? await videoToFrames(file) : [await photoToBase64(file)]
      const result = await api.checkSign(check.id, ageMonths, images)
      record(result.outcome, result.reasonHi)
    } catch {
      setManual(true)
    } finally {
      setChecking(false)
    }
  }

  return (
    <div className="stack">
      <header className="row between">
        <h2>{check.labelHi}</h2>
        <SpeakButton say={check.promptHi} />
      </header>
      <p>{check.promptHi}</p>
      {!manual && (
        <label className="button button-primary">
          {checking
            ? text.screening.checking
            : `${isVideo ? '🎥' : '📷'} ${observation ? text.screening.retake : isVideo ? text.screening.takeVideo : text.screening.takePhoto}`}
          <input
            type="file"
            accept={isVideo ? 'video/*' : 'image/*'}
            capture="environment"
            hidden
            disabled={checking}
            onChange={(event) => {
              const file = event.target.files?.[0]
              if (file) void analyse(file)
            }}
          />
        </label>
      )}
      {manual && <p className="notice">{text.screening.aiOffline}</p>}
      {manual && (
        <div className="segmented">
          {(Object.keys(OUTCOME_LABELS) as AiOutcome[]).map((outcome) => (
            <button
              key={outcome}
              type="button"
              className={observation?.outcome === outcome ? 'selected' : ''}
              onClick={() => record(outcome)}
            >
              {OUTCOME_LABELS[outcome]}
            </button>
          ))}
        </div>
      )}
      {observation && !manual && (
        <div className={`notice notice-${observation.outcome === 'notSeen' ? 'ok' : 'warn'}`}>
          <strong>{OUTCOME_LABELS[observation.outcome]}</strong>
          {observation.reasonHi && <p>{observation.reasonHi}</p>}
        </div>
      )}
    </div>
  )
}
