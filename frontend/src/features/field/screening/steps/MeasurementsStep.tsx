import { useState } from 'react'
import { api } from '../../../../api/endpoints'
import type { Check, Measurements } from '../../../../api/types'
import { SpeakButton } from '../../../../components/SpeakButton'
import { text } from '../../../../i18n/hi'
import { photoToBase64 } from '../../../../lib/media'
import type { DraftChange, ScreeningDraft } from '../screeningDraft'

const FIELD_BY_CHECK: Record<string, { key: keyof Measurements; unit: string; step: string }> = {
  weight: { key: 'weightKg', unit: 'kg', step: '0.1' },
  height: { key: 'heightCm', unit: 'cm', step: '0.1' },
  muac: { key: 'muacCm', unit: 'cm', step: '0.1' },
  haemoglobin: { key: 'haemoglobinGdl', unit: 'g/dL', step: '0.1' },
}

interface MeasurementsStepProps {
  checks: Check[]
  draft: ScreeningDraft
  onChange: DraftChange
}

export function MeasurementsStep({ checks, draft, onChange }: MeasurementsStepProps) {
  const [readingCheckId, setReadingCheckId] = useState<string | null>(null)
  const [unreadable, setUnreadable] = useState<string | null>(null)

  function setValue(key: keyof Measurements, value: number | undefined) {
    onChange({ measurements: { ...draft.measurements, [key]: value } })
  }

  async function readFromPhoto(check: Check, file: File) {
    if (!check.device) return
    setReadingCheckId(check.id)
    setUnreadable(null)
    try {
      const reading = await api.readDevice(check.device, await photoToBase64(file))
      if (reading.readable && reading.value !== null)
        setValue(FIELD_BY_CHECK[check.id].key, reading.value)
      else setUnreadable(check.id)
    } catch {
      setUnreadable(check.id)
    } finally {
      setReadingCheckId(null)
    }
  }

  return (
    <div className="stack">
      <h2>{text.screening.measurementsTitle}</h2>
      {checks.map((check) => {
        const field = FIELD_BY_CHECK[check.id]
        return (
          <section key={check.id} className="card">
            <header className="row between">
              <h3>{check.labelHi}</h3>
              <SpeakButton say={check.promptHi} />
            </header>
            <p className="muted">{check.promptHi}</p>
            <label className="field">
              <span>{field.unit}</span>
              <input
                type="number"
                inputMode="decimal"
                step={field.step}
                value={draft.measurements[field.key] ?? ''}
                onChange={(event) =>
                  setValue(field.key, event.target.value ? Number(event.target.value) : undefined)
                }
              />
            </label>
            {check.device && navigator.onLine && (
              <label className="button button-secondary button-small">
                📷{' '}
                {readingCheckId === check.id
                  ? text.screening.reading
                  : text.screening.readFromPhoto}
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  hidden
                  onChange={(event) => {
                    const file = event.target.files?.[0]
                    if (file) void readFromPhoto(check, file)
                  }}
                />
              </label>
            )}
            {unreadable === check.id && <p className="notice">{text.screening.unreadable}</p>}
          </section>
        )
      })}
    </div>
  )
}
