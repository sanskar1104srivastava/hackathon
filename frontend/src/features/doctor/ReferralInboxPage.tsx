import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/endpoints'
import { AreaPicker } from '../../components/AreaPicker'
import { ErrorMessage, Loading } from '../../components/StatusViews'
import { useAsync } from '../../hooks/useAsync'
import { formatDate } from '../../lib/dates'
import { preferences } from '../../lib/preferences'
import { referralStatusLabels, text } from '../../i18n/hi'

const districtOf = (facilityId: string | null) =>
  facilityId ? Number(facilityId.split('-')[1]) : null

export function ReferralInboxPage() {
  const [facilityId, setFacilityId] = useState<string | null>(preferences.getFacilityId())
  const [districtCode, setDistrictCode] = useState<number | null>(districtOf(facilityId))
  const facilities = useAsync(
    () => (districtCode ? api.getFacilities(districtCode) : Promise.resolve([])),
    [districtCode],
  )
  const referrals = useAsync(
    () => (facilityId ? api.listFacilityReferrals(facilityId) : Promise.resolve([])),
    [facilityId],
  )

  function chooseFacility(id: string) {
    setFacilityId(id)
    preferences.setFacilityId(id)
  }

  return (
    <div className="stack">
      <h1>{text.doctor.title}</h1>
      <AreaPicker
        districtCode={districtCode}
        blockCode={null}
        showBlock={false}
        onChange={(district) => {
          setDistrictCode(district)
          setFacilityId(null)
        }}
      />
      {facilities.data && facilities.data.length > 0 && (
        <label className="field">
          <span>{text.doctor.facility}</span>
          <select value={facilityId ?? ''} onChange={(event) => chooseFacility(event.target.value)}>
            <option value="" disabled>
              {text.doctor.facility}
            </option>
            {facilities.data.map((facility) => (
              <option key={facility.facilityId} value={facility.facilityId}>
                {facility.name}
              </option>
            ))}
          </select>
        </label>
      )}
      {referrals.loading && facilityId && <Loading />}
      {referrals.error && <ErrorMessage error={referrals.error} onRetry={referrals.reload} />}
      {facilityId && referrals.data?.length === 0 && <p className="muted">{text.doctor.empty}</p>}
      <ul className="list">
        {referrals.data?.map((referral) => (
          <li key={referral.referralId}>
            <Link
              to={`/doctor/children/${referral.childId}/referrals/${referral.referralId}`}
              className="list-item"
            >
              <span className="row between">
                <strong>{referral.childName}</strong>
                <span className="pill">{referralStatusLabels[referral.status]}</span>
              </span>
              <span className="muted">
                {formatDate(referral.createdAt)} · {referral.reasonsEn.join('; ')}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
