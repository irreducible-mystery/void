"""Ontologies, lossy translation, worlds, and observers.

Implements sections 8-10 of docs/spec/core.md -- the reflexive level, where the
field carries several incompatible readings of itself and where observing is a
move inside the field rather than a look from outside it.
"""

from __future__ import annotations

from dataclasses import dataclass

from .core import SCALE, Relation, EventRecord, Field, coupling, entities, scale_mul
from .events import instances

# --- ontologies (spec section 8) ------------------------------------------

ONTOLOGIES = {
    "O1": ("objects", "properties", "causes"),
    "O2": ("processes", "relations", "constraints"),
    "O3": ("agents", "meanings", "purposes"),
}


def read_ontology(f: Field, name: str, observers: list["Observer"] | None = None) -> list[str]:
    """A view of the field in one vocabulary. Total, canonical, and partial in scope."""
    obs = observers or []
    terms: list[str] = []
    if name == "O1":
        terms += [f"object:{'-'.join(map(str, s))}" for s in entities(f)]
        terms += [f"property:{d}" for d in f.dims]
        terms += [f"cause:{a}-{b}" for (a, b) in sorted({r.pair for r in f.relations})]
    elif name == "O2":
        terms += [f"process:{n}" for n in sorted({h.name for h in f.history})]
        terms += [f"relation:{a}-{b}" for (a, b) in sorted({r.pair for r in f.relations})]
        terms += [f"constraint:{n}" for n in sorted({e.name for e in instances(f)})]
    elif name == "O3":
        terms += [f"agent:{o.site}" for o in sorted(obs, key=lambda o: o.site)]
        terms += [f"meaning:{o.site}" for o in sorted(obs, key=lambda o: o.site)]
        terms += [f"purpose:{e.key()}" for e in instances(f)[:1]]
    else:
        raise ValueError(f"unknown ontology {name}")
    return terms


# What each vocabulary can say in each other vocabulary. Absence is the point:
# an empty target is untranslatable, and becomes residue rather than being dropped.
CORRESPONDENCE = {
    ("O1", "O2"): {"object": "process", "cause": "relation", "property": None},
    ("O2", "O1"): {"process": "object", "relation": "cause", "constraint": None},
    ("O1", "O3"): {"object": "agent", "property": "meaning", "cause": None},
    ("O3", "O1"): {"agent": "object", "meaning": "property", "purpose": None},
    ("O2", "O3"): {"process": "purpose", "relation": "meaning", "constraint": None},
    ("O3", "O2"): {"meaning": "relation", "purpose": "process", "agent": None},
}


@dataclass
class Translation:
    source: str
    target: str
    image: list[str]
    residue: list[str]

    def loss(self) -> int:
        """|residue| / |source terms|, fixed point. Zero only if nothing was lost."""
        total = len(self.image) + len(self.residue)
        if total == 0:
            return 0
        return (len(self.residue) * SCALE) // total

    def as_json(self) -> dict:
        return {"source": self.source, "target": self.target,
                "image": self.image, "residue": self.residue, "loss": self.loss()}


def translate(terms: list[str], source: str, target: str) -> Translation:
    """F : O_i -> O_j, returning both the translation and its residue.

    There is deliberately no variant of this function that returns the image
    alone. A caller cannot silently discard what did not survive.
    """
    table = CORRESPONDENCE[(source, target)]
    image, residue = [], []
    for t in terms:
        kind, _, rest = t.partition(":")
        mapped = table.get(kind)
        (image if mapped else residue).append(
            f"{mapped}:{rest}" if mapped else t)
    return Translation(source, target, image, residue)


# --- worlds (spec section 9) ----------------------------------------------

@dataclass
class World:
    name: str
    relevance: dict[str, int]

    def support(self, f: Field) -> list[int]:
        live = {i for i, d in enumerate(f.dims) if self.relevance.get(d, 0) != 0}
        sites: set[int] = set()
        for r in f.relations:
            if any(i in live and r.w[i] != 0 for i in range(len(r.w))):
                sites.update((r.a, r.b))
        return sorted(sites)


def partial_map(f: Field, wi: World, wj: World) -> dict[int, int]:
    """F_ij : W_i -> W_j, defined only where both worlds have purchase.

    Sites outside the overlap are absent from the mapping. They are never given
    a default value, because a default would assert a correspondence that the
    worlds do not have.
    """
    si, sj = set(wi.support(f)), set(wj.support(f))
    return {s: s for s in sorted(si & sj)}


def shared_world(f: Field, wi: World, wj: World, name: str) -> World:
    """Interaction can create a world that neither party inhabited before."""
    dims = {d: min(wi.relevance.get(d, 0), wj.relevance.get(d, 0)) for d in f.dims}
    return World(name=name, relevance={d: v for d, v in dims.items() if v != 0})


# --- observers (spec section 10) ------------------------------------------

@dataclass
class Observer:
    """An observer is a site in the field, not a viewpoint outside it.

    `back_action` must be given explicitly. Zero is a legitimate value but must
    be asserted, never assumed: principle 6 forbids treating detachment as the
    default case.
    """

    site: int
    back_action: int

    def __post_init__(self) -> None:
        if self.back_action is None:
            raise ValueError("back_action must be declared explicitly, even when zero")


def read(f: Field, o: Observer) -> tuple[int, Field]:
    """Measure, and in measuring, change what was measured.

    Returns the reading together with the field as the reading left it.
    """
    reading = sum(c for (a, b), c in coupling(f).items() if a == o.site or b == o.site)
    if o.back_action == 0:
        return reading, f

    g = f.copy()
    g.relations = [
        r if o.site not in (r.a, r.b)
        else Relation(r.id, r.a, r.b, tuple(scale_mul(x, o.back_action) for x in r.w))
        for r in g.relations
    ]
    g.history.append(EventRecord(tick=g.tick, name="observation", params=(o.site,),
                                 note=f"back_action={o.back_action}"))
    return reading, g
