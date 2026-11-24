import type { Colour } from '../api/types'
import { colourLabels } from '../i18n/hi'

export function ColourBadge({ colour, label }: { colour: Colour; label?: string }) {
  return <span className={`badge badge-${colour}`}>{label ?? colourLabels[colour]}</span>
}
