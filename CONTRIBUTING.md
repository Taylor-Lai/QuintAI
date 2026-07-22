# Contributing

## Workflow

1. Create a focused branch from the current mainline.
2. Install the backend in editable mode and install frontend dependencies.
3. Keep changes inside the documented backend or frontend boundary.
4. Add or update tests for observable behavior and public contracts.
5. Run Python tests, Ruff, frontend lint, and the production web build.
6. Update `.env.example`, documentation, and an ADR when relevant.

Do not commit secrets, local databases, generated reports, virtual
environments, dependency directories, or build output.

Commit messages should be imperative and scoped where useful, for example
`api: split authentication routes` or `web: validate multi-source uploads`.

See [repository conventions](docs/development/conventions.md) for naming and
placement rules.
