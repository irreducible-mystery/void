"""Dimension generation, the coupled step, and individuation.

Implements sections 5-7 of docs/spec/core.md. This is the load-bearing module:
sections 5 and 6 together are the claim that distinguishes a generative field
from a dynamic one.
"""

from __future__ import annotations

from dataclasses import dataclass, field as _field

from .core import (PERSISTENCE, EventRecord, Field, Relation, candidates,
                   entities, residual, residual_total)
from .events import Event, apply, bisect, possibility, snapshot_gaps

TAU = 100
WINDOW = 3


# --- dimension generation (spec section 5) --------------------------------

def contradictions(f: Field) -> list[tuple[int, int]]:
    pairs = set(f.observed) | {r.pair for r in f.relations}
    return sorted(p for p in pairs if abs(residual(f, p)) > TAU)


def reducible_within_space(f: Field) -> bool:
    """Can any presently accessible transformation reduce the total residual?

    The source text requires that a contradiction be *irreducible* before it
    generates a distinction, not merely persistent. This is that test.
    """
    base = residual_total(f)
    for e in possibility(f):
        try:
            if residual_total(apply(f, e)) < base:
                return True
        except ValueError:
            continue
    return False


def generate_dimension(f: Field) -> Field:
    """F_n -> F_{n+1}: add the coordinate the old space could not express.

    The content of the new coordinate is not arbitrary. It is exactly the
    residual -- the part of what the field is accountable to that the existing
    dimensions failed to account for. Absorbing it drives the total residual to
    zero, which is the property conformance checks.
    """
    g = f.copy()
    name = f"d{len(g.dims)}"
    g.dims.append(name)

    first_of_pair: dict[tuple[int, int], int] = {}
    for r in sorted(g.relations, key=lambda r: (r.a, r.b, r.id)):
        first_of_pair.setdefault(r.pair, r.id)

    g.relations = [
        Relation(r.id, r.a, r.b,
                 r.w + (residual(f, r.pair) if first_of_pair[r.pair] == r.id else 0,))
        for r in g.relations
    ]

    # A pair the old space could not express at all gets its first relation here.
    covered = {r.pair for r in g.relations}
    for pair in sorted(set(g.observed) - covered):
        res = residual(f, pair)
        if res != 0:
            g.add_relation(pair[0], pair[1], [0] * (len(g.dims) - 1) + [res])

    g.residual_streak = {}
    g.history.append(EventRecord(
        tick=g.tick, name="dimension", params=(name,),
        note="persistent contradiction -> new distinction -> expanded space"))
    g.history.append(EventRecord(
        tick=g.tick, name="migration", params=(name,),
        note=f"all prior records extended with coordinate {name}; "
             f"prior fields take 0 there"))
    return g


# --- the coupled step (spec section 6) ------------------------------------

def step(f: Field, event: Event | None = None,
         observe: dict[tuple[int, int], int] | None = None) -> Field:
    """One tick of both dynamics.

    The inner loop (the event) moves the field within its space. The outer loop
    (dimension generation) may change that space, in the same tick, immediately
    after. The seam between them is visible in `history` by design.

    `observe` supplies what the field is accountable to on this tick. It is
    exogenous -- the field does not choose it, and without a way to supply it a
    driver could only ever change the model, never the world it answers to.
    """
    g = apply(f, event) if event is not None else f.copy()
    g.tick += 1
    if observe:
        g.observed.update(observe)
        g.history.append(EventRecord(tick=g.tick, name="accountability",
                                     params=tuple(sorted(observe)),
                                     note="what the field answers to changed"))

    for pair in sorted(set(g.observed) | {r.pair for r in g.relations}):
        if abs(residual(g, pair)) > TAU:
            g.residual_streak[pair] = g.residual_streak.get(pair, 0) + 1
        else:
            g.residual_streak[pair] = 0

    persistent = any(v >= WINDOW for v in g.residual_streak.values())
    if persistent and not reducible_within_space(g):
        g = generate_dimension(g)

    g.candidate_log.append(frozenset(candidates(g)))
    g.gap_log.append(snapshot_gaps(g))
    return g


def _entry(item) -> tuple[Event | None, dict | None]:
    """A schedule entry is an event, or an (event, accountability-update) pair."""
    if isinstance(item, tuple) and len(item) == 2 and (
            item[0] is None or isinstance(item[0], Event)):
        return item[0], item[1]
    return item, None


def run(f: Field, schedule: list) -> Field:
    for item in schedule:
        e, obs = _entry(item)
        f = step(f, e, obs)
    return f


# --- individuation (spec section 7) ---------------------------------------

@dataclass
class Individual:
    support: tuple[int, ...]
    born_at: int
    formation_event: str
    maintained_by: list[int] = _field(default_factory=list)
    dissolution_condition: str = "coupling below THETA"
    suppressed: list[tuple[int, ...]] = _field(default_factory=list)
    died_at: int | None = None

    def as_json(self) -> dict:
        return {"support": list(self.support), "born_at": self.born_at,
                "formation_event": self.formation_event,
                "maintained_by": self.maintained_by,
                "dissolution_condition": self.dissolution_condition,
                "suppressed": [list(s) for s in self.suppressed],
                "died_at": self.died_at}


class Registry:
    """Tracks individuation across a run.

    Individuals are temporary by construction: when a support stops satisfying
    the entity criterion the record is closed with `died_at`, never deleted.
    What was suppressed at the branch point is kept, because 'which alternatives
    were suppressed?' is one of the questions the framework is required to answer.
    """

    def __init__(self) -> None:
        self.open: dict[tuple[int, ...], Individual] = {}
        self.closed: list[Individual] = []
        # A split does not become an individual on the tick it happens: the new
        # support must persist first. So what was suppressed at the branch point
        # is held open until the individuation it caused actually arrives.
        self.pending: list[tuple[int, ...]] = []
        self.pending_ttl: int = 0

    def observe(self, f: Field, formation_event: str = "seed",
                suppressed: list[tuple[int, ...]] | None = None) -> None:
        if suppressed:
            self.pending, self.pending_ttl = list(suppressed), PERSISTENCE + 1

        present = set(entities(f))
        born = sorted(present - set(self.open))
        for support in born:
            self.open[support] = Individual(
                support=support, born_at=f.tick, formation_event=formation_event,
                maintained_by=sorted(r.id for r in f.relations
                                     if r.a in support and r.b in support),
                suppressed=list(self.pending) if self.pending_ttl > 0 else [])
        if born and self.pending_ttl > 0:
            self.pending, self.pending_ttl = [], 0
        elif self.pending_ttl > 0:
            self.pending_ttl -= 1
        for support in sorted(set(self.open) - present):
            ind = self.open.pop(support)
            ind.died_at = f.tick
            self.closed.append(ind)

    def all(self) -> list[Individual]:
        return sorted(self.closed + list(self.open.values()),
                      key=lambda i: (i.born_at, i.support))


def alternatives(f: Field, support: tuple[int, ...]) -> list[tuple[int, ...]]:
    """Every viable bisection of a support, so the unchosen ones can be recorded."""
    chosen, _ = bisect(f, support)
    return [support[:k] for k in range(1, len(support)) if support[:k] != chosen]


def run_tracked(f: Field, schedule: list) -> tuple[Field, Registry]:
    reg = Registry()
    reg.observe(f)
    for item in schedule:
        e, obs = _entry(item)
        suppressed: list[tuple[int, ...]] = []
        if e is not None and e.name == "differentiate":
            suppressed = alternatives(f, tuple(e.params[0]))
        f = step(f, e, obs)
        reg.observe(f, formation_event=(e.name if e else "drift"), suppressed=suppressed)
    return f, reg
