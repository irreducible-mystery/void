"""M_t and its revisions.

Implements section 11 of docs/spec/core.md.

The model is never claimed to be complete. It is the best current organisation,
carrying an explicit record of what each revision changed and what it cost.
"""

from __future__ import annotations

from dataclasses import dataclass, field as _field

from .core import Field

SPEC_VERSION = "v0"


@dataclass
class Revision:
    at_tick: int
    changed: str
    lost: str

    def as_json(self) -> dict:
        return {"at_tick": self.at_tick, "changed": self.changed, "lost": self.lost}


@dataclass
class Model:
    """M_t = best current organisation of perspectives, limits, and possibilities.

    Deliberately provides no `is_complete`. There is no predicate here, and none
    may be added, that would license the claim the source text rejects. What it
    provides instead is `limits()`.
    """

    field: Field
    spec_version: str = SPEC_VERSION
    revisions: list[Revision] = _field(default_factory=list)

    def revise(self, new_field: Field, changed: str, lost: str) -> "Model":
        """M_t -> M_{t+1}. Recording what was lost is not optional."""
        if not lost:
            raise ValueError(
                "a revision must state its residue; write 'none identified' if that "
                "is the honest answer, but state it")
        return Model(field=new_field, spec_version=self.spec_version,
                     revisions=self.revisions + [Revision(new_field.tick, changed, lost)])

    def limits(self) -> list[str]:
        """What this model cannot currently say. The honest counterpart to a summary."""
        out = [
            "dimensions are generated only from residual against `observed`; "
            "a contradiction the field is not accountable to cannot be detected",
            "higher cells stop at the 2-cell implied by relation rewriting; "
            "beta (3-cells) is specified but not implemented",
            "the possibility space is bounded by the canonical instance space, "
            "so 'accessible' means accessible-among-enumerated",
        ]
        if len(self.field.dims) == 1:
            out.append("only one coordinate exists; no distinction has yet been generated")
        return out

    def as_json(self) -> dict:
        return {"spec_version": self.spec_version,
                "tick": self.field.tick,
                "dims": list(self.field.dims),
                "revisions": [r.as_json() for r in self.revisions],
                "limits": self.limits()}
