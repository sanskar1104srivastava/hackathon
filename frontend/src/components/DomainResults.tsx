import type { Domain, ScreeningOutcome } from '../api/types'
import { domainLabels } from '../i18n/hi'
import { ColourBadge } from './ColourBadge'
import { SpeakButton } from './SpeakButton'

const DOMAIN_ORDER: Domain[] = ['defects', 'deficiencies', 'diseases', 'development']

/** The four Ds, each with its colour, what was noticed, and the plain-Hindi advice (UC-3). */
export function DomainResults({ outcome }: { outcome: ScreeningOutcome }) {
  return (
    <div className="stack">
      {DOMAIN_ORDER.map((domain) => {
        const result = outcome.domains[domain]
        return (
          <section key={domain} className={`card card-${result.colour}`}>
            <header className="row between">
              <h3>{domainLabels[domain]}</h3>
              <ColourBadge colour={result.colour} />
            </header>
            {result.findings.length > 0 && (
              <ul className="findings">
                {result.findings.map((finding) => (
                  <li key={`${finding.checkId}-${finding.noteEn}`}>{finding.noteHi}</li>
                ))}
              </ul>
            )}
            <p className="advice">{result.adviceHi}</p>
            <SpeakButton say={`${domainLabels[domain]}. ${result.adviceHi}`} />
          </section>
        )
      })}
    </div>
  )
}
