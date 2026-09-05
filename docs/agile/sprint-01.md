# Sprint 01

## Sprint goal

Establish a professional, installable `linkeval` skeleton whose quality gates and release path work before introducing metric logic.

## Committed stories

1. Repository and installable package skeleton - 2 points
2. Local quality gates - 2 points
3. Pull-request CI gate - 2 points
4. Scrumban project foundation - 2 points
5. Publish `0.0.1` through TestPyPI and PyPI - 2 points

## Current state

## Current state

- Story 1 - Done
- Story 2 - Done
- Story 3 - Done
- Story 4 - Done
- Story 5 - Done

## Review

Sprint 1 committed 10 points and delivered 10 points.

The sprint established the complete engineering foundation for `linkeval`:

- the package uses a `src/` layout and Hatchling;
- the development environment includes pytest, coverage, Hypothesis, Ruff, mypy, and pre-commit;
- CI tests Python 3.10 through 3.13;
- `main` is protected and changes are merged through pull requests;
- the Scrumban board, Definition of Ready, Definition of Done, working agreement, velocity tracking, and issue templates are in place;
- Release Please manages release preparation from Conventional Commits;
- TestPyPI and PyPI publishing use GitHub OIDC trusted publishing;
- `linkeval==0.0.1` was successfully installed from public PyPI into a clean virtual environment.

## Retrospective

## Retrospective

### What happened versus what I committed to?

I committed to five stories worth 10 points and delivered all 10 points. The sprint required more troubleshooting than expected, particularly around Windows file encoding, Git and GitHub configuration, branch protection, and the first automated release. None of these issues caused a committed story to be dropped.

### What slowed me down that is fixable?

The largest avoidable slowdown was inconsistent text-file encoding on Windows. Files created through some PowerShell commands contained Windows-1252 characters or UTF-8 BOMs, which caused failures in Hatchling, TOML parsing, and Ruff. Learning GitHub Projects, branch protection, pull requests, and release automation also took time, but that was useful learning rather than avoidable waste.

### One change for Sprint 2

Repository text files will be created and edited only using VS Code or an explicit UTF-8-without-BOM method such as `WriteAllText(..., UTF8Encoding(false))`. Plain `Set-Content -Encoding utf8` will not be used for source, configuration, or documentation files.
