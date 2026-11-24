import { apiRequest, postOrQueue } from './client'
import type {
  Alert,
  CarePlan,
  Child,
  ChildDetail,
  CheckList,
  DashboardSummary,
  DeviceReadingResult,
  Device,
  District,
  Facility,
  NewChild,
  ParentView,
  Referral,
  ScreeningInput,
  ScreeningResult,
  SignCheckResult,
  SpeechCheckResult,
} from './types'

const query = (params: Record<string, string | number | undefined>) =>
  new URLSearchParams(
    Object.entries(params)
      .filter(([, value]) => value !== undefined)
      .map(([key, value]) => [key, String(value)]),
  ).toString()

export const api = {
  getDistricts: () => apiRequest<District[]>('GET', '/v1/districts'),
  getFacilities: (districtCode: number) =>
    apiRequest<Facility[]>('GET', `/v1/facilities?${query({ districtCode })}`),

  registerChild: (child: NewChild) => apiRequest<Child>('POST', '/v1/children', child),
  listChildren: (districtCode: number, blockCode?: number) =>
    apiRequest<Child[]>('GET', `/v1/children?${query({ districtCode, blockCode })}`),
  getChildDetail: (childId: string) => apiRequest<ChildDetail>('GET', `/v1/children/${childId}`),

  getChecks: (ageMonths: number) =>
    apiRequest<CheckList>('GET', `/v1/checks?${query({ ageMonths: ageMonths.toFixed(1) })}`),
  submitScreening: (childId: string, screening: ScreeningInput) =>
    postOrQueue<ScreeningResult>(`/v1/children/${childId}/screenings`, screening),

  checkSign: (checkId: string, childAgeMonths: number, imagesBase64: string[]) =>
    apiRequest<SignCheckResult>('POST', '/v1/ai/sign-check', {
      checkId,
      childAgeMonths,
      imagesBase64,
    }),
  readDevice: (device: Device, imageBase64: string) =>
    apiRequest<DeviceReadingResult>('POST', '/v1/ai/device-reading', { device, imageBase64 }),
  checkSpeech: (audioBase64: string, mimeType: string, cardIds: string[]) =>
    apiRequest<SpeechCheckResult>('POST', '/v1/ai/speech-check', {
      audioBase64,
      mimeType,
      cardIds,
    }),

  listFacilityReferrals: (facilityId: string) =>
    apiRequest<Referral[]>('GET', `/v1/facilities/${facilityId}/referrals`),
  markArrived: (childId: string, referralId: string) =>
    apiRequest<Referral>('POST', `/v1/children/${childId}/referrals/${referralId}/arrival`),
  recordDiagnosis: (
    childId: string,
    referralId: string,
    diagnosis: { doctorName: string; diagnosisText: string; carePlan: CarePlan },
  ) =>
    apiRequest<Referral>(
      'POST',
      `/v1/children/${childId}/referrals/${referralId}/diagnosis`,
      diagnosis,
    ),
  requestRecords: (
    childId: string,
    referralId: string,
    requester: { requesterName: string; requesterId: string },
  ) =>
    apiRequest<Referral>(
      'POST',
      `/v1/children/${childId}/referrals/${referralId}/records-request`,
      requester,
    ),
  getRecords: (childId: string, referralId: string) =>
    apiRequest<{ recordsStatus: string; records?: unknown }>(
      'GET',
      `/v1/children/${childId}/referrals/${referralId}/records`,
    ),

  listAlerts: (districtCode: number) =>
    apiRequest<Alert[]>('GET', `/v1/alerts?${query({ districtCode })}`),
  closeAlert: (childId: string, alertId: string) =>
    apiRequest<Alert>('POST', `/v1/alerts/${childId}/${alertId}/close`),

  getDashboard: (districtCode?: number) =>
    apiRequest<DashboardSummary>('GET', `/v1/dashboard/summary?${query({ districtCode })}`),
  skipWeek: () => apiRequest<{ offsetDays: number }>('POST', '/v1/demo/skip-week'),

  getParentView: (childId: string, token: string) =>
    apiRequest<ParentView>('GET', `/v1/parent/${childId}?${query({ token })}`),
  recordProgress: (childId: string, token: string, activityId: string, score: number) =>
    apiRequest<{ weekPoints: number }>(
      'POST',
      `/v1/parent/${childId}/progress?${query({ token })}`,
      {
        activityId,
        score,
      },
    ),
}
