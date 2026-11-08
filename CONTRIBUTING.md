# Contributing

- `master` is protected: work on a branch (`feat/...`, `fix/...`, `docs/...`), open a PR, merge when CI is green.
- Run `pytest`, `ruff check .` and `mypy` before pushing.
- A new algorithm needs: a cited primary source, a methodological-limitations section in `docs/`, tests with hand-verifiable results, edge cases, missing-data and malformed-input tests. Do not invent methodology; if a convention is not universal, make it an explicit parameter.
- Never fill gaps silently: report them in validation or in the result metadata.
- Test data must be clearly labelled fictional unless it is published data with a citation.
- Everything in the repository is in English.

By contributing you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
