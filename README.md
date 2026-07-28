# Email Generator (Django + React)

Full-stack email generator with two AI paths:
- **Groq LLM** (when `GROQ_API_KEY` is set)
- **Local self-trained fallback model** (works with no API keys)

Backend: Django + DRF  
Frontend: React + Vite  
Deploy: Render (backend) + Vercel (frontend)

## Features

- Generate email **subject** and **body** from structured brief inputs
- Tone + length controls
- Copy subject/body/full email
- Local fallback model trained from in-repo corpus, with retraining command for Kaggle/public datasets

## Project Structure

```text
.
├── backend
│   ├── email_generator
│   ├── emails
│   │   ├── data/seed_email_corpus.jsonl
│   │   ├── local_ai.py
│   │   └── management/commands/train_email_fallback_model.py
│   ├── manage.py
│   └── requirements.txt
├── frontend
│   ├── src
│   ├── package.json
│   └── vercel.json
└── render.yaml
```

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## API

`POST /api/generate-email/`  
`GET /api/health/`

## Local Fallback AI Model

If `GROQ_API_KEY` is empty, the app uses the local fallback model from `emails/local_ai.py`.

### Retrain fallback model from dataset

1. **From local Kaggle CSV/JSONL**
```bash
cd backend
python manage.py train_email_fallback_model --dataset-path /absolute/path/to/dataset.csv
```

2. **From public dataset URL**
```bash
cd backend
python manage.py train_email_fallback_model --dataset-url "https://example.com/email_dataset.csv"
```

Supported dataset columns: `subject`, plus one of `body` / `email` / `message` / `text` (optional `tone`).

Trained model is saved at:
`backend/emails/model/local_email_model.json`

## Environment Variables

Backend (`backend/.env`):

- `DJANGO_SECRET_KEY=...`
- `DJANGO_DEBUG=True|False`
- `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,.onrender.com`
- `CORS_ALLOW_ALL_ORIGINS=True`
- `GROQ_API_KEY=` (optional)
- `GROQ_MODEL=llama-3.1-8b-instant`
- `LOCAL_FALLBACK_ON_PROVIDER_ERROR=True`

Frontend (`frontend/.env`):

- `VITE_API_BASE_URL=http://127.0.0.1:8000` (local)
- `VITE_API_BASE_URL=https://email-generator-backend-klgk.onrender.com` (production)

## Deployment

### Render (backend)

- `render.yaml` already installs required libraries with `pip install -r requirements.txt`
- Runs migrations on start: `python manage.py migrate`
- Binds to Render port: `gunicorn ... --bind 0.0.0.0:${PORT:-10000}`

### Vercel (frontend)

- Root directory: `frontend`
- Set `VITE_API_BASE_URL` to your Render backend URL
