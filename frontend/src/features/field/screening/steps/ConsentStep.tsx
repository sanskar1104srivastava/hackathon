import type { Setting } from '../../../../api/types'
import { SpeakButton } from '../../../../components/SpeakButton'
import { settingLabels, text } from '../../../../i18n/hi'
import type { DraftChange, ScreeningDraft } from '../screeningDraft'

export function ConsentStep({ draft, onChange }: { draft: ScreeningDraft; onChange: DraftChange }) {
  return (
    <div className="stack">
      <h2>{text.screening.consentTitle}</h2>
      <p>{text.screening.consentBody}</p>
      <SpeakButton say={text.screening.consentBody} />
      <div className="segmented">
        <button
          type="button"
          className={draft.consentGiven ? 'selected' : ''}
          onClick={() => onChange({ consentGiven: true })}
        >
          {text.screening.consentYes}
        </button>
        <button
          type="button"
          className={!draft.consentGiven ? 'selected' : ''}
          onClick={() => onChange({ consentGiven: false, aiObservations: {}, speech: null })}
        >
          {text.screening.consentNo}
        </button>
      </div>
      <label className="field">
        <span>{text.screening.setting}</span>
        <select
          value={draft.setting}
          onChange={(event) => onChange({ setting: event.target.value as Setting })}
        >
          {Object.entries(settingLabels).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
    </div>
  )
}
