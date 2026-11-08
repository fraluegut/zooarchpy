"""The :class:`Assemblage`: a validated collection of specimens and the entry point to analyses."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from pathlib import Path

from zooarchpy.io import read_specimens
from zooarchpy.models import Specimen, TaxonomyPolicy, Vocabulary
from zooarchpy.quantification import mne as _mne
from zooarchpy.quantification import mni as _mni
from zooarchpy.quantification import nisp as _nisp
from zooarchpy.quantification import nsp as _nsp
from zooarchpy.reporting import AnalysisResult
from zooarchpy.validation import Issue, ValidationReport, validate_specimens


class Assemblage:
    """Specimens plus the explicit policies needed to interpret them.

    ``rows_are_specimens`` must be declared by the caller when records have no ``count``:
    ZooArchPy does not assume that one row is one specimen.
    """

    def __init__(
        self,
        specimens: Iterable[Specimen],
        *,
        rows_are_specimens: bool = False,
        taxonomy: TaxonomyPolicy | None = None,
        vocabularies: Mapping[str, Vocabulary] | None = None,
        source: str | None = None,
        parse_issues: Iterable[Issue] = (),
    ) -> None:
        self.specimens: tuple[Specimen, ...] = tuple(specimens)
        self.rows_are_specimens = rows_are_specimens
        self.taxonomy = taxonomy or TaxonomyPolicy()
        self.vocabularies: dict[str, Vocabulary] = dict(vocabularies or {})
        self.source = source
        self._parse_issues = tuple(parse_issues)

    @classmethod
    def from_csv(
        cls,
        path: str | Path,
        *,
        rows_are_specimens: bool = False,
        taxonomy: TaxonomyPolicy | None = None,
        vocabularies: Mapping[str, Vocabulary] | None = None,
    ) -> Assemblage:
        specimens, issues = read_specimens(path, rows_are_specimens=rows_are_specimens)
        return cls(
            specimens,
            rows_are_specimens=rows_are_specimens,
            taxonomy=taxonomy,
            vocabularies=vocabularies,
            source=str(path),
            parse_issues=issues,
        )

    def __len__(self) -> int:
        return len(self.specimens)

    def __iter__(self) -> Iterator[Specimen]:
        return iter(self.specimens)

    def effective_count(self, specimen: Specimen) -> int | None:
        """Specimens represented by a row: its ``count``, or 1 only if declared so."""
        if specimen.count is not None:
            return specimen.count
        return 1 if self.rows_are_specimens else None

    def validate(self) -> ValidationReport:
        """Structured errors and warnings. The data are never modified."""
        return validate_specimens(
            self.specimens,
            rows_are_specimens=self.rows_are_specimens,
            taxonomy=self.taxonomy,
            vocabularies=self.vocabularies,
            extra_issues=self._parse_issues,
        )

    def nisp(
        self,
        group_by: str | Sequence[str] = "taxon",
        *,
        taxon: str | Sequence[str] | None = None,
        min_rank: str | None = None,
        ambiguous: str = "separate",
        taxon_map: Mapping[str, str] | None = None,
        include_unidentified: bool = False,
        percent: bool | Sequence[str] = False,
        allow_errors: bool = False,
    ) -> AnalysisResult:
        """Number of Identified Specimens. See :func:`zooarchpy.quantification.nisp.nisp`."""
        return _nisp(
            self,
            group_by,
            taxon=taxon,
            min_rank=min_rank,
            ambiguous=ambiguous,  # type: ignore[arg-type]
            taxon_map=taxon_map,
            include_unidentified=include_unidentified,
            percent=percent,
            allow_errors=allow_errors,
        )

    def mne(
        self,
        *,
        aggregate_by: str | Sequence[str] | None,
        zone_scheme: str,
        counts_are_elements: bool,
        method: str = "zones",
        ambiguous: str = "separate",
        taxon_map: Mapping[str, str] | None = None,
        allow_errors: bool = False,
    ) -> AnalysisResult:
        """Zone-based MNE. See :func:`zooarchpy.quantification.mne.mne`."""
        return _mne(
            self,
            aggregate_by=aggregate_by,
            zone_scheme=zone_scheme,
            counts_are_elements=counts_are_elements,
            method=method,  # type: ignore[arg-type]
            ambiguous=ambiguous,  # type: ignore[arg-type]
            taxon_map=taxon_map,
            allow_errors=allow_errors,
        )

    def mni(
        self,
        *,
        aggregate_by: str | Sequence[str] | None,
        counts_are_elements: bool,
        ambiguous: str = "separate",
        taxon_map: Mapping[str, str] | None = None,
        allow_errors: bool = False,
    ) -> AnalysisResult:
        """Conservative sided-element MNI. See :func:`zooarchpy.quantification.mni.mni`."""
        return _mni(
            self,
            aggregate_by=aggregate_by,
            counts_are_elements=counts_are_elements,
            ambiguous=ambiguous,  # type: ignore[arg-type]
            taxon_map=taxon_map,
            allow_errors=allow_errors,
        )

    def nsp(
        self, group_by: str | Sequence[str] | None = None, *, allow_errors: bool = False
    ) -> AnalysisResult:
        """NR/NSP split into identified and unidentified specimens."""
        return _nsp(self, group_by, allow_errors=allow_errors)
