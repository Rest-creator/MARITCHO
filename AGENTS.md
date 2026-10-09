# Agent Instructions for Maricho Project

This file contains the checkpoint rules aligned with our SDLC implementation.

## Phase 1: Discovery Checkpoint
- [x] Verify that the active directory contains `/docs/discovery/vision_document.md`.
- [x] Read and parse the target functional boundaries specified in the `/docs/discovery/business_case.md`.
- [x] Check that the proposed stack aligns with the verified capabilities in the technical feasibility section.

## Phase 2: Requirements Checkpoint (Completed)
- [x] Ensure `/docs/requirements/prd.md` and `/docs/requirements/srs.md` are populated.
- [x] Extract the BDD acceptance criteria from the markdown tables to generate functional test files.
- [x] Confirm that non-functional performance boundaries are mapped to test assertions.

## Phase 3: Architecture Checkpoint (Completed)
- [x] Verify that `/docs/architecture/system_design.md` and `/docs/architecture/adr/` exist.
- [x] Run linting on OpenAPI spec to verify the API specification is compliant.
- [x] Ensure that database schema modifications are documented in the design files.

## Phase 4: Project Planning Checkpoint (Completed)
- [x] Read `/docs/backlog.md` to identify the highest priority uncompleted tasks.
- [x] Verify that all dependencies for the target task have been marked as complete.
- [x] Update the status of the assigned task in `/docs/backlog.md` when implementation begins.

## Phase 5: Engineering Standards Checkpoint (Completed)
- [x] Verify that formatting and linting tools are executed before committing code changes.
- [x] Ensure that new API endpoints include OpenTelemetry instrumentation.
- [x] Check that all log statements conform to the structured JSON template with trace context correlation.

## General Architectural Rules
- Prioritize offline-first constraints (WhatsApp integration, PWA).
- Assume inexpensive Android devices and small data bundles.
- Do not build complex forms where voice or photo inputs can be used.
- In conflict scenarios (worker vs buyer), default to "Design for the worker's worst day" logic.

## Mobile Architecture Guidelines (Flutter)
You are an expert mobile systems engineer. Your modifications must align with the architectural standards, performance configurations, and patterns defined below.

**Core System Conventions**
- **Directory Layout:** Use a feature-first folder structure (`/features/feature_name/data`, `/domain`, `/presentation`).
- **State Flow:** Follow Unidirectional Data Flow. Handle UI changes using Cubits that emit immutable states.
- **Dependency Management:** Inject dependencies explicitly via constructors. Do not use global dynamic registries.
- **Strict Typing:** Specify explicit types for all method signatures and variables. Do not use generic dynamic types.
- **Exceptions:** Never throw uncaught exceptions. Wrap fallible operations in functional `Result.ok()` or `Result.error()` return values.
- **Async Gap Safety:** Always check `if (!mounted) return;` before using context after an await block.
- **Resource Cleanup:** Every class that registers text/scroll controllers, streams, focus nodes, or listeners must explicitly release those assets in its `dispose()` method.

**Structural Rules**
- Limit each file to one major class or widget.
- Reference layout and styling properties from the centralized design system.
- Do not use feature-level barrel files; use absolute imports.

**Verification Protocol**
- Verify modifications with static analysis: `flutter analyze`.
- Format code files before committing changes: `dart format .`
- Run the automated test suite to verify changes: `flutter test`.
