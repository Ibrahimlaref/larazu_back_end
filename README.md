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

## Deploy Backend to Render.com

### Option 1: Deploy from shop_backend directory (Recommended)

1. **Navigate to backend directory**:
   ```bash
   cd shop_backend
   ```

2. **Install Render CLI**:
   ```bash
   npm install -g @render/cli
   # or
   brew install render
   ```

3. **Login to Render**:
   ```bash
   render login
   ```

4. **Deploy the backend**:
   ```bash
   chmod +x deploy-render.sh
   ./deploy-render.sh
   ```

### Option 2: Manual Deployment via Dashboard

1. **Go to [Render Dashboard](https://dashboard.render.com)**

2. **Create PostgreSQL Database**:
   - Service Type: `PostgreSQL`
   - Name: `lazuli-db`
   - Database: `lazuli`
   - User: `lazuli`

3. **Create Redis**:
   - Service Type: `Redis`
   - Name: `lazuli-redis`

4. **Create Backend Web Service**:
   - Service Type: `Web Service`
   - Runtime: `Docker`
   - Root Directory: `shop_backend` (if deploying from root)
   - Dockerfile Path: `Dockerfile.prod`
   - Environment Variables:
     ```
     DJANGO_SETTINGS_MODULE=brahim.settings.prod
     DEBUG=false
     SECRET_KEY=your-super-secret-key-here
     LAZULI_ADMIN_TOKEN=your-admin-token-here
     ALLOWED_HOSTS=your-backend-url.onrender.com
     CORS_ALLOWED_ORIGINS=https://your-frontend-url.onrender.com
     ```

### Production URLs

- **Frontend:** https://your-frontend-name.onrender.com
- **Backend API:** https://your-backend-name.onrender.com
- **API Docs:** https://your-backend-name.onrender.com/api/docs/
- **Admin:** https://your-backend-name.onrender.com/admin/

### Admin Access

- **Login:** admin@lazuli.dz / admin123
- **Admin Token:** Check `LAZULI_ADMIN_TOKEN` environment variable
