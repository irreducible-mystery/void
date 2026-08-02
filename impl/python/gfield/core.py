"""Field, relations, and the derivation of entities.

Implements sections 0-2 of docs/spec/core.md.

The central commitment: there is no operation in this module that creates an
entity. Entities are computed from relations, always. See `entities()`.
"""

from __future__ import annotations

from dataclasses import dataclass, field as _field

SCALE = 1000

THETA = 500
PERSISTENCE = 3
COHESION = 600
MAX_SITES = 64


def scale_mul(v: int, f: int) -> int:
    """v * f / SCALE, truncating toward zero.

    Defined explicitly because language division conventions differ: Python
    floor-divides, so a naive `v * f // SCALE` diverges from C-like languages
    on negative values. All four implementations use this rule.
    """
    n = v * f
    q = abs(n) // SCALE
    return q if n >= 0 else -q


def xorshift64s(s: int) -> int:
    """The generator named in spec section 0. Masked to 64 bits at each step."""
    m = (1 << 64) - 1
    s ^= (s >> 12)
    s &= m
    s ^= (s << 25) & m
    s ^= (s >> 27)
    s &= m
    return (s * 0x2545F4914F6CDD1D) & m


@dataclass(frozen=True)
class Relation:
    id: int
    a: int
    b: int
    w: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.a >= self.b:
            raise ValueError(f"relation endpoints must satisfy a < b, got {self.a},{self.b}")

    @property
    def pair(self) -> tuple[int, int]:
        return (self.a, self.b)

    def total(self) -> int:
        return sum(self.w)


@dataclass
class EventRecord:
    tick: int
    name: str
    params: tuple
    note: str = ""

    def as_json(self) -> dict:
        return {"tick": self.tick, "name": self.name,
                "params": list(self.params), "note": self.note}


@dataclass
class Field:
    """A generative field.

    `sites` is a count of addresses, not of things. Nothing in this structure
    *is* an individual; individuals are read off it by `entities()`.
    """

    dims: list[str]
    sites: int
    relations: list[Relation]
    observed: dict[tuple[int, int], int] = _field(default_factory=dict)
    tick: int = 0
    history: list[EventRecord] = _field(default_factory=list)
    candidate_log: list[frozenset[tuple[int, ...]]] = _field(default_factory=list)
    residual_streak: dict[tuple[int, int], int] = _field(default_factory=dict)
    gap_log: list[dict[str, int]] = _field(default_factory=list)
    next_relation_id: int = 0

    @staticmethod
    def seed(dims, sites, relations, observed=None) -> "Field":
        rels = [Relation(i, a, b, tuple(w)) for i, (a, b, w) in enumerate(relations)]
        for r in rels:
            if len(r.w) != len(dims):
                raise ValueError("relation weight arity must equal len(dims)")
        f = Field(dims=list(dims), sites=sites, relations=rels,
                  observed=dict(observed or {}), next_relation_id=len(rels))
        f.candidate_log.append(frozenset(candidates(f)))
        f.gap_log.append({})
        return f

    def copy(self) -> "Field":
        return Field(
            dims=list(self.dims), sites=self.sites, relations=list(self.relations),
            observed=dict(self.observed), tick=self.tick, history=list(self.history),
            candidate_log=list(self.candidate_log),
            residual_streak=dict(self.residual_streak),
            gap_log=list(self.gap_log), next_relation_id=self.next_relation_id,
        )

    def add_relation(self, a: int, b: int, w) -> None:
        if a == b:
            raise ValueError("a relation may not join a site to itself")
        lo, hi = (a, b) if a < b else (b, a)
        self.relations.append(Relation(self.next_relation_id, lo, hi, tuple(w)))
        self.next_relation_id += 1

    def digest(self) -> dict:
        """Canonical, comparable summary. The conformance corpus compares these."""
        return {
            "dims": list(self.dims),
            "sites": self.sites,
            "tick": self.tick,
            "relations": [[r.a, r.b, list(r.w)] for r in
                          sorted(self.relations, key=lambda r: (r.a, r.b, r.id))],
            "entities": [list(s) for s in entities(self)],
            "residual_total": residual_total(self),
        }


# --- derivation (spec section 2) ------------------------------------------

def coupling(f: Field) -> dict[tuple[int, int], int]:
    acc: dict[tuple[int, int], int] = {}
    for r in f.relations:
        acc[r.pair] = acc.get(r.pair, 0) + sum(abs(x) for x in r.w)
    return acc


def _components(f: Field, cpl: dict[tuple[int, int], int]) -> list[tuple[int, ...]]:
    parent = list(range(f.sites))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for (a, b) in sorted(cpl):
        if cpl[(a, b)] >= THETA:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)

    groups: dict[int, list[int]] = {}
    for s in range(f.sites):
        groups.setdefault(find(s), []).append(s)
    return sorted(tuple(sorted(g)) for g in groups.values() if len(g) >= 2)


def cohesion_holds(f: Field, support: tuple[int, ...]) -> bool:
    cpl = coupling(f)
    inside = set(support)
    internal = boundary = 0
    for (a, b), c in cpl.items():
        na, nb = a in inside, b in inside
        if na and nb:
            internal += c
        elif na or nb:
            boundary += c
    return internal * SCALE >= COHESION * (internal + boundary)


def candidates(f: Field) -> list[tuple[int, ...]]:
    """Components that both hold together and clear the coupling threshold.

    A candidate is not yet an entity: it has cohered but not yet lasted.
    """
    cpl = coupling(f)
    return [s for s in _components(f, cpl) if cohesion_holds(f, s)]


def entities(f: Field) -> list[tuple[int, ...]]:
    """Persistent convergences of relations (section 1 of the source text).

    A candidate becomes an entity only by surviving unchanged for PERSISTENCE
    consecutive ticks. There is deliberately no way to declare one.
    """
    if len(f.candidate_log) < PERSISTENCE:
        return []
    recent = f.candidate_log[-PERSISTENCE:]
    return sorted(s for s in recent[-1] if all(s in step for step in recent))


# --- accountability (spec section 5) --------------------------------------

def residual(f: Field, pair: tuple[int, int]) -> int:
    modeled = sum(r.total() for r in f.relations if r.pair == pair)
    return f.observed.get(pair, 0) - modeled


def residual_total(f: Field) -> int:
    pairs = set(f.observed) | {r.pair for r in f.relations}
    return sum(abs(residual(f, p)) for p in sorted(pairs))
