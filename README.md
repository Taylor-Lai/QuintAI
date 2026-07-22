# DocNexus

DocNexus is a document-intelligence system with a FastAPI backend, a Vue 3
frontend, and integrated AI workflows for document editing, information
extraction, and multi-source table filling.

## Repository layout

```text
.
├── backend/                 # Python backend and all server-side AI capabilities
│   ├── src/docnexus/        # Installable application package
│   └── tests/               # Unit, contract, and acceptance tests
├── frontend/                # Vue 3 + Vite client
├── deploy/docker/           # Production container definition
├── docs/                    # Architecture, development, operations, and ADRs
├── requirements/            # Python dependency sets
├── scripts/                 # Repeatable PowerShell workflows
├── tests/manual/            # Cross-system manual QA scenarios and fixtures
├── compose.yaml
├── environment.yml          # Local Anaconda environment definition
└── pyproject.toml           # Repository-wide test and lint configuration
```

The repository has two deployable boundaries: `backend` and `frontend`.
Server-side AI code is an internal backend capability under `docnexus.ai`; it
is not maintained as a separately versioned or published package.

## Local setup with Anaconda

```powershell
conda activate wangtiao-engineering
python -m pip install -r requirements/dev.txt
python -m pip install --no-deps -e backend
Copy-Item .env.example .env
```

For a clean machine, run `conda env create -f environment.yml` from the
repository root. Set a strong `SECRET_KEY` and configure a supported model
provider in `.env` before exercising AI endpoints.

## Run

Backend:

```powershell
uvicorn docnexus.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```powershell
Set-Location frontend
npm install
npm run dev
```

## Verify

```powershell
pytest -m "not api_acceptance"
ruff check backend
Set-Location frontend
npm run lint
npm run build
```

Real-provider tests live under `backend/tests/acceptance`, are marked
`api_acceptance`, and require valid credentials in `.env`.

Manual end-to-end scenarios and their source/template files are retained under
`tests/manual`. Each scenario contains its own Chinese usage instructions.

## Container deployment

```powershell
docker compose up --build
```

The production container serves the compiled frontend and API on port 8000.
SQLite data uses the `docnexus-data` volume; reports are mounted to `reports/`.

See [the documentation index](docs/README.md) for architecture, conventions,
setup, deployment, and recorded design decisions.
