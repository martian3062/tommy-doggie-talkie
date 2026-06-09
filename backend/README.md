# Dog Translator Backend

FastAPI backend for the Dog Translator app. It supports:

- Supabase-first storage/database/auth integration once credentials are provided.
- SQLite fallback for local development.
- Video upload analysis jobs.
- Baseline multimodal behavior interpretation with optional heavy ML adapters.
- Feedback and per-dog habit summaries.

## Local Setup

```powershell
cd backend
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install ".[dev]"
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Optional ML packages:

```powershell
python -m pip install ".[ml]"
```

## API

- `POST /api/v1/dogs`
- `GET /api/v1/dogs`
- `POST /api/v1/analysis-jobs`
- `GET /api/v1/analysis-jobs/{job_id}`
- `GET /api/v1/analysis-jobs/{job_id}/result`
- `POST /api/v1/analysis-jobs/{job_id}/feedback`
- `GET /api/v1/dogs/{dog_id}/habits`
- `POST /api/v1/dogs/{dog_id}/personal-model/retrain`

Use `X-User-Id` during local testing to simulate a Supabase user id.
