const DAYS_PER_MONTH = 30.4375
const MS_PER_DAY = 86_400_000

export function ageInMonths(dateOfBirth: string, on: Date = new Date()): number {
  return (on.getTime() - new Date(dateOfBirth).getTime()) / MS_PER_DAY / DAYS_PER_MONTH
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('hi-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}
