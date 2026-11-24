import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api/endpoints'
import type { NewChild, Sex } from '../../api/types'
import { AreaPicker } from '../../components/AreaPicker'
import { ErrorMessage } from '../../components/StatusViews'
import { todayIso } from '../../lib/dates'
import { preferences } from '../../lib/preferences'
import { text } from '../../i18n/hi'

export function RegisterChildPage() {
  const navigate = useNavigate()
  const savedArea = preferences.getArea()
  const [districtCode, setDistrictCode] = useState<number | null>(savedArea?.districtCode ?? null)
  const [blockCode, setBlockCode] = useState<number | null>(savedArea?.blockCode ?? null)
  const [sex, setSex] = useState<Sex>('female')
  const [error, setError] = useState<Error | null>(null)
  const [saving, setSaving] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!districtCode || !blockCode) return
    const form = new FormData(event.currentTarget)
    const child: NewChild = {
      name: String(form.get('name')),
      sex,
      dateOfBirth: String(form.get('dateOfBirth')),
      guardianName: String(form.get('guardianName')),
      guardianPhone: String(form.get('guardianPhone')),
      districtCode,
      blockCode,
      abhaAddress: String(form.get('abhaAddress') || '') || undefined,
    }
    setSaving(true)
    setError(null)
    try {
      const created = await api.registerChild(child)
      navigate(`/field/children/${created.childId}`, { replace: true })
    } catch (caught) {
      setError(caught as Error)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="stack" onSubmit={submit}>
      <h1>{text.register.title}</h1>
      {!navigator.onLine && <p className="notice">{text.register.needsInternet}</p>}
      <label className="field">
        <span>{text.register.name}</span>
        <input name="name" required maxLength={80} autoComplete="off" />
      </label>
      <fieldset className="field">
        <legend>{text.register.sex}</legend>
        <div className="segmented">
          {(['female', 'male'] as const).map((option) => (
            <button
              key={option}
              type="button"
              className={sex === option ? 'selected' : ''}
              onClick={() => setSex(option)}
            >
              {option === 'female' ? text.register.female : text.register.male}
            </button>
          ))}
        </div>
      </fieldset>
      <label className="field">
        <span>{text.register.dateOfBirth}</span>
        <input name="dateOfBirth" type="date" required max={todayIso()} />
      </label>
      <label className="field">
        <span>{text.register.guardianName}</span>
        <input name="guardianName" required maxLength={80} />
      </label>
      <label className="field">
        <span>{text.register.guardianPhone}</span>
        <input
          name="guardianPhone"
          type="tel"
          inputMode="numeric"
          required
          pattern="[6-9][0-9]{9}"
          maxLength={10}
        />
      </label>
      <AreaPicker
        districtCode={districtCode}
        blockCode={blockCode}
        onChange={(district, block) => {
          setDistrictCode(district)
          setBlockCode(block)
        }}
      />
      <label className="field">
        <span>{text.register.abhaAddress}</span>
        <input name="abhaAddress" maxLength={80} placeholder="name@sbx" />
      </label>
      {error && <ErrorMessage error={error} />}
      <button className="button button-primary" disabled={saving || !blockCode}>
        {text.register.submit}
      </button>
    </form>
  )
}
