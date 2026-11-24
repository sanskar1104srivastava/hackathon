# Backend

Python 3.12 on AWS Lambda, in the same shape as `D:\production-backend`: FastAPI routed through Mangum,
container-image Lambdas, config from one Secrets Manager JSON, camelCase modules with `routes`,
`apiService` and `dbService` files. Dependencies are managed with uv.

## Layout

```
common/            shared services: settings, DynamoDB, errors, Claude, Deepgram, Sahai (ABDM), WhatsApp
modules/
  appApi/          Lambda entry point for the HTTP API (all routers)
  followUpWorker/  Lambda entry point for the daily schedule
  screening/       WHO z-scores, RBSK check catalogue, colour rules, AI checks, screening API
  children/        registration and child records
  referrals/       referral card, arrival, diagnosis and care plan, ABDM records request
  homePlan/        home activities, weekly progress, the parent page API
  alerts/          ASHA task list
  abdmBridge/      ABHA care-context linking (M2) and records pull (M3) through Sahai, webhook
  parentChannel/   status endpoint for the calling agent and callback requests
  dashboard/       running totals by district and block
  demo/            demo clock and "skip a week"
  geo/             UP districts, blocks and referral facilities
data/
  who/             WHO LMS growth tables (WHO anthro and anthroplus on GitHub)
  rules/           RBSK 2.0 check catalogue, home activities
  geo/             UP districts and blocks from the Local Government Directory
deploy/            module registry, DynamoDB table definition, IAM policies, deploy.ps1
scripts/           local table creation, synthetic data seeding
tests/             rules and growth tests, full API journey on mocked DynamoDB
```

## Design rule

Rules decide the colour; AI only supplies evidence. Claude reads photos, video frames and device displays
and answers seen, not seen or unsure. Unsure always refers the child. The app never states a diagnosis.

## Deploy (dev)

1. Create the Secrets Manager secret `up4ds/backend/dev` in `ap-south-1` with the keys in `.env.example`
   (`anthropicApiKey`, `deepgramApiKey`, `sahaiBaseUrl`, `sahaiApiKey`, `sahaiWebhookSecret`, `abdmHipId`,
   `abdmHiuId`, `whatsAppAccessToken`, `whatsAppPhoneNumberId`, `parentChannelToken`, `appBaseUrl`, `corsOrigins`).
2. Start Docker, then run `powershell -ExecutionPolicy Bypass -File deploy/deploy.ps1 -Environment dev`.
   It creates the table, role, ECR repository, both Lambdas, the HTTP API and the daily schedule.
3. Register the printed API URL plus `/v1/abdm/webhook` as this app's webhook in Sahai
   (`PUT /v1/webhook-endpoint`).
