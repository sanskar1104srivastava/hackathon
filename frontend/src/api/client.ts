import { enqueueRequest } from '../offline/syncQueue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export class ApiError extends Error {
  readonly status: number
  readonly errorCode: string

  constructor(status: number, errorCode: string, message: string) {
    super(message)
    this.status = status
    this.errorCode = errorCode
  }
}

type Method = 'GET' | 'POST' | 'PUT'

export async function apiRequest<T>(method: Method, path: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (response.status === 204) return undefined as T
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new ApiError(
      response.status,
      payload.errorCode ?? 'HTTP_ERROR',
      payload.message ?? response.statusText,
    )
  }
  return payload as T
}

export type QueuedResult<T> = { queued: false; data: T } | { queued: true }

/** POSTs now, or keeps the request on the phone and sends it later when there is no network. */
export async function postOrQueue<T>(path: string, body: unknown): Promise<QueuedResult<T>> {
  if (!navigator.onLine) {
    await enqueueRequest(path, body)
    return { queued: true }
  }
  try {
    return { queued: false, data: await apiRequest<T>('POST', path, body) }
  } catch (error) {
    if (error instanceof TypeError) {
      await enqueueRequest(path, body)
      return { queued: true }
    }
    throw error
  }
}
