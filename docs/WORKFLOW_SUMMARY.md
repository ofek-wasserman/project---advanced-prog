# Project Workflow Summary

This document defines the mandatory team workflow.

----------------------------------------
JIRA RULES
----------------------------------------

Every code change must be linked to a Jira issue (KAN-XX).

Each Jira issue must contain:
- Clear description
- Acceptance criteria
- Phase label (Phase01 or Phase02)

----------------------------------------
BRANCH STRATEGY
----------------------------------------

Main branch is protected.

No direct pushes to main.

One Jira issue → one branch → one PR.

Branch name format:
    feature/KAN-XX-short-description

Example:
    feature/KAN-23-start-ride-service

----------------------------------------
PULL REQUEST RULES
----------------------------------------

A PR can be merged only if:

- CI (pytest) is green
- At least 1 approval exists
- Branch is up to date with main
- All conversations are resolved

Merge type:
- Squash merge only

Branches are automatically deleted after merge.

----------------------------------------
JIRA STATUS MEANING
----------------------------------------

TO DO / IDEA
    Not started

IN PROGRESS
    Work happening in feature branch

IN REVIEW
    PR opened to main, reviewer requested, CI running or green

DONE
    PR merged to main and CI green on main

If a PR is not merged, the issue is NOT DONE.

----------------------------------------
COMMIT MESSAGE RULE
----------------------------------------

Every commit must start with the Jira key:

Example:
    KAN-12: Implement deterministic vehicle selection