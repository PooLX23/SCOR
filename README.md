# SCOR

Monorepo dla aplikacji scoringowej (FastAPI + React + Entra ID).

## Backend

1. Skopiuj `backend/.env.example` do `backend/.env` i uzupełnij wartości.
2. Uruchom:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
```

## Frontend

1. Skopiuj `frontend/.env.example` do `frontend/.env`.
2. Uruchom:

```bash
cd frontend
npm install
npm run dev
```
