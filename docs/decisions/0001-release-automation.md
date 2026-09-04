# ADR 0001: Release automation

## Status

Accepted

## Context

`linkeval` needs a release process that keeps version numbers, changelog entries, GitHub releases, and package publication consistent with one another. Because the project uses protected `main`, pull-request-only changes, and Conventional Commits, the release mechanism should fit that workflow rather than bypass it. The aim is to avoid manually deciding version bumps or reconstructing a changelog at release time.

## Decision

We will use Release Please for release versioning and changelog generation. Release Please derives the next release from Conventional Commits and prepares the version and changelog changes in a release pull request. This fits the repository's PR-gated workflow because release-related changes remain reviewable and must pass CI before reaching `main`. Publishing to TestPyPI and PyPI will then be triggered from the resulting GitHub release using trusted publishing.

## Alternatives considered

### python-semantic-release

`python-semantic-release` was a reasonable alternative because it also derives version changes from Conventional Commits and can automate changelog generation and publishing. We did not choose it because Release Please's release-PR model fits more naturally with this repository's protected-branch workflow. It keeps the version and changelog update inside the same pull-request process used for normal development rather than relying on release automation to write changes directly to `main`.

### Manual versioning and changelog maintenance

Manual versioning would give full control over each release, but it would introduce a repetitive maintenance step that is easy to forget or apply inconsistently. It would also weaken the purpose of adopting Conventional Commits, since commit history would no longer directly drive release metadata. For this project, the additional manual control is not worth the risk of version and changelog drift.

## Consequences

Release preparation becomes reproducible and visible in pull requests, and the changelog is derived from the same commit history used for development. The trade-off is that commit messages now form part of the release system: incorrect Conventional Commit prefixes can lead to an incorrect version bump or missing changelog entry. This means commit-message discipline is a functional requirement rather than only a style preference.