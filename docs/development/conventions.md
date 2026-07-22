# Repository conventions

## Naming

- Python packages and modules: `snake_case`.
- Python classes: `PascalCase`; functions and variables: `snake_case`.
- Vue components and views: `PascalCase.vue`; routed pages end in `View.vue`.
- JavaScript modules: lower-case domain nouns such as `auth.js` and `user.js`.
- Tests: `test_<behavior>.py`; test functions describe observable behavior.
- Environment variables: `UPPER_SNAKE_CASE` and documented in `.env.example`.

## Placement rules

- HTTP parsing, status codes, and FastAPI dependencies belong in `api/`.
- Security primitives and settings belong in `core/`.
- SQL queries belong in `repositories/`; sessions and models belong in `db/`.
- Cross-domain application operations belong in `services/`.
- AI workflows and algorithms belong in `docnexus.ai` and cannot import API routes.
- Runtime data, reports, caches, environments, dependencies, and builds are not committed.

## Change requirements

Every public API change must update route-contract or acceptance tests. Every
new configuration key must be added to `.env.example`. Architecture boundary
changes require an ADR under `docs/adr/`.
