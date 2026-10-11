# 🌶️ MirchiRakshak AI — FastAPI Backend Foundation

FastAPI backend service for MirchiRakshak AI crop pathology, farm management, and intelligent farmer guidance platform.

## Architecture

- **Python**: 3.12+
- **Framework**: FastAPI
- **Database**: PostgreSQL (Supabase) via SQLAlchemy 2.x
- **Validation**: Pydantic v2
- **Auth**: Supabase JWT authentication
- **AI Engine**: Google Gemini API

## Setup Instructions

### 1. Create Virtual Environment & Install Dependencies

```bash
cd backend
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```
Fill in your `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `DATABASE_URL`, and `GEMINI_API_KEY`.

### 3. Run Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Verify Health Endpoint

Open `http://localhost:8000/api/health` or `http://localhost:8000/docs` for Swagger UI.
