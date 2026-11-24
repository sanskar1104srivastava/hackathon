/** Per-phone conveniences (chosen area, facility, worker id). Safe when storage is blocked. */

export interface SavedArea {
  districtCode: number
  blockCode: number
}

function read<T>(key: string): T | null {
  try {
    const value = localStorage.getItem(key)
    return value ? (JSON.parse(value) as T) : null
  } catch {
    return null
  }
}

function write(key: string, value: unknown): void {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // Private mode or blocked storage: the app still works, it just forgets the choice.
  }
}

export const preferences = {
  getArea: () => read<SavedArea>('up4ds.area'),
  setArea: (area: SavedArea) => write('up4ds.area', area),
  getFacilityId: () => read<string>('up4ds.facilityId'),
  setFacilityId: (facilityId: string) => write('up4ds.facilityId', facilityId),
  getWorkerId: (): string => {
    const existing = read<string>('up4ds.workerId')
    if (existing) return existing
    const created = `worker-${crypto.randomUUID().slice(0, 8)}`
    write('up4ds.workerId', created)
    return created
  },
}
