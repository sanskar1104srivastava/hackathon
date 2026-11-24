import type {
  AiObservation,
  Check,
  Measurements,
  ScreeningInput,
  Setting,
} from '../../../api/types'
import { text } from '../../../i18n/hi'

export interface ScreeningDraft {
  consentGiven: boolean
  setting: Setting
  measurements: Measurements
  answers: Record<string, boolean>
  aiObservations: Record<string, AiObservation>
  speech: { shownCount: number; namedCount: number } | null
  tasks: Record<string, boolean>
}

export type DraftChange = (change: Partial<ScreeningDraft>) => void

export type Step =
  | { kind: 'consent' }
  | { kind: 'measurements'; checks: Check[] }
  | { kind: 'sign'; check: Check }
  | { kind: 'speech'; check: Check }
  | { kind: 'questions'; title: string; checks: Check[] }
  | { kind: 'vision'; check: Check }
  | { kind: 'attention'; check: Check }
  | { kind: 'review' }

export const emptyDraft: ScreeningDraft = {
  consentGiven: false,
  setting: 'anganwadi',
  measurements: {},
  answers: {},
  aiObservations: {},
  speech: null,
  tasks: {},
}

/** The age-appropriate steps, in the order a worker does them. Media steps only appear after consent. */
export function buildSteps(checks: Check[], consentGiven: boolean): Step[] {
  const byMethod = (method: Check['method']) => checks.filter((check) => check.method === method)
  const steps: Step[] = [{ kind: 'consent' }]
  const measurements = byMethod('measurement')
  if (measurements.length) steps.push({ kind: 'measurements', checks: measurements })
  if (consentGiven) {
    steps.push(
      ...[...byMethod('photo'), ...byMethod('video')].map((check) => ({
        kind: 'sign' as const,
        check,
      })),
    )
    steps.push(...byMethod('voice').map((check) => ({ kind: 'speech' as const, check })))
  }
  const questionGroups: [string, Check[]][] = [
    [text.screening.developmentTitle, byMethod('milestone')],
    [text.screening.behaviourTitle, byMethod('mchat')],
    [text.screening.healthTitle, byMethod('question')],
  ]
  for (const [title, group] of questionGroups) {
    if (group.length) steps.push({ kind: 'questions', title, checks: group })
  }
  for (const check of byMethod('task')) {
    steps.push({ kind: check.id === 'visionChart' ? 'vision' : 'attention', check })
  }
  steps.push({ kind: 'review' })
  return steps
}

export function toScreeningInput(draft: ScreeningDraft, workerId: string): ScreeningInput {
  return {
    screeningId: crypto.randomUUID().replaceAll('-', ''),
    setting: draft.setting,
    screenedAt: new Date().toISOString(),
    workerId,
    consentGiven: draft.consentGiven,
    measurements: draft.measurements,
    answers: draft.answers,
    aiObservations: Object.values(draft.aiObservations),
    speech: draft.speech,
    tasks: Object.entries(draft.tasks).map(([checkId, passed]) => ({ checkId, passed })),
  }
}
