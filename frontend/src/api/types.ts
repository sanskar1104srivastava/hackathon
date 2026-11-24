/** Shapes returned and accepted by the backend (`backend/modules/*`). */

export type Colour = 'green' | 'yellow' | 'red'
export type Domain = 'defects' | 'deficiencies' | 'diseases' | 'development'
export type Sex = 'male' | 'female'
export type Setting = 'facility' | 'home' | 'anganwadi' | 'school'
export type AiOutcome = 'seen' | 'notSeen' | 'unsure'
export type Device = 'weighingScale' | 'muacTape' | 'haemoglobinMeter'
export type CheckMethod =
  'measurement' | 'photo' | 'video' | 'voice' | 'milestone' | 'mchat' | 'question' | 'task'

export interface Block {
  blockCode: number
  blockName: string
}

export interface District {
  districtCode: number
  districtName: string
  blocks: Block[]
}

export interface Facility {
  facilityId: string
  name: string
  type: 'deic' | 'districtHospital'
  districtCode: number
  districtName: string
}

export interface Child {
  childId: string
  name: string
  sex: Sex
  dateOfBirth: string
  guardianName: string
  guardianPhone: string
  districtCode: number
  districtName: string
  blockCode: number
  blockName: string
  abhaAddress?: string | null
  parentLinkPath?: string
}

export interface NewChild {
  name: string
  sex: Sex
  dateOfBirth: string
  guardianName: string
  guardianPhone: string
  districtCode: number
  blockCode: number
  abhaAddress?: string
}

export interface Check {
  id: string
  domain: Domain
  method: CheckMethod
  labelEn: string
  labelHi: string
  promptHi: string
  device?: Device | null
  dueByMonths?: number | null
}

export interface PictureCard {
  id: string
  symbol: string
  wordHi: string
}

export interface CheckList {
  version: string
  checks: Check[]
  pictureCards: PictureCard[]
}

export interface Measurements {
  weightKg?: number
  heightCm?: number
  muacCm?: number
  haemoglobinGdl?: number
}

export interface AiObservation {
  checkId: string
  outcome: AiOutcome
  reasonHi: string
}

export interface ScreeningInput {
  screeningId: string
  setting: Setting
  screenedAt: string
  workerId: string
  consentGiven: boolean
  measurements: Measurements
  answers: Record<string, boolean>
  aiObservations: AiObservation[]
  speech: { shownCount: number; namedCount: number } | null
  tasks: { checkId: string; passed: boolean }[]
}

export interface Finding {
  checkId: string
  domain: Domain
  colour: Colour
  noteHi: string
  noteEn: string
}

export interface DomainResult {
  colour: Colour
  findings: Finding[]
  adviceHi: string
}

export interface ScreeningOutcome {
  overall: Colour
  domains: Record<Domain, DomainResult>
  growth: Record<string, number | null>
  nextSteps: ('referral' | 'homePlan')[]
}

export interface Screening {
  screeningId: string
  screenedAt: string
  ageMonths: number
  outcome: ScreeningOutcome
}

export interface CarePlan {
  careInstructionsHi: string
  medicines: { name: string; scheduleHi: string }[]
  checkupDates: string[]
  therapyDates: string[]
}

export type ReferralStatus = 'sent' | 'reached' | 'underTreatment'

export interface Referral {
  referralId: string
  childId: string
  childName: string
  screeningId: string
  facilityId: string
  facilityName: string
  reasonsHi: string[]
  reasonsEn: string[]
  status: ReferralStatus
  createdAt: string
  reachedAt?: string
  doctorName?: string
  diagnosisText?: string
  carePlan?: CarePlan
  recordsStatus?: string
}

export interface Activity {
  id: string
  focus: string
  checkMethod: 'voice' | 'photo' | 'video' | 'none'
  titleHi: string
  stepsHi: string
}

export interface HomePlan {
  focusAreas: string[]
  stage: number
  noImprovementWeeks?: number
}

export interface Alert {
  alertId: string
  childId: string
  childName: string
  guardianPhone: string
  blockName: string
  kind: 'noImprovement' | 'referralNotReached' | 'callbackRequested'
  messageHi: string
  createdAt: string
}

export interface ChildDetail {
  child: Child
  screenings: Screening[]
  referrals: Referral[]
  alerts: Alert[]
  homePlan: HomePlan | null
}

export interface ScreeningResult {
  screening: Screening
  duplicate: boolean
  referral?: Referral | null
  homePlan?: HomePlan | null
}

export interface SignCheckResult {
  outcome: AiOutcome
  reasonHi: string
  imageQualityOk: boolean
}

export interface DeviceReadingResult {
  readable: boolean
  value: number | null
  unit: 'kg' | 'cm' | 'g/dL'
}

export interface SpeechCheckResult {
  transcript: string
  namedCardIds: string[]
  shownCount: number
  namedCount: number
}

export const COUNTER_KEYS = [
  'screened',
  'flaggedDefects',
  'flaggedDeficiencies',
  'flaggedDiseases',
  'flaggedDevelopment',
  'referred',
  'reached',
  'homePlans',
  'improving',
  'alerts',
] as const

export type CounterKey = (typeof COUNTER_KEYS)[number]

export type DashboardRow = Record<CounterKey, number> & { code: number; name: string }

export interface DashboardSummary {
  level: 'state' | 'district'
  totals: Record<CounterKey, number>
  rows: DashboardRow[]
}

export interface ParentView {
  child: Pick<Child, 'childId' | 'name' | 'sex' | 'dateOfBirth'>
  latestResult: { screenedAt: string; outcome: ScreeningOutcome } | null
  referral: Referral | null
  homePlan: (HomePlan & { todaysActivities: Activity[] }) | null
}
