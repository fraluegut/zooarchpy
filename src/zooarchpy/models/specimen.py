"""The :class:`Specimen` entity: one record of a faunal collection.

Three distinct states are never conflated (design principle 2 and section 3 of the
brief): a value that was *not recorded* (``None`` / ``Observation.UNKNOWN``), an
*observed absence* (``Observation.ABSENT``) and a feature that *does not apply*
(``Observation.NOT_APPLICABLE``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Side(StrEnum):
    """Body side of an element. ``None`` on a specimen means "not recorded"."""

    LEFT = "left"
    RIGHT = "right"
    AXIAL = "axial"
    INDETERMINATE = "indeterminate"


class FusionStatus(StrEnum):
    FUSED = "fused"
    UNFUSED = "unfused"
    INDETERMINATE = "indeterminate"


class Observation(StrEnum):
    """Tri-state-plus observation of a modification (cut marks, carnivore marks...)."""

    PRESENT = "present"
    ABSENT = "absent"  # observed and not there
    NOT_APPLICABLE = "not_applicable"  # cannot be observed on this specimen
    UNKNOWN = "unknown"  # not recorded: NEVER equivalent to ABSENT


@dataclass(frozen=True)
class Specimen:
    """One registered specimen (or aggregated lot, see ``count``).

    Only ``specimen_id``, ``site`` and ``context`` are mandatory: every record must be
    tied to its archaeological provenance. Each algorithm declares what else it needs.
    """

    specimen_id: str
    site: str
    context: str
    phase: str | None = None
    taxon: str | None = None
    taxon_rank: str | None = None
    element: str | None = None
    side: Side | None = None
    portion: str | None = None
    diagnostic_zones: tuple[str, ...] = ()
    count: int | None = None
    weight_g: float | None = None
    completeness: float | None = None
    fusion_status: FusionStatus | None = None
    tooth: str | None = None
    tooth_wear_stage: str | None = None
    age_class: str | None = None
    cut_marks: Observation = Observation.UNKNOWN
    burning: str | None = None
    carnivore_marks: Observation = Observation.UNKNOWN
    measurements: dict[str, float] = field(default_factory=dict)
    identification_confidence: str | None = None
    refit_group: str | None = None

    def __post_init__(self) -> None:
        for name in ("specimen_id", "site", "context"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Specimen.{name} is required and cannot be empty")

    @property
    def is_identified(self) -> bool:
        """True when a taxon was recorded (says nothing about how precise it is)."""
        return self.taxon is not None
