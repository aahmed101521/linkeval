# Contributing to linkeval

## Development setup

Clone the repository and create a virtual environment:

    python -m venv .venv

Activate the environment and install the package with development dependencies:

    python -m pip install -e ".[dev]"
    pre-commit install

## Quality checks

Before opening a pull request, run:

    pytest
    ruff check .
    ruff format --check .
    mypy src/linkeval
    python -m build
    pre-commit run --all-files

## Branches and pull requests

Development happens on short-lived branches using an issue number, for example:

    feat/12-cluster-representation
    fix/18-empty-truth-set
    docs/21-bootstrap-guide
    chore/6-release-pipeline

Changes reach `main` only through pull requests. CI must pass before merge.

Pull requests are squash merged and should include `Closes #n` for their associated issue.

## Conventional Commits

Commit messages follow Conventional Commits.

Examples:

    feat: add cluster representation
    fix: reject self-pairs
    docs: explain record-level bootstrap
    chore: update release workflow

The commit type is part of the release system. Release Please uses Conventional Commits to determine the next version and generate the changelog.

## Releases

Release Please manages release preparation.

1. Conventional Commits merged to `main` are inspected by Release Please.
2. Release Please opens or updates a release pull request.
3. The release pull request contains the calculated version and generated changelog.
4. The release pull request must pass the normal review and CI gates.
5. Merging the release pull request creates the Git tag and GitHub release.
6. The release workflow builds the wheel and source distribution.
7. The distributions are published to TestPyPI using GitHub OIDC trusted publishing.
8. Installation from TestPyPI is verified.
9. The same distributions are published to PyPI using GitHub OIDC trusted publishing.
10. Installation from PyPI is verified.

No PyPI API token is stored in repository secrets.

## Release credentials

TestPyPI and PyPI trust the GitHub Actions workflow through OpenID Connect.

Authorized workflow:

    .github/workflows/release.yml

GitHub environments:

    testpypi
    pypi
