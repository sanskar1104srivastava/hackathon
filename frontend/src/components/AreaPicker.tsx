import { api } from '../api/endpoints'
import type { District } from '../api/types'
import { useAsync } from '../hooks/useAsync'
import { text } from '../i18n/hi'
import { ErrorMessage } from './StatusViews'

interface AreaPickerProps {
  districtCode: number | null
  blockCode: number | null
  onChange: (districtCode: number, blockCode: number | null) => void
  showBlock?: boolean
}

export function AreaPicker({
  districtCode,
  blockCode,
  onChange,
  showBlock = true,
}: AreaPickerProps) {
  const districts = useAsync(api.getDistricts, [])
  if (districts.error) return <ErrorMessage error={districts.error} onRetry={districts.reload} />

  const district: District | undefined = districts.data?.find(
    (d) => d.districtCode === districtCode,
  )
  return (
    <div className="row wrap">
      <label className="field grow">
        <span>{text.area.district}</span>
        <select
          value={districtCode ?? ''}
          onChange={(event) => onChange(Number(event.target.value), null)}
          disabled={!districts.data}
        >
          <option value="" disabled>
            {text.area.chooseDistrict}
          </option>
          {districts.data?.map((d) => (
            <option key={d.districtCode} value={d.districtCode}>
              {d.districtName}
            </option>
          ))}
        </select>
      </label>
      {showBlock && (
        <label className="field grow">
          <span>{text.area.block}</span>
          <select
            value={blockCode ?? ''}
            onChange={(event) => onChange(districtCode!, Number(event.target.value))}
            disabled={!district}
          >
            <option value="" disabled>
              {text.area.chooseBlock}
            </option>
            {district?.blocks.map((block) => (
              <option key={block.blockCode} value={block.blockCode}>
                {block.blockName}
              </option>
            ))}
          </select>
        </label>
      )}
    </div>
  )
}
