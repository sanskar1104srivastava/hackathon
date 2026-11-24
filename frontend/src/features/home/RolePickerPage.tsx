import { Link } from 'react-router-dom'
import { text } from '../../i18n/hi'

const ROLES = [
  { to: '/field', title: text.roles.field, hint: text.roles.fieldHint, icon: '🩺' },
  { to: '/doctor', title: text.roles.doctor, hint: text.roles.doctorHint, icon: '🏥' },
  { to: '/dashboard', title: text.roles.dashboard, hint: text.roles.dashboardHint, icon: '📊' },
]

/** Proof of concept: roles are picked here; production would sign users in. */
export function RolePickerPage() {
  return (
    <div className="stack">
      <div>
        <h1>{text.appTitle}</h1>
        <p className="muted">{text.appSubtitle}</p>
      </div>
      <h2>{text.roles.title}</h2>
      {ROLES.map((role) => (
        <Link key={role.to} to={role.to} className="card card-link">
          <span className="role-icon" aria-hidden="true">
            {role.icon}
          </span>
          <span>
            <strong>{role.title}</strong>
            <span className="muted block">{role.hint}</span>
          </span>
        </Link>
      ))}
    </div>
  )
}
