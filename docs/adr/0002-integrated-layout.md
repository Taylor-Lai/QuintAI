# ADR-0002: Integrated backend and frontend boundaries

- Status: accepted
- Date: 2026-07-22

## Context

The AI capabilities and FastAPI application are developed, tested, deployed,
and versioned together. An `apps/` and `packages/` monorepo split added package
boundaries without an independent consumer or publication lifecycle.

## Decision

Use top-level `backend/` and `frontend/` deployable boundaries. Package all
server-side code under the single `docnexus` namespace and place AI domains
under `docnexus.ai`. Keep the backend's `src` layout, capability-based API
routes, layered persistence, repository-wide tooling, and dedicated deployment
and documentation directories.

## Consequences

Developers install one Python distribution and imports express the actual
ownership model. Backend and AI changes ship together. If a real independent
consumer or release cadence emerges later, the AI module can be extracted
behind its existing workflow facade.
