"""Taxonomic policy: rank order and what counts as an ambiguous identification.

``Ovis/Capra``, ``Capra hircus`` and ``Mammalia`` are three different categories. This
module never merges them; it only lets callers *declare* which labels are ambiguous and
how ranks are ordered, so that filters and warnings are explicit and reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass

# From most general to most specific. Override it for other conventions.
DEFAULT_RANKS: tuple[str, ...] = (
    "class",
    "order",
    "family",
    "subfamily",
    "tribe",
    "genus",
    "species",
    "subspecies",
)


@dataclass(frozen=True)
class TaxonomyPolicy:
    ranks: tuple[str, ...] = DEFAULT_RANKS
    # A label containing any of these substrings is considered ambiguous.
    ambiguity_markers: tuple[str, ...] = ("/", "cf.", "aff.")
    # Extra labels declared ambiguous by the researcher (e.g. "Caprinae").
    ambiguous_taxa: frozenset[str] = frozenset()

    def is_ambiguous(self, taxon: str) -> bool:
        return taxon in self.ambiguous_taxa or any(m in taxon for m in self.ambiguity_markers)

    def rank_index(self, rank: str) -> int | None:
        """Position of ``rank`` (0 = most general) or ``None`` if unknown."""
        try:
            return self.ranks.index(rank)
        except ValueError:
            return None
