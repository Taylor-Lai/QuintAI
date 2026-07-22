# ADR-0001: Monorepo application and package boundaries

- Status: superseded by ADR-0002
- Date: 2026-07-22

## Context

The original repository mixed the API entry point, database module, service
modules, frontend, and reusable AI code at the root. Imports depended on the
current working directory and the API entry point contained every route.

## Decision

Use an application/package monorepo:

- deployable products live under `apps/`;
- reusable Python capabilities live under `packages/`;
- the backend and AI core use installable `src` layouts;
- API routes are grouped by capability;
- repository-wide tooling stays at the root;
- deployment and documentation receive dedicated directories.

## Consequences

Imports are stable after installation, application boundaries are explicit,
and independent packaging is possible. Contributors must install both Python
packages in editable mode for development and keep public route tests current.
