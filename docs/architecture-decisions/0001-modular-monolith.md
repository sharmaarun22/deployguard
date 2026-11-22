# ADR-0001: Modular Monolith

## Status

Accepted

## Context

DeployGuard needs a maintainable local MVP without premature distributed infrastructure.

## Decision

Implement a modular monolith using FastAPI and SQLAlchemy.

## Consequences

The application is easy to run and test locally. Module boundaries remain clear enough to extract
services later. Networked integrations remain optional.
