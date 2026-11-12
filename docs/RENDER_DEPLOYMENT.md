# Render Free: temporary FairModel demonstration

## Existing hosted preview: judge access

The owner-deployed preview is [fairmodel.onrender.com](https://fairmodel.onrender.com). The owner explicitly authorized publishing its shared website username/password for judging; copy the current values from [README — Hosted demo login](../README.md#hosted-demo-login). Enter them in the browser's login prompt, without quotation marks. This is website access, not a PayPal buyer login or provider API credential. The provided login was documented, not independently authenticated by this update.

This is now intentionally shared demonstration access: anyone with it can switch both personas, inspect hosted records and use enabled AI features. Use fictional/authorized materials only. Keep all provider secrets private and PayPal draft/send disabled. For a new deployment with confidential data, generate separate access credentials and do not reuse or publish the shared judging password. The fresh-deployment instructions below describe that separate setup.

This deployment packages the existing Next.js frontend, Python 3.12 backend and
FFmpeg into **one Docker web service**. Only Next.js listens publicly on Render's
`PORT`; FastAPI listens on `127.0.0.1:8000` inside the same container. The existing
same-origin API proxy and application workflows remain in place.

## Read this before deploying

- **This is an ephemeral demo, not a durable production deployment.** Render Free
  cannot attach a persistent disk. SQLite, uploaded contracts, reference samples,
  generated recordings, approvals and local invoice/event records disappear on
  restart, redeploy or idle spin-down. Free services spin down after 15 idle
  minutes and can take around a minute to wake. See [Render Free limits](https://render.com/docs/free).
- This creates a **fresh cloud database**. Your Windows database, uploaded files,
  existing licenses, consents and financial history stay on your computer. They
  are never added to the image, uploaded, reset or overwritten by these files.
  There is no automatic import of private data or Windows absolute file paths.
- **PayPal draft creation and sending are deliberately disabled** in this free
  deployment. Losing durable operation intents makes financial writes unsuitable
  here. The launcher refuses to start if these flags are enabled. You can inspect
  integration configuration and run the existing explicit read-only Sandbox
  diagnostics, or select `PAYMENT_PROVIDER=mock` for clearly simulated invoices.
  Continue your genuine invoice/payment demonstration locally, where its history
  is preserved. No production PayPal endpoints are used.
- Provider usage is separate from Render hosting: Gemini/Groq/Fish requests can
  have their own quota/terms/costs. Deployment and health checks do not run them.
- Access uses a shared password for invited judges, **not individual production
  authentication**. Anyone given that password can switch both demo personas and
  access this hosted demonstration's records and enabled AI features. Share only
  with trusted reviewers. Do not collect real private material in this temporary
  instance. Keep provider generation disabled until you deliberately configure it.
- A 512 MB free instance is resource constrained. Audio conversion and concurrent
  requests may exhaust memory. Cloud runtime/build success must be checked in
  Render; local tests do not prove those limits are sufficient.
- Keep your working local copy for the recorded demo and durable financial proof.

## Deploy from GitHub

1. Commit and push the prepared source **only after the owner authorizes the push**.
   Required source includes `Dockerfile`, `.dockerignore`, `render.yaml`, `deploy/`,
   frontend changes and the previously ignored Postman download route. Never stage
   `.env`, databases, uploaded media, `tools/` or `.tmp/`.
2. Sign in at [Render Dashboard](https://dashboard.render.com/). Connect GitHub and
   grant access to the private **1805shahab/fairmodel** repository only.
3. Choose **New > Blueprint**, select the repository and the branch containing this
   code. Render should discover the root `render.yaml`.
4. Review the plan before applying: **one Free Docker web service**, no database
   service, no persistent disk, no paid instance. Do not upgrade or create paid
   resources for this free-only option. Review workspace usage/spend settings too:
   Render's free compute still has bandwidth/build usage limits.
5. Create the Blueprint. Wait for Docker build and deployment. `healthCheckPath`
   is `/healthz`; it checks both app processes without credentials or AI calls.
6. In the service's **Environment** tab, inspect the generated
   `DEMO_ACCESS_PASSWORD` privately. Username is `fairmodel`. Do not paste the
   password into chat, commit it or put it in the URL. Open the service's actual
   `https://...onrender.com` URL and enter these values in the browser sign-in box.
   For a private new deployment, share its credentials only with invited reviewers.
   The existing owner-authorized shared judging preview is the explicit exception
   documented above; never publish provider keys or account passwords with it.
7. To enable real AI, add the backend variables below in Render Environment and
   save/redeploy. Enter values privately from your own configuration. This
   redeploy loses cloud demonstration data, so configure keys **before** uploads.
   Never upload `backend/.env` or add secrets as Docker build arguments.
8. Run the verification checklist below. There is no deployed URL until Render
   reports the actual service as Live. Auto-deploy is off; later deployments are
   deliberate, because they erase this demo's temporary records.

### Manual Web Service alternative

If you prefer **New > Web Service** instead of Blueprint:

| Setting | Value |
| --- | --- |
| Repository | `1805shahab/fairmodel` |
| Root Directory | **blank** (repository root) |
| Language | Docker |
| Dockerfile Path | `./Dockerfile` |
| Docker Build Context | `.` |
| Docker Command | **blank** (use the image CMD) |
| Instance | Free |
| Health Check Path | `/healthz` |
| Auto-Deploy | Off |

Add `DEMO_ACCESS_USER=fairmodel` and a randomly generated password of at least 24
characters under `DEMO_ACCESS_PASSWORD` **before creating the service**. Do not set
a custom build/start command, root directory `frontend`, or `APP_ENV=production`.
The backend deliberately remains in its supported demo mode.

## Runtime variables

The image already sets isolated temporary paths, demo mode, Sandbox-only selection,
disabled financial writes and the internal API URL. **Do not override these paths
or expose port 8000.** Secrets are loaded only at runtime by the backend.

| Variable | Purpose |
| --- | --- |
| `DEMO_ACCESS_USER` / `DEMO_ACCESS_PASSWORD` | Shared hosted-demo access; password at least 24 characters |
| `GEMINI_API_KEY` | Live contract extraction and advisory content analysis |
| `GEMINI_MODEL` | Optional supported model override; preserve your working model selection |
| `GROQ_API_KEY` | Live Whisper transcription |
| `GROQ_WHISPER_MODEL` | Defaults to `whisper-large-v3-turbo` |
| `FISH_API_KEY` | Optional Fish generation; never use a different paid model |
| `ENABLE_FISH_GENERATION` | Defaults false; Fish also requires `ENABLE_VOICE_GENERATION=true`, its own key and separate artist consent |
| `ENABLE_VOICE_GENERATION` | Defaults false; master generation opt-in for either provider; Gemini replication access remains provider-dependent |
| `GEMINI_TTS_MODEL` / `GEMINI_VOICE_REPLICATION_MODEL` | Existing supported requested models; never switch after an error |
| `PAYMENT_PROVIDER` | `paypal_sandbox` by default; `mock` explicitly selects simulation |
| `PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET` | Optional Sandbox OAuth/read-only diagnostics only on this free deployment |
| `PAYPAL_SANDBOX_MERCHANT_EMAIL` / `PAYPAL_SANDBOX_BUYER_EMAIL` | Your actual configured sandbox accounts, if running read-only checks |
| `PAYPAL_ALLOW_DRAFTS` / `PAYPAL_ALLOW_SENDING` | **Must remain false** on this ephemeral deployment |

Do not add buyer passwords, `NEXT_PUBLIC_` provider keys or real OAuth tokens.
`NEXT_PUBLIC_HOSTED_EPHEMERAL_DEMO` is only a nonsecret build-time storage notice.
The backend's private health response is not forwarded to anonymous visitors.
`/healthz` returns only `ok`/`unavailable` and performs no financial operation.

`FAIRMODEL_STANDALONE=true` is set only during the Docker frontend build. Ordinary
Windows builds and the existing PowerShell launch commands keep their normal
Next.js output; no change to your local start command is necessary.

Webhooks are not configured by this deployment. The shared access gate also blocks
unauthenticated webhook traffic. Do not register it as a payment webhook endpoint.

## Verification after Render says Live

1. Open `/healthz`: expect `{"status":"ok"}`. A failing API produces HTTP 503.
2. In a private browser window, `/dashboard` and `/api/backend/licenses` must ask
   for the demo password. Missing access configuration causes HTTP 503, not public
   access. Do not disable the gate to fix an incorrect password.
3. Sign in. Check landing, artist/studio switching, settings, AG Grid analytics
   and the Postman download. The temporary-storage notice must be visible.
4. Upload a **new authorized** contract/reference; extract/review/activate terms.
   Upload/generate a consented recording only through the existing explicit
   actions. Check actual FFprobe/VAD measurements and live provider provenance.
   No provider is called by startup, screenshots or the health probe.
5. Complete compliance/artist review/royalty calculation as usual. Use real measured
   duration; do not invent a value to fit a demo amount. Zero usage has no invoice.
6. For a purely simulated end-to-end invoice demonstration, explicitly choose mock
   before starting and keep every simulation label. Real Sandbox create/send is
   held on this free host; use your durable local application for that portion.
7. Download any evidence you need while the instance is still running. Never rely
   on these cloud records surviving an idle pause, process failure or redeploy.

## Local checks and optional container verification

```powershell
# From the FairModel repository root. No provider or payment requests.
.\backend\.venv\Scripts\python.exe -m pytest backend/tests deploy/tests -q
.\backend\.venv\Scripts\python.exe -m ruff check backend deploy
$env:Path = "$PWD\tools\node;$env:Path"
Push-Location frontend
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
Pop-Location
node .\scripts\test_render_access.cjs
```

If Docker is already installed, the optional build is `docker build -t fairmodel-render .`.
This downloads/builds dependencies but does not call AI or PayPal. Do not install
Docker or assume that this command was run merely because this guide includes it.
For a local container run, supply only a synthetic access username/password, leave
provider keys absent, and map `-p 10000:10000`. Stop it with Ctrl+C. The two-process
supervisor terminates both children on shutdown and exits if either fails.

## Moving beyond the free demonstration

Durable hosting needs a separate project milestone: paid persistent disk (single
SQLite instance) or validated database + object-storage migration, consistent
backup/restore, real authentication, payment reconciliation and an authorized
data migration. Do not upload a Windows SQLite file by itself: private file paths
and dependent evidence need a verified transfer. Do not silently substitute free
Postgres; this application's schema/settings currently support SQLite only.

Sources: [Render Docker deployment](https://render.com/docs/docker),
[Render Blueprint fields](https://render.com/docs/blueprint-spec),
[Free service limits](https://render.com/docs/free),
[Persistent disks](https://render.com/docs/disks).

## Preparation verification — November 12, 2026

- 384 Python tests passed: 370 application regressions plus 14 launcher checks.
- Backend/deployment Ruff, frontend TypeScript, ESLint, standalone generation and
  final ordinary production build passed. All 38 Edge browser regressions passed
  against isolated local records and mocked/explicit-fixture providers.
- Local hosted HTTP checks passed for missing configuration, missing/wrong/valid
  passwords, API protection, cross-site rejection, role switching, Postman download
  and healthy/unhealthy readiness. Blueprint YAML structure parsed locally.
- Backend application source and the Postman collection are unchanged. No `.env`
  values were displayed or copied; no live AI or financial request was performed.
- **Not verified:** Docker image build/runtime, Render account setup, actual cloud
  service, cloud provider connectivity or persistence. Docker CLI is installed but
  its engine was not running. These local checks do not prove a deployed service
  is live, fits the Free memory limit or retains records.
