# Working instructions

- `master` is protected: no direct pushes. Every small, self-contained change goes on its own branch (`feat/...`, `fix/...`, `docs/...`, `chore/...`), is committed, pushed and merged through a pull request once CI is green.
- Before pushing run `pytest`, `ruff check .` and `mypy`.
- The user's goal is to learn how to build a library with good practices: when adding tooling or conventions, briefly explain why it is good practice.
- Do not publish to PyPI unless the user explicitly asks.

# Project

Python library (`zooarchpy`) for quantitative zooarchaeology. Design in `docs/design.md`; roadmap in `docs/roadmap.md`.

- Code in `src/zooarchpy/`, tests in `tests/`, fictional sample data in `examples/`.
- Scientific rules: never invent methodology, never fill missing data silently, keep missing / observed-absent / not-applicable distinct, cite primary sources per method, document limitations per algorithm.
- No runtime dependencies unless justified; development ones go in `[project.optional-dependencies].dev`.
- Everything (code, docs, messages) is in English.
