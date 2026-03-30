# SCOR

Monorepo dla aplikacji scoringowej (FastAPI + React + Entra ID).

## Backend

1. Skopiuj `backend/.env.example` do `backend/.env` i uzupełnij wartości.
2. Jeśli chcesz przebudować strukturę tabel na starcie (utrata danych), ustaw `DB_REBUILD_ON_START=true`.
3. Uruchom:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
```

## Frontend

1. Skopiuj `frontend/.env.example` do `frontend/.env`.
2. Uzupełnij zmienne środowiskowe.


Zmienne frontend (`frontend/.env`):
- `VITE_ENTRA_TENANT_ID`
- `VITE_ENTRA_SPA_CLIENT_ID`
- `VITE_API_SCOPE`
- `VITE_API_BASE_URL`
- `VITE_LOGIN_BACKGROUND_URL` (opcjonalnie: tło ekranu logowania)
- `VITE_APP_LOGO_URL` (opcjonalnie: logo w panelu po zalogowaniu)

3. Uruchom:

```bash
cd frontend
npm install
npm run dev
```


## Troubleshooting

- Jeśli `npm run build` zwraca błąd `Unexpected "<<"`, sprawdź czy w plikach frontendu nie zostały markery konfliktu merge (`<<<<<<<`, `=======`, `>>>>>>>`).
- Po `git pull` uruchom ponownie `npm run build`.
