# Child Health Screening Across the 4Ds (POC)

Proof of concept for the UP AI Mission challenge: a frontline worker screens a child for the four Ds
(defects at birth, deficiencies, diseases, developmental delays), the family gets a plain-Hindi result,
red results are referred and tracked through ABDM, yellow results get a home activity plan on WhatsApp,
and the Health Department sees the totals.

All child records are synthetic.

```
backend/    Python on AWS Lambda (FastAPI + Mangum, container images), DynamoDB, Claude, Deepgram
frontend/   Vite + React + TypeScript web app: field worker, doctor, department, parent pages
*.pdf       App flow brief and POC build plan
```

## How the pieces connect

| Part | Where | Notes |
|---|---|---|
| Field app, doctor view, dashboard, parent page | `frontend/` | One web app, roles picked on the home page (POC, no login) |
| HTTP API | `backend/modules/appApi` | One Lambda behind an API Gateway HTTP API |
| Daily follow-up | `backend/modules/followUpWorker` | Same image, run daily by EventBridge |
| ABDM (ABHA, HIP, HIU) | `D:\production-backend` (Sahai) | Called over HTTPS as a Sahai customer; events come back on `/v1/abdm/webhook` |
| Calls from parents | Team calling agent | Uses `GET /v1/parent-channel/status` as a tool |
| WhatsApp | Meta Cloud API | Same API as the team's existing WhatsApp module |

## Run locally (no AWS needed)

Terminal 1, local DynamoDB:

```powershell
cd backend
uv sync
$env:AWS_ACCESS_KEY_ID="local"; $env:AWS_SECRET_ACCESS_KEY="local"; $env:AWS_DEFAULT_REGION="ap-south-1"
uv run moto_server -p 5000
```

Terminal 2, API (`backend/.env` points at the local table; copy from `.env.example`):

```powershell
cd backend
$env:AWS_ACCESS_KEY_ID="local"; $env:AWS_SECRET_ACCESS_KEY="local"; $env:AWS_DEFAULT_REGION="ap-south-1"
uv run python -m scripts.createLocalTable
uv run python -m scripts.seedSyntheticData --per-district 3
uv run uvicorn modules.appApi.main:app --port 8000
```

Terminal 3, web app:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Photo, video, device-reading and speech AI need `anthropicApiKey` and
`deepgramApiKey` in `backend/.env`; without them those steps fall back to the worker's own answer.

## Checks

```powershell
cd backend;  uv run python -m unittest discover -s tests -t .;  uv run ruff check .
cd frontend; npm run lint;  npm run format:check;  npm run build
```
