# Development setup

## Prerequisites

- A local Anaconda installation with Python 3.11 support.
- Node.js 20.19+ or 22.12+ and npm.
- Docker Desktop only for container validation.

## Python environment

```powershell
conda create -n wangtiao-engineering python=3.11 pip -y
conda activate wangtiao-engineering
python -m pip install -r requirements/dev.txt
python -m pip install --no-deps -e backend
```

Alternatively, run `conda env create -f environment.yml` from the repository
root. The editable install makes the single `docnexus` package importable.

## Configuration

Copy `.env.example` to `.env`. Development requires `SECRET_KEY` for login and
the selected `LLM_PROVIDER` credential when exercising AI endpoints.

## Common commands

The `scripts/` directory provides repeatable PowerShell entry points. Commands
can also be executed directly as documented in the root README.
