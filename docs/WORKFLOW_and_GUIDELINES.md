# Engineering Workflow & Contribution Guidelines

## Vehicle Sharing API

------------------------------------------------------------------------

## 1. Purpose

This document defines the mandatory engineering workflow for the Vehicle
Sharing API project.

The goal is to:

-   Prevent scope creep\
-   Prevent architectural violations\
-   Maintain integration stability\
-   Ensure consistent quality\
-   Enforce disciplined PR process

These rules apply to **all contributors**.

------------------------------------------------------------------------

## 2. Jira Rules

-   Every code change must be linked to a Jira issue (KAN-XX).
-   Each Jira issue must include:
    -   Clear description
    -   Acceptance criteria
    -   Phase label (Phase01 or Phase02)
-   If a PR is not merged, the issue is NOT DONE.

------------------------------------------------------------------------

## 3. Branch Strategy

-   `main` branch is protected.
-   No direct pushes to `main`.
-   One Jira issue → one branch → one PR.

Branch name format:

    feature/KAN-XX-short-description

Example:

    feature/KAN-23-start-ride-service

------------------------------------------------------------------------

## 4. Start of Every Work Session

Before starting any work:

    git checkout main
    git pull origin main

Never start working on an outdated base.

------------------------------------------------------------------------

## 5. Before Committing -- Branch Verification

Ensure:

-   You are on the correct branch
-   The branch name matches the Jira ticket
-   The branch is dedicated to a single task

Verify:

    git branch --show-current

------------------------------------------------------------------------

## 6. Before Committing -- Commit Scope Control

Ensure:

-   Only files relevant to the Jira task are staged
-   No unrelated formatting or accidental deletions
-   No cross-task changes
-   No hidden scope expansion

Check:

    git status
    git diff --staged

Rule:

**One Jira ticket = One focused PR**

------------------------------------------------------------------------

## 7. Unit Testing Requirements

Every task must include corresponding unit tests.

Requirements:

-   Tests must be placed in the correct folder
-   Test file name should reflect functionality (no Jira number
    required)
-   Minimum **80% test coverage**
-   At least:
    -   One happy-path test
    -   One failure-case test

CI must pass before merge.

------------------------------------------------------------------------

## 8. Folder & Layer Structure (Strict Architecture)

Files must be placed in the correct layer:

-   `src/api/` → API layer only (routes, schemas, HTTP mapping)
-   `src/services/` → business orchestration only
-   `src/domain/` → entities and invariants only (NO I/O)
-   `src/data/` → CSV loading only
-   `tests/` → mirrored structure by layer

No cross-layer leakage is allowed.

------------------------------------------------------------------------

## 9. Phase Scope Enforcement

Implementation must stay within the current Phase.

For Phase 1, scope is limited to:

-   CSV bootstrap
-   Register user
-   Start ride (deterministic vehicle selection)
-   End ride (nearest station, fixed 15 ILS pricing)

Do NOT:

-   Add persistence (Phase 2)
-   Add future features
-   Introduce speculative design
-   Implement out-of-scope logic

------------------------------------------------------------------------

## 10. Task Domain Boundaries

When implementing a task:

-   Do not modify unrelated domain models
-   Do not change data types without team alignment
-   Do not refactor architecture unless explicitly part of the task
-   Do not introduce breaking changes outside task scope

------------------------------------------------------------------------

## 11. Lint & Tests Before Every Commit

Always run:

    ruff check . --fix
    python -m pytest -q

Only commit if:

-   Lint passes
-   All local tests pass

CI must be green before merge.

------------------------------------------------------------------------

## 12. Pull Request Rules

A PR can be merged only if:

-   CI is green
-   At least 1 approval exists
-   Branch is up to date with `main`
-   All review conversations are resolved

Merge type:

-   **Squash merge only**

Branches are deleted after merge.

------------------------------------------------------------------------

## 13. PR Template Completion

Before requesting review:

-   Fill the PR template
-   Include Jira link
-   Clearly describe what changed
-   Clearly describe how to test locally
-   Ensure "Files changed" matches the description
-   Ensure no unrelated files appear

------------------------------------------------------------------------

## 14. Commit Message Rule

Every commit must start with the Jira key.

Example:

    KAN-12: Implement deterministic vehicle selection

------------------------------------------------------------------------

## 15. Final Sanity Check Before Push

Before pushing, ask:

-   Does this PR break anything already merged?
-   Does `main` still run?
-   Are tests aligned with implementation?
-   Is this the minimal correct solution?
-   Does this respect the architecture boundaries?

If unsure --- do not push.

------------------------------------------------------------------------

## 16. Enforcement Policy

Any PR violating these rules may be:

-   Rejected
-   Requested for changes
-   Moved back to IN PROGRESS in Jira

Process discipline is part of the project evaluation.