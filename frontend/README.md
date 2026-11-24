# Frontend

Vite + React + TypeScript. One mobile-first web app in Hindi with four parts:

| Route | For | Use cases |
|---|---|---|
| `/field` | ASHA, anganwadi worker, Mobile Health Team | Register, guided screening, result, ASHA alerts (UC-1 to UC-4, UC-6) |
| `/doctor` | DEIC and hospital doctors | Referral inbox, arrival, diagnosis and care plan, ABDM records (UC-4, UC-7) |
| `/dashboard` | Health Department | Totals by district and block, demo "skip a week" (UC-8) |
| `/parent/:childId?token=` | Parents, from the QR code | Result, referral, today's home activities (UC-5) |

```
src/
  api/          types, fetch client, one function per backend endpoint
  offline/      offline copies of data and the queue of screenings waiting to be sent
  features/     pages, grouped by user (field, doctor, dashboard, parent, home)
  components/   shared UI
  hooks/        data loading, audio recording
  lib/          media compression, Hindi speech, dates, saved preferences
  i18n/hi.ts    all Hindi UI text
public/sw.js    keeps the app shell on the phone for offline use
```

Offline: opened child records and check lists are kept on the phone, finished screenings wait in a queue and
are sent when the network returns, and AI steps fall back to the worker's own answer. The colour result itself
is calculated by the backend, so an offline screening shows its result once it has synced.

Scripts: `npm run dev`, `npm run build`, `npm run lint`, `npm run format`, `npm run format:check`.
Set `VITE_API_BASE_URL` for a deployed build (see `.env.example`).
