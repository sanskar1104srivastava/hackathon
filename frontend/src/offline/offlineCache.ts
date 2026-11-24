import { get, set } from 'idb-keyval'

/**
 * Loads fresh data when online and remembers it, so a worker can still open a child and screen without network.
 * Only network failures fall back to the saved copy; server errors are shown as errors.
 */
export async function loadWithOfflineCopy<T>(cacheKey: string, load: () => Promise<T>): Promise<T> {
  try {
    const data = await load()
    await set(cacheKey, data)
    return data
  } catch (error) {
    if (!(error instanceof TypeError)) throw error
    const saved = await get<T>(cacheKey)
    if (saved === undefined) throw error
    return saved
  }
}
