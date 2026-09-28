# Document Extraction

Extract user-defined fields from PDF documents using a configurable vision/multimodal LLM.
Upload a PDF, describe the fields you want (name, description, type, required), run extraction,
and review results with confidence scores, page numbers and source evidence — then download as
JSON or CSV.

```
Configure Vision Model → Upload PDF → Define Fields → Run Extraction → View Results → Download
```

## Architecture

```
frontend/            React + TypeScript + Vite + Tailwind CSS (two pages: Settings, Document Extraction)
backend/
  app/
    api/             FastAPI routers (thin — validation + wiring only)
    services/        Application logic: document_service, extraction_service, settings_service
    pdf/              PDFService — PyMuPDF-based validation/rendering, independent of any provider
    vision/           VisionModelProvider abstraction + OpenAICompatibleProvider + prompt builder
    storage/          ObjectStorage abstraction + MinIOObjectStorage
    models/           SQLAlchemy 2.x models (Document, Extraction, ExtractionField, ExtractionResult, ...)
    schemas/          Pydantic request/response models
  alembic/            Migrations
  tests/              pytest suite (unit + API + persistence integration)
```

Design principles carried through the codebase:

- **PDF processing is isolated from extraction logic.** `PDFService` only knows about PyMuPDF; it
  has no idea a vision model exists.
- **The vision model is pluggable.** `VisionModelProvider` is an abstract interface;
  `OpenAICompatibleProvider` implements it against any OpenAI-compatible `/chat/completions` API
  (OpenAI, vLLM, DKubeX SecureLLM, ...). No model-specific logic lives in the extraction service.
- **Object storage is pluggable.** Services depend on the `ObjectStorage` interface
  (`upload`/`download`/`delete`/`exists`/`generate_presigned_url`), not on a MinIO client directly.
- **The original PDF binary lives only in object storage.** PostgreSQL holds metadata, extraction
  runs, field definitions, results, confidence, evidence and validation/edit state — never PDF
  bytes.
- **Extractions are append-only.** Every "Extract Again" creates a new `Extraction` row; previous
  runs are never overwritten.

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS v4 |
| Backend | Python, FastAPI, Pydantic, Uvicorn |
| PDF processing | PyMuPDF (`fitz`) |
| Object storage | MinIO (S3 API) via the `minio` SDK |
| Database | PostgreSQL |
| ORM / migrations | SQLAlchemy 2.x (async, `asyncpg`) + Alembic |

## Installation

Requires Python 3.12+, Node 20+, and a PostgreSQL server + an S3-API-compatible object store
(MinIO in production) reachable over the network. No Docker is required or used by the app
itself.

```bash
# Backend
cd backend
python3 -m venv ../.venv && source ../.venv/bin/activate
pip install -r requirements.txt        # add requirements-dev.txt for tests/lint/type-check
cp .env.example .env                   # edit DATABASE_URL / MINIO_* / MODEL_* as needed
alembic upgrade head

# Frontend
cd ../frontend
npm install
```

### A note on the MinIO dependency in this environment

`MinIOObjectStorage` is written against the plain S3 API via the official `minio` Python SDK —
it has no MinIO-specific behavior. The public MinIO server binaries and container images were
discontinued from free distribution after this project was built, so local development here runs
the storage layer against [`moto`](https://github.com/getmoto/moto)'s standalone S3-API mock
server (`python -m moto.server`) instead of a real MinIO instance. Pointing `MINIO_ENDPOINT` /
`MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` at a real MinIO (or any S3-compatible) deployment requires
no code change — this was verified directly against the `minio` SDK's presigned URLs, uploads,
downloads and deletes.

PostgreSQL is a genuine local PostgreSQL 18 server (installed via apt), not a substitute.

## Running

```bash
# Backend (from backend/, with the venv active)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (from frontend/, separate terminal)
npm run dev
```

The Vite dev server proxies `/api` to the backend (see `vite.config.ts`, `BACKEND_PORT` env var,
default `8010`). Ports are configurable via `--port` / `PORT`.

For a single-process deployment (e.g. as a DKubeX workspace app tile), build the frontend first
and let the backend serve the static bundle alongside the API:

```bash
cd frontend && npm run build   # writes frontend/dist
cd ../backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`app/main.py` mounts `frontend/dist` at `/` when that directory exists. `run.sh` at the project
root does exactly this, plus starting the local PostgreSQL cluster and the moto storage mock if
they are not already running, and is what `d3x app create` / this workspace's tile runs.

### Base-path awareness

The frontend and backend both honor `DKUBEX_BASE_PATH` when running as a platform app tile served
under a path prefix rather than at `/` (Vite's `base` config at build time; a small ASGI
middleware in `app/main.py` sets `scope["root_path"]` at request time, since this platform's
nginx forwards the full, unstripped request path rather than stripping the prefix itself). Neither
matters for plain local development, where the variable is simply unset.

## Model configuration

Open **Settings** (the default page). Choose a provider:

- **OpenAI Compatible** — point at any OpenAI-compatible vision endpoint (OpenAI, vLLM, ...).
- **DKubeX (SecureLLM)** — when the Base URL field is empty, it auto-fills with
  `https://<current-host>/securellm/v1` derived from `window.location`, so the same build works
  unmodified on any DKubeX deployment.

Both providers use the same `OpenAICompatibleProvider` backend. Fill in the API key, model name
(type freely, or click **Fetch Models** to populate a dropdown from `{base_url}/models`),
temperature, max tokens, timeout and PDF rendering DPI, then **Save Settings** and **Test
Connection**. Settings persist to a JSON file (`SETTINGS_FILE`, `0600` permissions) so they
survive a restart; the API key is never echoed back to the browser.

## API overview

```
GET    /api/health

GET    /api/settings/model
PUT    /api/settings/model
POST   /api/settings/model/test
POST   /api/settings/model/models

POST   /api/documents/upload
GET    /api/documents/{document_id}
GET    /api/documents/{document_id}/pages/{page_num}
GET    /api/documents/{document_id}/download
DELETE /api/documents/{document_id}

POST   /api/extractions
GET    /api/extractions/{extraction_id}
GET    /api/extractions/{extraction_id}/result
GET    /api/extractions/{extraction_id}/download/json
GET    /api/extractions/{extraction_id}/download/csv
```

Interactive docs at `/docs` (FastAPI/Swagger) once the backend is running.

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
createdb document_extractor_test   # once; conftest.py runs Alembic against it automatically
pytest -q
```

No real vision-model API key is required: `respx` mocks the HTTP calls to the (OpenAI-compatible)
vision endpoint, and PDFs are generated synthetically with PyMuPDF. Coverage includes:

- `PDFService` (valid/invalid/empty/multi-page PDFs, page rendering, DPI)
- The prompt builder and the response schema validator (valid / invalid / markdown-fenced JSON /
  missing fields / out-of-range confidence)
- `OpenAICompatibleProvider` (success, 401, 429, timeout, malformed response)
- Every API endpoint (upload, settings, test-connection, extraction, downloads)
- A full persistence integration test: upload → verify in Postgres+MinIO → extract → simulate a
  backend restart → verify everything survived → Extract Again → verify the first run is intact

Lint / type-check:

```bash
ruff check app tests
mypy app --ignore-missing-imports
```

Frontend build (`tsc -b && vite build`) fails on type errors by design; there is no separate
`tsc --noEmit` step needed.

## Packaging as a DKubeX platform app

`charts/docextract/` is a Helm chart following the DKubeX app standard, alongside `Dockerfile`
and `docker-entrypoint.sh` at the project root which build the single container it deploys
(backend + the frontend's static build in one image, per `app/main.py`'s static-file mount).

```bash
docker build -t <registry>/docextract:<tag> .
docker push <registry>/docextract:<tag>
helm install docextract charts/docextract \
  --set image.repository=<registry>/docextract --set image.tag=<tag>
```

What differs from the plain "Running" section above:

- **`postgres` and `minio` are declared dependencies** (see `Chart.yaml`'s `dkubex.dependencies`),
  so the platform auto-provisions a database and bucket and injects `postgres.db_url` /
  `minio.*` as Helm values — no local PostgreSQL or storage substitute needed. The deployment
  template rewrites the injected bare `postgresql://` URL to `postgresql+asyncpg://` and splits
  the injected MinIO endpoint URL into a bare `host:port` plus a secure flag, since that's what
  this app's config (`app/config.py`) and the `minio` SDK expect.
- **Identity comes from the gateway, not a login screen.** `PLATFORM_AUTH_REQUIRED=true` in the
  chart's Deployment turns on a small ASGI middleware (`app/main.py`) that 401s any request
  without `X-Auth-Request-User` — except `/api/health`, which kubelet probes reach directly and
  never carry that header. This is off by default (`false`) so plain local dev and the
  workspace-tile deployment (neither behind that gateway) are unaffected.
- **The base path is handled the same way as the workspace-tile deployment** — Vite bakes
  `/docextract` into the frontend build (fixed, since the chart's `DKUBEX_BASE_PATH` is
  `/<chart name>` for the common case of no `nameOverride`), and `_RootPathMiddleware` in
  `app/main.py` sets `scope["root_path"]` at request time rather than uvicorn's `--root-path`,
  because this platform's Gateway `HTTPRoute` (like the workspace's nginx) forwards the full,
  unstripped request path.
- **Settings persist to a small PVC** (`storage.storageClass`/`.size`, default 1Gi) mounted at
  `SETTINGS_FILE`'s directory, so the Settings page survives a pod reschedule, not just an
  in-process restart.
- Validate the chart with `python3 <package-app skill dir>/scripts/validate_chart.py
  charts/docextract` before publishing — it renders the chart with `helm template` and checks
  routing, resource units and the annotation schema.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| "The Vision Model rejected the API key (401)" | Wrong/expired API key in Settings |
| "The Vision Model is rate-limiting requests (429)" | Retry after a pause, or lower request rate |
| "The Vision Model did not return valid structured data" | Model ignored the JSON-only instruction; check the truncated raw response snippet in the error detail, and consider lowering temperature |
| Upload rejected with "Only PDF documents are supported." | Non-PDF file, or wrong `Content-Type` |
| Extract button disabled | No PDF uploaded, no fields defined, or the Vision Model isn't configured yet (Settings) |
| 502 from the app tile | The server isn't running — `run.sh` must be started and left running; nothing supervises it |
