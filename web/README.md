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