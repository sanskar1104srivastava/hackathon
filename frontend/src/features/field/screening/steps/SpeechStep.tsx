import { useState } from 'react'
import { api } from '../../../../api/endpoints'
import type { Check, PictureCard } from '../../../../api/types'
import { SpeakButton } from '../../../../components/SpeakButton'
import { useAudioRecorder } from '../../../../hooks/useAudioRecorder'
import { text } from '../../../../i18n/hi'
import { blobToBase64 } from '../../../../lib/media'
import type { DraftChange } from '../screeningDraft'

const CARDS_SHOWN = 6

interface SpeechStepProps {
  check: Check
  pictureCards: PictureCard[]
  onChange: DraftChange
}

/** Picture naming. Deepgram transcribes the child; the worker's taps on named cards are the backup. */
export function SpeechStep({ check, pictureCards, onChange }: SpeechStepProps) {
  const cards = pictureCards.slice(0, CARDS_SHOWN)
  const recorder = useAudioRecorder()
  const [named, setNamed] = useState<Set<string>>(new Set())
  const [checking, setChecking] = useState(false)
  const [transcript, setTranscript] = useState('')

  function saveNamed(next: Set<string>) {
    setNamed(next)
    onChange({ speech: { shownCount: cards.length, namedCount: next.size } })
  }

  function toggle(cardId: string) {
    const next = new Set(named)
    if (next.has(cardId)) next.delete(cardId)
    else next.add(cardId)
    saveNamed(next)
  }

  async function stopAndCheck() {
    const recording = await recorder.stop()
    setChecking(true)
    try {
      const result = await api.checkSpeech(
        await blobToBase64(recording.blob),
        recording.mimeType,
        cards.map((card) => card.id),
      )
      setTranscript(result.transcript)
      saveNamed(new Set(result.namedCardIds))
    } catch {
      setTranscript('')
    } finally {
      setChecking(false)
    }
  }

  return (
    <div className="stack">
      <header className="row between">
        <h2>{text.screening.speechTitle}</h2>
        <SpeakButton say={check.promptHi} />
      </header>
      <p>{check.promptHi}</p>
      <div className="picture-grid">
        {cards.map((card) => (
          <button
            key={card.id}
            type="button"
            className={`picture-card ${named.has(card.id) ? 'selected' : ''}`}
            onClick={() => toggle(card.id)}
            aria-pressed={named.has(card.id)}
          >
            <span className="picture-symbol" aria-hidden="true">
              {card.symbol}
            </span>
            <span>{card.wordHi}</span>
          </button>
        ))}
      </div>
      {navigator.onLine && (
        <button
          type="button"
          className="button button-primary"
          disabled={checking}
          onClick={() => void (recorder.isRecording ? stopAndCheck() : recorder.start())}
        >
          {checking
            ? text.screening.checking
            : recorder.isRecording
              ? `⏹ ${text.screening.stopRecording}`
              : `🎙 ${text.screening.record}`}
        </button>
      )}
      {transcript && <p className="muted">“{transcript}”</p>}
      <p className="notice">{text.screening.namedCount(named.size, cards.length)}</p>
    </div>
  )
}
