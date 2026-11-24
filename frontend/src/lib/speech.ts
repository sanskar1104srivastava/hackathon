/**
 * Reads Hindi text aloud with the phone's own text-to-speech, which works offline once the Hindi voice is
 * installed (Android: Google Text-to-speech, Hindi).
 */
export function speakHindi(text: string): void {
  if (!('speechSynthesis' in window)) return
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = 'hi-IN'
  utterance.rate = 0.9
  const hindiVoice = window.speechSynthesis.getVoices().find((voice) => voice.lang.startsWith('hi'))
  if (hindiVoice) utterance.voice = hindiVoice
  window.speechSynthesis.speak(utterance)
}
