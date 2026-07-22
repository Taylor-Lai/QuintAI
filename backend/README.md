# DocNexus backend

The backend is one installable Python distribution named `docnexus-backend`
and exposes the `docnexus` package. It contains the HTTP application,
persistence layer, application services, and internal AI capabilities.

```text
src/docnexus/
├── api/                     # FastAPI routing and request dependencies
├── ai/                      # Document intelligence and table engine
├── core/                    # Configuration and security primitives
├── db/                      # SQLAlchemy models, sessions, and bootstrap
├── repositories/            # Persistence operations
├── schemas/                 # Transport contracts
├── services/                # Application-level orchestration
└── main.py                  # ASGI application factory
```

From the repository root, install and run it with:

```powershell
python -m pip install --no-deps -e backend
uvicorn docnexus.main:app --reload
```

The optional `any2table` console command remains available for direct table
pipeline execution, but its implementation is internal to `docnexus.ai`.
