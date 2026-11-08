"""Configurable controlled vocabularies."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Vocabulary:
    """A named set of accepted terms for one field (taxa, elements, phases...).

    Terms are compared exactly (case-sensitive): ZooArchPy never guesses that two labels
    are equivalent. Map labels explicitly if you need to.
    """

    field: str
    terms: frozenset[str]

    @classmethod
    def of(cls, field: str, terms: Iterable[str]) -> Vocabulary:
        return cls(field, frozenset(terms))

    def __contains__(self, term: object) -> bool:
        return term in self.terms
