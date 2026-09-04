# Working Agreement

## Cadence

- Work is organized in two-week sprints.
- Sprints start on Saturday.
- Sprints may be skipped for defence preparation, interviews, or other higher-priority commitments.
- A skipped sprint is recorded as skipped rather than silently removed.

## Ceremony timeboxes

- Sprint planning: 15 minutes.
- Sprint review: 5 minutes.
- Sprint retrospective: 10 minutes.
- Total ceremony budget: 30 minutes per sprint.

## Board workflow

Work moves through:

Backlog -> Ready -> In Progress -> In Review -> Done

The In Progress column has a WIP limit of 1.

## Branching and review

- `main` is protected.
- Work happens on short-lived branches using `feat/`, `fix/`, `docs/`, or `chore/` prefixes plus the issue number.
- Changes reach `main` through pull requests.
- CI must pass before merge.
- Pull requests are squash merged.
- Every PR body links its issue using `Closes #n`.
- Before merge, the maintainer reads the full diff and leaves at least one substantive self-review comment.

## Commits

Commit messages follow Conventional Commits:

- `feat:` for user-facing functionality.
- `fix:` for bug fixes.
- `docs:` for documentation changes.
- `test:` for test-only changes.
- `refactor:` for internal code changes without user-facing behavior changes.
- `chore:` for tooling, infrastructure, packaging, or maintenance work.

## Definition enforcement

- A story may move from Backlog to Ready only when it satisfies the Definition of Ready.
- A story may move to Done only when it satisfies the Definition of Done.
- Significant technical or statistical decisions require an ADR in `docs/decisions/`.
