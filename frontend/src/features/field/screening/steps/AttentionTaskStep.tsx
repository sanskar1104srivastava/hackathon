import { useEffect, useRef, useState } from 'react'
import type { Check } from '../../../../api/types'
import { text } from '../../../../i18n/hi'

const TRIALS = 12
const GO_SHARE = 0.7
const STIMULUS_MS = 1200
const PASS_ACCURACY = 0.75

type Phase = 'ready' | 'running' | 'done'

const randomGo = () => Math.random() < GO_SHARE
const hasPassed = (correct: number) => correct / TRIALS >= PASS_ACCURACY

interface AttentionTaskStepProps {
  check: Check
  onResult: (passed: boolean) => void
}

/** Go/no-go game: touch the green circle, hold back on the red one. Scores how often the child got it right. */
export function AttentionTaskStep({ check, onResult }: AttentionTaskStepProps) {
  const [phase, setPhase] = useState<Phase>('ready')
  const [trial, setTrial] = useState(0)
  const [isGo, setIsGo] = useState(randomGo)
  const [correct, setCorrect] = useState(0)
  const tappedRef = useRef(false)

  useEffect(() => {
    if (phase !== 'running') return
    tappedRef.current = false
    const timer = window.setTimeout(() => {
      const nextCorrect = correct + (tappedRef.current === isGo ? 1 : 0)
      setCorrect(nextCorrect)
      if (trial + 1 >= TRIALS) {
        setPhase('done')
        onResult(hasPassed(nextCorrect))
      } else {
        setTrial(trial + 1)
        setIsGo(randomGo())
      }
    }, STIMULUS_MS)
    return () => window.clearTimeout(timer)
  }, [phase, trial, isGo, correct, onResult])

  if (phase === 'ready') {
    return (
      <div className="stack center">
        <h2>{check.labelHi}</h2>
        <p className="muted">{text.screening.attentionHint}</p>
        <button type="button" className="button button-primary" onClick={() => setPhase('running')}>
          {text.screening.startGame}
        </button>
      </div>
    )
  }

  if (phase === 'done') {
    return (
      <div className="stack center">
        <h2>{check.labelHi}</h2>
        <p className={`notice notice-${hasPassed(correct) ? 'ok' : 'warn'}`}>
          {hasPassed(correct) ? text.screening.passed : text.screening.notPassed} ({correct}/
          {TRIALS})
        </p>
      </div>
    )
  }

  return (
    <div className="stack center">
      <button
        type="button"
        className={`go-circle ${isGo ? 'go' : 'stop'}`}
        onPointerDown={() => {
          tappedRef.current = true
        }}
        aria-label={isGo ? 'green' : 'red'}
      />
      <p className="muted">
        {trial + 1} / {TRIALS}
      </p>
    </div>
  )
}
