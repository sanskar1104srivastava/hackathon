import type { Check } from '../../../../api/types'
import { SpeakButton } from '../../../../components/SpeakButton'
import { text } from '../../../../i18n/hi'
import type { DraftChange, ScreeningDraft } from '../screeningDraft'

interface QuestionsStepProps {
  title: string
  checks: Check[]
  draft: ScreeningDraft
  onChange: DraftChange
}

/** Yes/no questions read aloud to the parent: milestones, M-CHAT-R items, or health warning signs. */
export function QuestionsStep({ title, checks, draft, onChange }: QuestionsStepProps) {
  function answer(checkId: string, value: boolean) {
    onChange({ answers: { ...draft.answers, [checkId]: value } })
  }

  return (
    <div className="stack">
      <h2>{title}</h2>
      {checks.map((check) => (
        <section key={check.id} className="card">
          <div className="row between top">
            <p className="question">{check.promptHi}</p>
            <SpeakButton say={check.promptHi} />
          </div>
          <div className="segmented">
            {[true, false].map((value) => (
              <button
                key={String(value)}
                type="button"
                className={draft.answers[check.id] === value ? 'selected' : ''}
                onClick={() => answer(check.id, value)}
              >
                {value ? text.yes : text.no}
              </button>
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}
