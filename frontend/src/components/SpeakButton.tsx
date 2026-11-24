import { text } from '../i18n/hi'
import { speakHindi } from '../lib/speech'

export function SpeakButton({ say }: { say: string }) {
  return (
    <button
      type="button"
      className="button button-ghost button-small"
      onClick={() => speakHindi(say)}
      aria-label={text.listen}
    >
      🔊 {text.listen}
    </button>
  )
}
