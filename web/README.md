# NADOS Dv1.0 Web Interface

Web-based interface for NADOS Dv1.0 - Integrated Air Defense Research & Simulation Environment.

## Architecture

```
web/
├── frontend/          # Vue 3 + Vite + Element Plus
│   ├── src/
│   │   ├── views/     # Page components
│   │   ├── stores/    # Pinia state management
│   │   ├── services/  # API services
│   │   ├── router/    # Vue Router
│   │   └── styles/    # SCSS styles
│   ├── public/        # Static assets
│   ├── nginx.conf     # Nginx configuration
│   └── Dockerfile
├── backend/           # FastAPI backend
│   ├── api/           # API routes
│   ├── main.py        # FastAPI app
│   └── Dockerfile
└── docker-compose.yml # Full stack deployment
```

## Features

- **Real-time Simulation Dashboard**: Live 2D map with objects, sensors, tracks
- **Scenario Management**: Create, edit, validate, and run scenarios
- **Sensor Management**: Configure radar, LIDAR, optical sensors
- **Tracking Visualization**: Kalman filter tracks with covariance
- **Event Log**: Real-time event streaming
- **Reports**: Generate JSON/CSV reports
- **Tests**: Run and view test results
- **Settings**: Configure all system parameters

## Quick Start

### Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (in another terminal)
cd ../frontend
npm install
npm run dev
```

### Docker (Production)

```bash
# From web directory
docker-compose up -d

# Access:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Cloudflare Pages / Workers

The static frontend can be hosted on Cloudflare. The FastAPI backend
cannot run inside Cloudflare (Python + SQLite process) — host it anywhere
and point the frontend/proxy at it.

Prepared artifacts:

| File | Purpose |
|------|---------|
| `web/frontend/public/_redirects` | SPA fallback for Pages routing |
| `web/frontend/functions/api/[[path]].js` | Pages Function that proxies `/api/*` to `BACKEND_URL` |
| `web/frontend/src/worker.js` + `wrangler.toml` | Alternative Workers static-assets deployment with the same proxy |
| `.github/workflows/deploy-cloudflare.yml` | CI deployment to the Pages project `nadosdv1` |

Manual deployment (Pages):

```bash
cd web/frontend
npm ci && npm run build

# Requires an API token with "Account -> Cloudflare Pages -> Edit"
export CLOUDFLARE_API_TOKEN=...        # PowerShell: $env:CLOUDFLARE_API_TOKEN="..."
npx wrangler@4 pages deploy dist --project-name=nadosdv1 --branch=main
```

Alternative deployment (Worker, static assets):

```bash
cd web/frontend
npm ci && npm run build

# Requires an API token with "Account -> Workers Scripts -> Edit"
npx wrangler@4 deploy
```

After deployment, configure the backend URL so `/api/*` works:

- Pages: project Settings -> Environment variables -> add `BACKEND_URL`
  (production), e.g. `https://nados-api.example.com`
  (the Function forwards `/api/...` to `BACKEND_URL/api/...`).
- Worker: `npx wrangler secret put BACKEND_URL`.

If `BACKEND_URL` is not set, `/api/*` returns a clear 503 JSON error and
the UI stays usable (it shows "قاعدة البيانات غير متصلة").

CI deployment uses two repository secrets:

- `CLOUDFLARE_API_TOKEN` — token with **Cloudflare Pages: Edit**
- `CLOUDFLARE_ACCOUNT_ID` — `12649c0d3d106dcb980f606b668e53e2`

and the optional repository variable `VITE_API_BASE` (e.g.
`https://api.example.com/api`) to hardcode the backend at build time.

## API Endpoints

### Scenarios
- `GET /api/scenarios` - List scenarios
- `GET /api/scenarios/{id}` - Get scenario
- `POST /api/scenarios` - Create scenario
- `PUT /api/scenarios/{id}` - Update scenario
- `DELETE /api/scenarios/{id}` - Delete scenario
- `POST /api/scenarios/{id}/validate` - Validate scenario

### Simulation
- `GET /api/simulation/status` - Get simulation status
- `POST /api/simulation/start` - Start simulation
- `POST /api/simulation/pause` - Pause simulation
- `POST /api/simulation/resume` - Resume simulation
- `POST /api/simulation/stop` - Stop simulation
- `POST /api/simulation/reset` - Reset simulation
- `POST /api/simulation/speed` - Set speed
- `POST /api/simulation/load` - Load scenario
- `GET /api/simulation/objects` - Get objects
- `GET /api/simulation/sensors` - Get sensors
- `GET /api/simulation/tracks` - Get tracks

### Sensors
- `GET /api/sensors` - List sensors
- `POST /api/sensors` - Create sensor
- `PUT /api/sensors/{id}` - Update sensor
- `DELETE /api/sensors/{id}` - Delete sensor

### Tracking
- `GET /api/tracking` - List tracks
- `GET /api/tracking/stats/summary` - Tracking statistics
- `POST /api/tracking/config` - Set tracker config

### Reports
- `GET /api/reports/runs` - List runs
- `POST /api/reports/generate` - Generate report
- `GET /api/reports/{run_id}/download/{format}` - Download report

### Health
- `GET /api/health` - Health check
- `GET /api/health/live` - Liveness probe
- `GET /api/health/ready` - Readiness probe

## Environment Variables

Copy `web/.env.example` to `web/.env` and configure:

```bash
cp .env.example .env
```

Key variables:
- `NADOS_DB_PATH` - Database path
- `NADOS_LOG_LEVEL` - Log level (DEBUG/INFO/WARNING/ERROR)
- `NADOS_API_URL` - Backend API URL for frontend
- `NADOS_SECRET_KEY` - JWT secret key

## Development Notes

### Frontend (Vue 3 + Vite)
- Framework: Vue 3 + Composition API
- UI Library: Element Plus
- State Management: Pinia
- Routing: Vue Router 4
- Charts: ECharts + vue-echarts
- Styling: SCSS with RTL support
- Language: Arabic (RTL) primary

### Backend (FastAPI)
- Framework: FastAPI
- Database: SQLite + SQLAlchemy 2.0
- Validation: Pydantic v2
- Async: async/await throughout
- Auth: JWT (planned)

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd ../frontend
npm run test
```

## License

MIT License - see LICENSE in root directory.