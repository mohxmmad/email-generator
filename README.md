# Email Generator (Django + React)

A full-stack email generator web app:
- **Backend:** Django + Django REST Framework
- **Frontend:** React + Vite
- **AI generation:** Groq model (optional) with built-in local fallback
- **Deployment targets:** Render (backend) and Vercel (frontend)

## Features

- Rich email brief form (sender, recipient, purpose, key points, tone, length, language)
- AI-generated **subject** and **body**
- Copy subject/body/full email to clipboard
- Clean responsive UI
- API-first architecture for easy future extension

## Project Structure

```text
.
├── backend
│   ├── email_generator
│   ├── emails
│   ├── manage.py
│   └── requirements.txt
├── frontend
│   ├── src
│   ├── package.json
│   └── vercel.json
└── render.yaml
```

## Local Development

### 1) Backend (Django)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Backend runs on `http://localhost:8000`.

### 2) Frontend (React)

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend runs on `http://localhost:5173`.

## API

`POST /api/generate-email/`

### Request body

```json
{
  "sender_name": "Alex",
  "sender_role": "Account Manager",
  "recipient_name": "Priya",
  "recipient_role": "Head of Marketing",
  "company": "Acme Inc.",
  "purpose": "Follow up after product demo",
  "key_points": "Thank them for the time; propose pilot timeline; share pricing options.",
  "additional_context": "They requested rollout support details.",
  "call_to_action": "Ask for a 30-minute pilot planning call next week.",
  "tone": "Professional",
  "length": "Medium",
  "language": "English"
}
```

### Response body

```json
{
  "subject": "Suggested email subject",
  "body": "Generated email body"
}
```

## Deploy Backend on Render

1. Push repository to GitHub.
2. In Render, create a new Blueprint and point it to this repo.
3. Render picks up `render.yaml` automatically.
4. Set:
   - `CORS_ALLOW_ALL_ORIGINS=True` (already set in `render.yaml`)
   - (Optional) `GROQ_API_KEY`
   - (Optional) `GROQ_MODEL`
5. Deploy.

Your backend URL will be similar to:
`https://email-generator-backend.onrender.com`

## Deploy Frontend on Vercel

1. Import the `frontend` directory as a Vercel project.
2. Framework preset: **Vite**
3. Set environment variable:
   - `VITE_API_BASE_URL=https://your-render-backend.onrender.com`
4. Deploy.

## Notes

- No OpenAI key is required.
- If `GROQ_API_KEY` is present, Groq is used for generation.
- If `GROQ_API_KEY` is empty, the app uses the built-in local generator.
