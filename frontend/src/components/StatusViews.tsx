import { text } from '../i18n/hi'

export function Loading() {
  return <p className="muted center">{text.loading}</p>
}

export function ErrorMessage({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  return (
    <div className="notice notice-error" role="alert">
      <p>{error.message}</p>
      {onRetry && (
        <button type="button" className="button button-secondary" onClick={onRetry}>
          {text.retry}
        </button>
      )}
    </div>
  )
}
