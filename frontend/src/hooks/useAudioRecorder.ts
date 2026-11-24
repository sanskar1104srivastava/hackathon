import { useRef, useState } from 'react'

export interface Recording {
  blob: Blob
  mimeType: string
}

/** Records from the microphone with the browser's MediaRecorder (webm/opus on Android Chrome). */
export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  async function start(): Promise<void> {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const recorder = new MediaRecorder(stream)
    chunksRef.current = []
    recorder.ondataavailable = (event) => chunksRef.current.push(event.data)
    recorder.start()
    recorderRef.current = recorder
    setIsRecording(true)
  }

  function stop(): Promise<Recording> {
    const recorder = recorderRef.current
    if (!recorder) return Promise.reject(new Error('Not recording'))
    return new Promise((resolve) => {
      recorder.onstop = () => {
        recorder.stream.getTracks().forEach((track) => track.stop())
        const mimeType = recorder.mimeType.split(';')[0] || 'audio/webm'
        setIsRecording(false)
        resolve({ blob: new Blob(chunksRef.current, { type: mimeType }), mimeType })
      }
      recorder.stop()
    })
  }

  return { isRecording, start, stop }
}
