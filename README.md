# tommy-doggie-talkie

# Dog Translator

Dog Translator is a React Native + FastAPI app that estimates probable dog behavior from uploaded videos, audio signals, context tags, and owner feedback.

The app intentionally presents behavior interpretations, not literal translations or veterinary diagnoses.

## What Is Implemented

- Expo React Native Android app scaffold.
- FastAPI backend with all planned API routes.
- SQLite 3 local fallback.
- Supabase-ready auth, database, and storage configuration.
- Direct video upload fallback when Supabase credentials are missing.
- Baseline ML fusion layer with optional YOLO adapter and declared Hugging Face model registry.
- Breed intelligence with breed profiles, optional breed detection, breed-aware behavior scoring, and health-watch cautions.
- Feedback loop and per-dog habit summaries.
- Backend tests for dog creation, upload, result retrieval, feedback, and habits.

## Repo Layout

```text
backend/   FastAPI API, SQLModel data layer, ML pipeline, tests
mobile/    Expo React Native Android app
supabase/  SQL schema and RLS starter policy
docs/      Model and implementation notes
```

## Quick Start

Backend:

```powershell
cd backend
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install ".[dev]"
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Mobile:

```powershell
cd mobile
npm install
copy .env.example .env
npm start
```

Use `http://10.0.2.2:8000` for Android emulator. Use your computer LAN IP for a physical Android device.

## Supabase Setup

1. Create a Supabase project.
2. Create the `dog-videos` storage bucket.
3. Run `supabase/schema.sql` in the Supabase SQL editor.
4. Add backend credentials to `backend/.env`.
5. Add Expo public credentials to `mobile/.env`.

SQLite remains the dev fallback and is enough for local MVP testing.

For the linked project `qvokxgvqhegbpgrbcznq`, the app is configured to upload private videos to Supabase Storage and pass a short-lived signed URL to FastAPI for processing. Supabase CLI `link` still requires a Supabase access token via `supabase login --token ...`; account username/password cannot be used by the CLI.

## Model Roadmap

The backend currently provides a working baseline fusion layer and optional YOLO detection if `ultralytics` is installed. Heavy model integrations are intentionally optional until model licenses, GPU availability, and validation data are confirmed.

Priority order:

1. Validate YOLO dog detection on real phone videos.
2. Add bark/no-bark inference and benchmark it separately.
3. Add DeepLabCut quadruped pose after license review.
4. Add VideoMAE/SlowFast only after enough labeled clips exist.
5. Train lightweight per-dog classifiers after 30-50 corrected clips per dog.
6. Fine-tune breed classification on clear owner photos and phone frames, especially for local and mixed breeds.
