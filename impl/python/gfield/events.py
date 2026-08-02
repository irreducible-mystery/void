"""The eight grammar rules, which are also the event vocabulary.

Implements sections 3-4 of docs/spec/core.md.

Section 7 of the source text lists eight rule families that generate structure;
section 2 makes transformation the primitive unit. They are the same thing, so
the grammar *is* the set of legal events. Nothing else may alter a field.
"""

from __future__ import annotations

from dataclasses import dataclass

from .core import (MAX_SITES, SCALE, EventRecord, Field, candidates, coupling,
                   scale_mul)

BOUNDARY_DECAY = 500
REINFORCE = 1500
JOIN_W = 700
FEEDBACK_W = 600
LEVEL_W = 800
BECOMING_WINDOW = 2


@dataclass(frozen=True)
class Event:
    name: str
    params: tuple

    def key(self) -> str:
        """Canonical identity, fixed across implementations.

        `name(p;p)` with set-valued parameters comma-joined. Defined explicitly
        because the instance space is *sorted* by this string, and a
        language-native repr would order it differently -- which would change
        which terms an ontology reads and therefore the translation losses.
        """
        parts = [",".join(str(x) for x in p) if isinstance(p, (tuple, list)) else str(p)
                 for p in self.params]
        return f"{self.name}({';'.join(parts)})"


def bisect(f: Field, support: tuple[int, ...]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Canonical minimum-coupling bisection by prefix split.

    Deterministic by construction, so no search heuristic and no tie-breaking
    policy is needed beyond 'smallest prefix wins'.
    """
    cpl = coupling(f)
    best_k, best_cross = 1, None
    for k in range(1, len(support)):
        left, right = set(support[:k]), set(support[k:])
        cross = sum(c for (a, b), c in cpl.items()
                    if (a in left and b in right) or (a in right and b in left))
        if best_cross is None or cross < best_cross:
            best_k, best_cross = k, cross
    return support[:best_k], support[best_k:]


def _pair_class(r, s: set[int]) -> str:
    na, nb = r.a in s, r.b in s
    if na and nb:
        return "inside"
    if na or nb:
        return "crossing"
    return "outside"


# --- the eight rules -------------------------------------------------------

def _boundary_coupling(f: Field, s: set[int]) -> int:
    return sum(c for (a, b), c in coupling(f).items() if (a in s) != (b in s))


def gap(f: Field, e: Event) -> int:
    """Non-negative distance to enablement. Zero exactly when the event is possible."""
    p = e.params
    if e.name == "form_boundary":
        s = set(p[0])
        return 0 if s and _boundary_coupling(f, s) > 0 else 1
    if e.name == "differentiate":
        return max(0, 4 - len(p[0]))
    if e.name == "join":
        s, t = set(p[0]), set(p[1])
        return 0 if s and t and not (s & t) else 1
    if e.name in ("branch", "repeat"):
        return max(0, f.sites + len(p[0]) - MAX_SITES)
    if e.name == "feedback":
        return 0 if any(r.pair == (p[0], p[1]) for r in f.relations) else 1
    if e.name == "new_level":
        return max(0, 2 - len(p[0])) + (0 if f.sites < MAX_SITES else 1)
    if e.name == "dissolve":
        s = set(p[0])
        return 0 if any(_pair_class(r, s) == "inside" for r in f.relations) else 1
    raise ValueError(f"unknown event {e.name}")


def enabled(f: Field, e: Event) -> bool:
    return gap(f, e) == 0


def apply(f: Field, e: Event, note: str = "") -> Field:
    """Return a new field. The only way a field state may come into being."""
    if not enabled(f, e):
        raise ValueError(f"precondition not met for {e.key()}")
    g = f.copy()
    p = e.params

    if e.name == "form_boundary":
        s = set(p[0])
        g.relations = [
            r if _pair_class(r, s) != "crossing"
            else type(r)(r.id, r.a, r.b, tuple(scale_mul(x, BOUNDARY_DECAY) for x in r.w))
            for r in g.relations
        ]

    elif e.name == "differentiate":
        left, right = bisect(f, tuple(p[0]))
        ls, rs = set(left), set(right)
        out = []
        for r in g.relations:
            crossing = (r.a in ls and r.b in rs) or (r.a in rs and r.b in ls)
            intra = (r.a in ls and r.b in ls) or (r.a in rs and r.b in rs)
            factor = BOUNDARY_DECAY if crossing else (REINFORCE if intra else None)
            out.append(r if factor is None
                       else type(r)(r.id, r.a, r.b, tuple(scale_mul(x, factor) for x in r.w)))
        g.relations = out

    elif e.name == "join":
        a, b = min(p[0]), min(p[1])
        g.add_relation(a, b, [JOIN_W] + [0] * (len(g.dims) - 1))

    elif e.name in ("branch", "repeat"):
        src = tuple(p[0])
        mapping = {s: g.sites + i for i, s in enumerate(src)}
        g.sites += len(src)
        inside = set(src)
        for r in list(f.relations):
            cls = _pair_class(r, inside)
            if cls == "inside":
                g.add_relation(mapping[r.a], mapping[r.b], r.w)
            elif cls == "crossing" and e.name == "repeat":
                if r.a in inside:
                    g.add_relation(mapping[r.a], r.b, r.w)
                else:
                    g.add_relation(r.a, mapping[r.b], r.w)

    elif e.name == "feedback":
        g.add_relation(p[0], p[1], [FEEDBACK_W] + [0] * (len(g.dims) - 1))

    elif e.name == "new_level":
        level = g.sites
        g.sites += 1
        for m in sorted(p[0]):
            g.add_relation(m, level, [LEVEL_W] + [0] * (len(g.dims) - 1))

    elif e.name == "dissolve":
        s = set(p[0])
        g.relations = [r for r in g.relations if _pair_class(r, s) != "inside"]

    g.history.append(EventRecord(tick=g.tick, name=e.name, params=p, note=note))
    return g


# --- the instance space (spec section 4) ----------------------------------

def instances(f: Field) -> list[Event]:
    """The canonical, finite space of event instances considered at a field.

    Bounded by construction so that possibility sets are computable and
    identical across implementations: supports come from current candidates,
    and pairs come from existing relations.
    """
    out: list[Event] = []
    cands = candidates(f)
    for s in cands:
        for name in ("form_boundary", "differentiate", "branch", "repeat",
                     "new_level", "dissolve"):
            out.append(Event(name, (s,)))
    for i, s in enumerate(cands):
        for t in cands[i + 1:]:
            out.append(Event("join", (s, t)))
    for pair in sorted({r.pair for r in f.relations}):
        out.append(Event("feedback", pair))
    return sorted(out, key=lambda e: e.key())


def possibility(f: Field) -> list[Event]:
    """P(x) = transformations accessible from x."""
    return [e for e in instances(f) if enabled(f, e)]


def becoming_accessible(f: Field) -> list[Event]:
    """Events whose distance to enablement is strictly decreasing.

    Our reading of 'what is becoming accessible', which the source text names
    but does not define. Tracked as contradictions/003.
    """
    if len(f.gap_log) < BECOMING_WINDOW + 1:
        return []
    window = f.gap_log[-(BECOMING_WINDOW + 1):]
    out = []
    for e in instances(f):
        k = e.key()
        series = [step.get(k) for step in window]
        if any(v is None for v in series):
            continue
        if series[-1] > 0 and all(b < a for a, b in zip(series, series[1:])):
            out.append(e)
    return out


def snapshot_gaps(f: Field) -> dict[str, int]:
    return {e.key(): gap(f, e) for e in instances(f)}


def state(f: Field) -> dict:
    """state = what is actual + what is accessible + what is becoming accessible."""
    return {
        "actual": f.digest(),
        "accessible": [e.key() for e in possibility(f)],
        "becoming": [e.key() for e in becoming_accessible(f)],
    }
