"""Write the shared conformance corpus.

Each vector carries two kinds of expectation:

  checks  -- written by hand from docs/spec/core.md, before running anything.
             These can fail for the reference implementation too, so they are
             the ones that carry evidence.
  digest  -- filled in from the reference run. This proves the four
             implementations agree with each other; it does not prove any of
             them is right. Only `checks` does that.

Run:  python3 tools/generate_vectors.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gfield.conformance import corpus_dir, run_vector  # noqa: E402

idle = None


def ev(name, *params, observe=None):
    e = {"name": name, "params": [list(p) if isinstance(p, tuple) else p for p in params]}
    if observe:
        e["observe"] = observe
    return e


def obs_only(observe):
    return {"name": None, "params": [], "observe": observe}


TRIANGLE = {
    "dims": ["d0"], "sites": 6,
    "relations": [[0, 1, [600]], [1, 2, [600]], [0, 2, [600]]],
    "observed": {"0,1": 900, "1,2": 600, "0,2": 600},
}

BALANCED = {
    "dims": ["d0"], "sites": 6,
    "relations": [[0, 1, [600]], [1, 2, [600]], [0, 2, [600]]],
    "observed": {"0,1": 600, "1,2": 600, "0,2": 600},
}

CHAIN = {
    "dims": ["d0"], "sites": 8,
    "relations": [[0, 1, [600]], [1, 2, [900]], [2, 3, [900]]],
    "observed": {"0,1": 600, "1,2": 900, "2,3": 900},
}

WEAK = {
    "dims": ["d0"], "sites": 4,
    "relations": [[0, 1, [100]]],
    "observed": {"0,1": 100},
}

VECTORS = [
    {
        "id": "L2-entities-are-derived",
        "level": 2,
        "description": "A cohering, persisting convergence of relations becomes an "
                       "entity. Nothing declared it.",
        "seed": BALANCED,
        "schedule": [idle, idle, idle],
        "expect": {"checks": {"entity_count": 1, "dimension_count": 1,
                              "residual_total": 0, "generated_dimension": False}},
    },
    {
        "id": "L2-weak-coupling-is-not-a-thing",
        "level": 2,
        "description": "Coupling below THETA never condenses, however long it lasts.",
        "seed": WEAK,
        "schedule": [idle, idle, idle, idle],
        "expect": {"checks": {"entity_count": 0, "generated_dimension": False}},
    },
    {
        "id": "L3-events-transform-the-field",
        "level": 3,
        "description": "Branching a convergence produces a second one; the original "
                       "survives, so identity follows the arrows.",
        "seed": BALANCED,
        "schedule": [idle, idle, idle, ev("branch", (0, 1, 2)), idle, idle, idle],
        "expect": {"checks": {"entity_count": 2, "generated_dimension": False}},
    },
    {
        "id": "L3-dissolution-removes-the-class",
        "level": 3,
        "description": "A classification has no existence apart from the relations "
                       "that sustain it.",
        "seed": BALANCED,
        "schedule": [idle, idle, idle, ev("dissolve", (0, 1, 2)), idle, idle, idle],
        "expect": {"checks": {"entity_count": 0}},
    },
    {
        "id": "L4-dimension-generation",
        "level": 4,
        "description": "A persistent, irreducible contradiction generates a new "
                       "coordinate, and that coordinate absorbs exactly what "
                       "produced it.",
        "seed": TRIANGLE,
        "schedule": [idle, idle, idle],
        "expect": {"checks": {"dimension_count": 2, "residual_total": 0,
                              "generated_dimension": True}},
    },
    {
        "id": "L4-accord-generates-nothing",
        "level": 4,
        "description": "Persistence is not sufficient. A field in accord with what "
                       "it is accountable to invents no distinction.",
        "seed": BALANCED,
        "schedule": [idle, idle, idle, idle, idle],
        "expect": {"checks": {"dimension_count": 1, "generated_dimension": False}},
    },
    {
        "id": "L4-a-split-undoes-itself",
        "level": 4,
        "description": "Differentiating while accountability is unchanged regenerates "
                       "the coupling the split removed. A distinction cannot be "
                       "imposed by fiat.",
        "seed": CHAIN,
        "schedule": [idle, idle, idle, ev("differentiate", (0, 1, 2, 3)),
                     idle, idle, idle, idle, idle],
        "expect": {"checks": {"dimension_count": 2, "entity_count": 1,
                              "generated_dimension": True}},
    },
    {
        "id": "L4-a-split-holds-when-accountability-follows",
        "level": 4,
        "description": "The same split, with what the field answers to changing "
                       "alongside it, produces a genuinely new individual. Note "
                       "that differentiation both severs and reinforces, so all "
                       "three couplings must follow, not only the severed one.",
        "seed": CHAIN,
        "schedule": [idle, idle, idle,
                     ev("differentiate", (0, 1, 2, 3),
                        observe={"0,1": 300, "1,2": 1350, "2,3": 1350}),
                     idle, idle, idle],
        "expect": {"checks": {"dimension_count": 1, "entity_count": 1,
                              "generated_dimension": False}},
    },
    {
        "id": "L5-translation-always-loses",
        "level": 5,
        "description": "Every translation between the three ontologies has non-zero "
                       "residue. The vocabularies do not cover one another.",
        "seed": TRIANGLE,
        "schedule": [idle, idle, idle],
        "check_translation": True,
        "expect": {"checks": {"all_losses_positive": True}},
    },
    {
        "id": "L5-observation-changes-what-is-observed",
        "level": 5,
        "description": "A probe with declared back-action alters the entity "
                       "decomposition that follows it.",
        "seed": BALANCED,
        "schedule": [idle, idle, idle],
        "check_observer": {"site": 0, "back_action": 100},
        "expect": {"checks": {"observation_changed_field": True}},
    },
    {
        "id": "L5-detached-observation-must-be-declared",
        "level": 5,
        "description": "A zero back-action is legitimate but must be stated, and "
                       "then genuinely changes nothing.",
        "seed": BALANCED,
        "schedule": [idle, idle, idle],
        "check_observer": {"site": 0, "back_action": 0},
        "expect": {"checks": {"observation_changed_field": False}},
    },
    {
        "id": "L5-worlds-map-only-partially",
        "level": 5,
        "description": "Two worlds weighting different coordinates share only part "
                       "of their support; elsewhere the map is undefined, not "
                       "defaulted.",
        "seed": TRIANGLE,
        "schedule": [idle, idle, idle, ev("new_level", (0, 1, 2)), idle],
        "check_worlds": {"a": {"name": "a", "relevance": {"d0": 1000}},
                         "b": {"name": "b", "relevance": {"d1": 1000}}},
        "expect": {"checks": {"map_is_partial": True}},
    },
]


def main() -> int:
    out = corpus_dir()
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.json"):
        old.unlink()

    failures = []
    for vec in VECTORS:
        hand_written = dict(vec["expect"]["checks"])
        actual = run_vector(vec)

        for k, want in hand_written.items():
            if actual["checks"].get(k) != want:
                failures.append(
                    f"{vec['id']}: spec says {k}={want!r}, "
                    f"implementation gives {actual['checks'].get(k)!r}")

        vec["expect"] = {"checks": actual["checks"], "digest": actual["digest"],
                         "hand_written": hand_written}
        (out / f"{vec['id']}.json").write_text(json.dumps(vec, indent=2) + "\n")

    if failures:
        print("HAND-WRITTEN EXPECTATIONS FAILED:", file=sys.stderr)
        for f in failures:
            print("  " + f, file=sys.stderr)
        return 1

    print(f"wrote {len(VECTORS)} vectors to {out}")
    print("all hand-written spec expectations hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
