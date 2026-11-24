import { useState, type FormEvent } from 'react'
import type { CarePlan } from '../../api/types'
import { text } from '../../i18n/hi'

export interface DiagnosisInput {
  doctorName: string
  diagnosisText: string
  carePlan: CarePlan
}

/** The doctor's part of the referral card. Saving it starts the family's treatment reminders (UC-7). */
export function DiagnosisForm({ onSave }: { onSave: (input: DiagnosisInput) => Promise<void> }) {
  const [saving, setSaving] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const field = (name: string) => String(form.get(name) ?? '').trim()
    const medicineName = field('medicineName')
    setSaving(true)
    try {
      await onSave({
        doctorName: field('doctorName'),
        diagnosisText: field('diagnosisText'),
        carePlan: {
          careInstructionsHi: field('careInstructionsHi'),
          medicines: medicineName
            ? [{ name: medicineName, scheduleHi: field('medicineSchedule') || '-' }]
            : [],
          checkupDates: field('checkupDate') ? [field('checkupDate')] : [],
          therapyDates: field('therapyDate') ? [field('therapyDate')] : [],
        },
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="card stack" onSubmit={submit}>
      <h2>{text.doctor.diagnosisTitle}</h2>
      <label className="field">
        <span>{text.doctor.doctorName}</span>
        <input name="doctorName" required maxLength={80} />
      </label>
      <label className="field">
        <span>{text.doctor.diagnosis}</span>
        <textarea name="diagnosisText" required maxLength={500} rows={3} />
      </label>
      <label className="field">
        <span>{text.doctor.careInstructions}</span>
        <textarea name="careInstructionsHi" maxLength={600} rows={3} />
      </label>
      <div className="row wrap">
        <label className="field grow">
          <span>{text.doctor.medicineName}</span>
          <input name="medicineName" maxLength={80} />
        </label>
        <label className="field grow">
          <span>{text.doctor.medicineSchedule}</span>
          <input name="medicineSchedule" maxLength={120} />
        </label>
      </div>
      <div className="row wrap">
        <label className="field grow">
          <span>{text.doctor.checkupDate}</span>
          <input name="checkupDate" type="date" />
        </label>
        <label className="field grow">
          <span>{text.doctor.therapyDate}</span>
          <input name="therapyDate" type="date" />
        </label>
      </div>
      <button className="button button-primary" disabled={saving}>
        {text.doctor.saveDiagnosis}
      </button>
    </form>
  )
}
