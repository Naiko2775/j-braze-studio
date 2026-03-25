# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

J-Braze Studio is a Braze CRM toolkit providing data model analysis, Liquid code generation, and platform migration tools. It is a monorepo deployed on Vercel with a Neon PostgreSQL database.

## Architecture

```
J_braze_studio/
├── apps/
│   ├── web/          # React SPA (Vite)
│   └── api/          # FastAPI backend (Vercel serverless via Mangum)
├── vercel.json       # Vercel deployment config
├── package.json      # Root workspace (concurrently for dev)
└── CLAUDE.md
```

- **Frontend**: React 18 + React Router + Vite, served as static build on Vercel
- **Backend**: FastAPI wrapped with Mangum for Vercel Python serverless functions
- **Database**: Neon PostgreSQL (SQLAlchemy ORM, Alembic migrations), SQLite fallback in dev
- **AI**: Anthropic Claude API for analysis and generation features

## Commands

### Development
```bash
# Start both frontend and backend in dev mode
npm run dev

# Frontend only (port 5173)
npm run dev:web

# Backend only (port 8000)
npm run dev:api
```

### Build
```bash
# Build frontend for production
npm run build:web
```

### Test
```bash
# Run API tests
npm run test:api

# Or directly
cd apps/api && python -m pytest tests/ -v
```

### Database Migrations
```bash
cd apps/api
alembic upgrade head          # Apply migrations
alembic revision --autogenerate -m "description"  # Create migration
```

## Backend Modules (apps/api/)

| Module | Router | Service | Description |
|--------|--------|---------|-------------|
| Data Model | `routers/data_model.py` | `services/data_model/` | Braze data model analysis, estimation, export |
| Liquid | `routers/liquid.py` | `services/liquid/` | Liquid template generation from briefs |
| Migration | `routers/migration.py` | `services/migration/` | Platform migration (Brevo, SFMC, CSV to Braze) |
| Projects | `routers/projects.py` | - | Multi-project management |
| Settings | `routers/app_config.py` | - | App configuration, API key management |

### Service Sub-modules

- `services/claude_client.py` -- Shared Anthropic Claude API client
- `services/data_model/analyzer.py` -- AI-powered data model analysis
- `services/data_model/estimator.py` -- Cost/volume estimation
- `services/data_model/exporter.py` -- Excel/JSON export
- `services/data_model/reference.py` -- Braze reference data
- `services/liquid/generator.py` -- Liquid code generation
- `services/liquid/templates.py` -- Template library
- `services/migration/engine.py` -- Migration orchestration
- `services/migration/connectors/` -- Source platform connectors (Brevo, SFMC, CSV)
- `services/migration/mappers/` -- Data mapping logic
- `services/migration/exporters/` -- Braze API export

## Frontend Modules (apps/web/src/)

| Module | Path | Description |
|--------|------|-------------|
| Data Model | `modules/data-model/` | Analysis form, results, entity explorer |
| Liquid Generator | `modules/liquid-generator/` | Brief form, result display, preview |
| Migration | `modules/migration/` | Platform config, data preview, runner, warmup |
| Shared | `shared/` | Layout, components, hooks, context, styles |
| Pages | `pages/` | Explorer, History, Projects, Settings |

## Code Conventions

- **Python**: FastAPI with type hints, Pydantic models, async where beneficial. All API routes prefixed with `/api/`.
- **JavaScript/React**: Functional components with hooks, JSX. No TypeScript (plain JS).
- **Styling**: CSS modules via `shared/styles/`. Jakala brand theme.
- **API pattern**: Routes in `routers/`, business logic in `services/`, DB models in `models/`.
- **Environment**: All secrets via environment variables (never hardcoded). `python-dotenv` for local dev.
- **Vercel deployment**: Frontend via `@vercel/static-build`, backend via `@vercel/python` (Mangum ASGI adapter).

## Key Files

- `apps/api/main.py` -- FastAPI app definition, middleware, router registration, Mangum handler
- `apps/api/index.py` -- Vercel serverless entry point (imports handler from main.py)
- `apps/api/models/db.py` -- SQLAlchemy engine/session configuration
- `apps/web/src/App.jsx` -- React app with routing
- `apps/web/src/shared/hooks/useApi.js` -- Shared API fetch hook
- `vercel.json` -- Vercel build and routing configuration
