# Mirchi Rakshak

Mirchi Rakshak is a chili-crop assistance application with a React and
TanStack Start frontend, a FastAPI backend, and supporting machine-learning
tools.

## Requirements

- Node.js and npm
- Python 3.12 or later for the backend

## Run the frontend

1. Create a local environment file from the safe template:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Add your Supabase and any server-side AI credentials to `.env`. Never
   commit real credentials; `.env` files are ignored by Git.
3. Install dependencies and start the development server:

   ```powershell
   npm ci
   npm run dev
   ```

The available frontend scripts also include `npm run build`, `npm run preview`,
and `npm run lint`.

## Run the backend

The backend has its own environment file and dependency list:

```powershell
cd backend
Copy-Item .env.example .env
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Set the Supabase, database, and Gemini values required by your setup in
`backend/.env`. The API docs are available at `http://localhost:8000/docs`.

## Machine-learning data

Training datasets, downloaded archives, scratch files, virtual environments,
and generated build output are local-only and excluded by `.gitignore`. Follow
the setup instructions in `ml/README.md` for the machine-learning workflow.
Do not commit model weights or datasets unless they have been intentionally
prepared for distribution.

## Before publishing

Review `git status` and the staged diff before committing. Keep `.env` files,
credentials, virtual environments, datasets, and generated output out of the
repository. Large files already tracked by Git remain tracked until they are
removed from the index; adding an ignore rule does not remove them from Git
history.
