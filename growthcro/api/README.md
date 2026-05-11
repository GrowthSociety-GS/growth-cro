# growthcro.api

FastAPI HTTP server exposing the audit + recos pipeline (V26 webapp).
Was `api_server.py` at the repo root before the #9 reorganization.

## Modules
- `server.py` — FastAPI app (`app`), routes for client list, page status, captures, scores, recos.

## Entrypoints
```bash
python -m growthcro.api.server                     # uvicorn auto-binds 0.0.0.0:8000
uvicorn growthcro.api.server:app --port 8000       # explicit
```

Docker:
```bash
docker run --rm -p 8000:8000 growthcro python -m growthcro.api.server
```

## Imports from
- `growthcro.config` (port + CORS origins).
- `fastapi`, `uvicorn`.

## Imported by
- External (HTTP only). Consumed by `deliverables/GrowthCRO-V26-WebApp.html`.
