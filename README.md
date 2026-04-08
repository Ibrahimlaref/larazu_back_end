# LAZULI E-Commerce

Full-stack e-commerce app: Django REST backend + React/Vite frontend.

## Quick Start (Docker)

From project root:

```bash
cp shop_backend/.env.example shop_backend/.env
docker compose up --build
```

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API docs:** http://localhost:8000/api/docs/

## Local Development

### Backend
```bash
cd shop_backend
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
python -m pip install -r requirements/base.txt
# PostgreSQL running locally with lazuli DB
python manage.py migrate
python manage.py seed_lazuli
python manage.py runserver
```

### Frontend
```bash
cd shop_frontend
npm install
npm run dev
```

Frontend proxies `/api` and `/media` to backend when using default config. Set `VITE_API_URL=http://localhost:8000` if backend runs separately.

## Environment

- `shop_backend/.env` — PostgreSQL, Django, `LAZULI_ADMIN_TOKEN`
- `shop_frontend/.env` — `VITE_API_URL`, `VITE_USE_API` (set to `false` for mock data)

## Admin

- Login: admin@lazuli.dz / admin123 (after `seed_lazuli`)
- Admin token: `X-Admin-Token: lazuli-admin-token-dev` (or value from `LAZULI_ADMIN_TOKEN`)
