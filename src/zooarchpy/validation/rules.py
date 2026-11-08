"""Structured validation. Rules report; they never modify the data."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum

from zooarchpy.models import Specimen, TaxonomyPolicy, Vocabulary


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class Issue:
    severity: Severity
    code: str
    message: str
    specimen_id: str | None = None
    field: str | None = None
    row: int | None = None  # 1-based data row in the source file, when known

    def __str__(self) -> str:
        where = f" [{self.specimen_id}]" if self.specimen_id else ""
        return f"{self.severity.value.upper()} {self.code}{where}: {self.message}"


@dataclass(frozen=True)
class ValidationReport:
    issues: tuple[Issue, ...] = ()

    @property
    def errors(self) -> tuple[Issue, ...]:
        return tuple(i for i in self.issues if i.severity is Severity.ERROR)

    @property
    def warnings(self) -> tuple[Issue, ...]:
        return tuple(i for i in self.issues if i.severity is Severity.WARNING)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dicts(self) -> list[dict[str, object]]:
        return [{**asdict(i), "severity": i.severity.value} for i in self.issues]

    def __str__(self) -> str:
        if not self.issues:
            return "No issues found."
        return "\n".join(str(i) for i in self.issues)


def validate_specimens(
    specimens: Sequence[Specimen],
    *,
    rows_are_specimens: bool,
    taxonomy: TaxonomyPolicy,
    vocabularies: Mapping[str, Vocabulary],
    extra_issues: Iterable[Issue] = (),
) -> ValidationReport:
    """Run the Phase 1 rules over ``specimens``. ``extra_issues`` are parse-time issues."""
    issues: list[Issue] = list(extra_issues)

    for sid, n in Counter(s.specimen_id for s in specimens).items():
        if n > 1:
            issues.append(
                Issue(Severity.ERROR, "duplicate_id", f"id appears {n} times", sid, "specimen_id")
            )

    ambiguous: Counter[str] = Counter()
    for s in specimens:
        if s.count is not None and s.count <= 0:
            issues.append(
                Issue(
                    Severity.ERROR,
                    "invalid_count",
                    f"count must be a positive integer, got {s.count}",
                    s.specimen_id,
                    "count",
                )
            )
        if s.count is None and not rows_are_specimens:
            issues.append(
                Issue(
                    Severity.WARNING,
                    "missing_count",
                    "count not recorded; the row is excluded from counts "
                    "(declare rows_are_specimens=True if each row is one specimen)",
                    s.specimen_id,
                    "count",
                )
            )
        if s.weight_g is not None and s.weight_g < 0:
            issues.append(
                Issue(
                    Severity.ERROR,
                    "negative_weight",
                    f"weight_g cannot be negative, got {s.weight_g}",
                    s.specimen_id,
                    "weight_g",
                )
            )
        if s.completeness is not None and not 0 <= s.completeness <= 1:
            issues.append(
                Issue(
                    Severity.ERROR,
                    "completeness_out_of_range",
                    f"completeness must be in [0, 1], got {s.completeness}",
                    s.specimen_id,
                    "completeness",
                )
            )
        if s.taxon is not None and taxonomy.is_ambiguous(s.taxon):
            ambiguous[s.taxon] += 1
        for fname, vocab in vocabularies.items():
            value = getattr(s, fname, None)
            value = getattr(value, "value", value)
            if value is not None and value not in vocab:
                issues.append(
                    Issue(
                        Severity.WARNING,
                        "unrecognized_term",
                        f"{value!r} is not in the controlled vocabulary for {fname}",
                        s.specimen_id,
                        fname,
                    )
                )
    for taxon, n in sorted(ambiguous.items()):
        issues.append(
            Issue(
                Severity.WARNING,
                "ambiguous_taxon",
                f"{taxon!r} is an ambiguous identification ({n} rows); "
                "it is kept as its own category and never merged automatically",
                None,
                "taxon",
            )
        )
    return ValidationReport(tuple(issues))
