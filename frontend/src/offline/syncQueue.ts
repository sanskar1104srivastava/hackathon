/**
 * Requests made without network (finished screenings) wait in IndexedDB and are sent in order once the
 * phone is back online. The backend treats a re-sent screening as the same one, so retries are safe.
 */
import { get, update } from 'idb-keyval'

const QUEUE_KEY = 'pendingRequests'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

interface PendingRequest {
  id: string
  path: string
  body: unknown
  createdAt: string
}

type Listener = (pendingCount: number) => void
const listeners = new Set<Listener>()

async function notify() {
  const count = await pendingCount()
  listeners.forEach((listener) => listener(count))
}

export async function enqueueRequest(path: string, body: unknown): Promise<void> {
  const request: PendingRequest = {
    id: crypto.randomUUID(),
    path,
    body,
    createdAt: new Date().toISOString(),
  }
  await update<PendingRequest[]>(QUEUE_KEY, (queue = []) => [...queue, request])
  await notify()
}

export async function pendingCount(): Promise<number> {
  return ((await get<PendingRequest[]>(QUEUE_KEY)) ?? []).length
}

let flushing = false

/** Sends waiting requests in order. Stops at the first network failure; drops requests the server rejects. */
export async function flushQueue(): Promise<void> {
  if (flushing || !navigator.onLine) return
  flushing = true
  try {
    for (const request of (await get<PendingRequest[]>(QUEUE_KEY)) ?? []) {
      const response = await fetch(`${API_BASE_URL}${request.path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request.body),
      }).catch(() => null)
      if (response === null || response.status >= 500) break
      if (!response.ok) console.error('Dropped queued request', request.path, response.status)
      await update<PendingRequest[]>(QUEUE_KEY, (queue = []) =>
        queue.filter((item) => item.id !== request.id),
      )
    }
  } finally {
    flushing = false
    await notify()
  }
}

export function subscribeToQueue(listener: Listener): () => void {
  listeners.add(listener)
  void pendingCount().then(listener)
  return () => listeners.delete(listener)
}

export function startAutoSync(): void {
  window.addEventListener('online', () => void flushQueue())
  window.setInterval(() => void flushQueue(), 60_000)
  void flushQueue()
}
