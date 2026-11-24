import { useCallback, useEffect, useRef, useState } from 'react'

interface AsyncState<T> {
  data: T | null
  error: Error | null
  loading: boolean
  reload: () => void
}

interface Settled<T> {
  key: string
  data: T | null
  error: Error | null
}

/**
 * Runs `load` whenever `dependencies` (plain values) change and exposes the result; `reload` runs it again.
 * While a new load runs, the previous data stays available so lists do not flash empty.
 */
export function useAsync<T>(load: () => Promise<T>, dependencies: unknown[]): AsyncState<T> {
  const [attempt, setAttempt] = useState(0)
  const [settled, setSettled] = useState<Settled<T> | null>(null)
  const loadRef = useRef(load)
  const key = JSON.stringify([...dependencies, attempt])

  useEffect(() => {
    loadRef.current = load
  })

  useEffect(() => {
    let cancelled = false
    loadRef.current().then(
      (data) => !cancelled && setSettled({ key, data, error: null }),
      (error: unknown) => !cancelled && setSettled({ key, data: null, error: error as Error }),
    )
    return () => {
      cancelled = true
    }
  }, [key])

  const reload = useCallback(() => setAttempt((value) => value + 1), [])
  const isCurrent = settled?.key === key
  return {
    data: settled?.data ?? null,
    error: isCurrent ? settled.error : null,
    loading: !isCurrent,
    reload,
  }
}
