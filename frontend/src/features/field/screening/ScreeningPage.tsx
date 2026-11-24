import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../../../api/endpoints'
import type { ScreeningResult } from '../../../api/types'
import { ErrorMessage, Loading } from '../../../components/StatusViews'
import { useAsync } from '../../../hooks/useAsync'
import { ageInMonths } from '../../../lib/dates'
import { preferences } from '../../../lib/preferences'
import { text } from '../../../i18n/hi'
import { loadWithOfflineCopy } from '../../../offline/offlineCache'
import { ScreeningResultView } from './ScreeningResultView'
import {
  buildSteps,
  emptyDraft,
  toScreeningInput,
  type ScreeningDraft,
  type Step,
} from './screeningDraft'
import { AttentionTaskStep } from './steps/AttentionTaskStep'
import { ConsentStep } from './steps/ConsentStep'
import { MeasurementsStep } from './steps/MeasurementsStep'
import { QuestionsStep } from './steps/QuestionsStep'
import { SignCheckStep } from './steps/SignCheckStep'
import { SpeechStep } from './steps/SpeechStep'
import { VisionTaskStep } from './steps/VisionTaskStep'

type Submission =
  | { status: 'editing' }
  | { status: 'submitting' }
  | { status: 'queued' }
  | { status: 'done'; result: ScreeningResult }
  | { status: 'failed'; error: Error }

/** UC-1: the guided, age-based screening, one step at a time. */
export function ScreeningPage() {
  const { childId = '' } = useParams()
  const loaded = useAsync(async () => {
    const detail = await loadWithOfflineCopy(`child:${childId}`, () => api.getChildDetail(childId))
    const months = ageInMonths(detail.child.dateOfBirth)
    const checkList = await loadWithOfflineCopy(`checks:${childId}`, () => api.getChecks(months))
    return { child: detail.child, ageMonths: months, checkList }
  }, [childId])

  const [draft, setDraft] = useState<ScreeningDraft>(emptyDraft)
  const [stepIndex, setStepIndex] = useState(0)
  const [submission, setSubmission] = useState<Submission>({ status: 'editing' })
  const steps = useMemo(
    () => (loaded.data ? buildSteps(loaded.data.checkList.checks, draft.consentGiven) : []),
    [loaded.data, draft.consentGiven],
  )

  if (loaded.loading) return <Loading />
  if (loaded.error || !loaded.data)
    return <ErrorMessage error={loaded.error!} onRetry={loaded.reload} />
  if (submission.status === 'done')
    return <ScreeningResultView result={submission.result} childId={childId} />
  if (submission.status === 'queued') return <p className="notice">{text.screening.queued}</p>

  const { child, ageMonths, checkList } = loaded.data
  const step = steps[Math.min(stepIndex, steps.length - 1)]
  const change = (patch: Partial<ScreeningDraft>) =>
    setDraft((current) => ({ ...current, ...patch }))
  const recordTask = (checkId: string) => (passed: boolean) =>
    setDraft((current) => ({ ...current, tasks: { ...current.tasks, [checkId]: passed } }))

  async function submit() {
    setSubmission({ status: 'submitting' })
    try {
      const outcome = await api.submitScreening(
        childId,
        toScreeningInput(draft, preferences.getWorkerId()),
      )
      setSubmission(
        outcome.queued ? { status: 'queued' } : { status: 'done', result: outcome.data },
      )
    } catch (error) {
      setSubmission({ status: 'failed', error: error as Error })
    }
  }

  function renderStep(current: Step) {
    switch (current.kind) {
      case 'consent':
        return <ConsentStep draft={draft} onChange={change} />
      case 'measurements':
        return <MeasurementsStep checks={current.checks} draft={draft} onChange={change} />
      case 'sign':
        return (
          <SignCheckStep
            check={current.check}
            ageMonths={ageMonths}
            draft={draft}
            onChange={change}
          />
        )
      case 'speech':
        return (
          <SpeechStep
            check={current.check}
            pictureCards={checkList.pictureCards}
            onChange={change}
          />
        )
      case 'questions':
        return (
          <QuestionsStep
            title={current.title}
            checks={current.checks}
            draft={draft}
            onChange={change}
          />
        )
      case 'vision':
        return <VisionTaskStep check={current.check} onResult={recordTask(current.check.id)} />
      case 'attention':
        return <AttentionTaskStep check={current.check} onResult={recordTask(current.check.id)} />
      case 'review':
        return (
          <div className="stack">
            <h2>{child.name}</h2>
            {submission.status === 'failed' && <ErrorMessage error={submission.error} />}
            <button
              type="button"
              className="button button-primary"
              disabled={submission.status === 'submitting'}
              onClick={() => void submit()}
            >
              {submission.status === 'submitting'
                ? text.screening.submitting
                : text.screening.submit}
            </button>
          </div>
        )
    }
  }

  return (
    <div className="stack">
      <p className="muted">
        {child.name} · {text.screening.stepOf(stepIndex + 1, steps.length)}
      </p>
      <progress className="progress" value={stepIndex + 1} max={steps.length} />
      {/* key resets per-step state (recordings, games) when moving between steps */}
      <div key={`${step.kind}-${stepIndex}`}>{renderStep(step)}</div>
      <nav className="row between step-nav">
        <button
          type="button"
          className="button button-ghost"
          disabled={stepIndex === 0}
          onClick={() => setStepIndex(stepIndex - 1)}
        >
          {text.back}
        </button>
        {step.kind !== 'review' && (
          <button
            type="button"
            className="button button-secondary"
            onClick={() => setStepIndex(stepIndex + 1)}
          >
            {text.next}
          </button>
        )}
      </nav>
    </div>
  )
}
