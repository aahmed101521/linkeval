# Definition of Done

A story is Done only when all of the following are true:

- It is merged to `main` through a pull request and is never pushed directly to `main`.
- CI is green: tests, Ruff, and mypy all pass.
- Test coverage has not decreased.
- Public API changes are fully typed and documented with docstrings.
- Documentation is updated when the public API changes.
- Commit messages follow Conventional Commits.
- An ADR exists in `docs/decisions/` when the story introduces a significant technical or statistical decision.

A story that has completed implementation but has not satisfied every condition remains In Review rather than moving to Done.
