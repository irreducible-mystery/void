# Conformance corpus

Twelve vectors that every implementation in [`impl/`](../impl) must satisfy.
This is what makes four implementations one project rather than four projects.

## What a vector contains

```jsonc
{
  "id": "L4-dimension-generation",
  "level": 4,
  "description": "...",
  "seed":     { "dims": [...], "sites": 6, "relations": [...], "observed": {...} },
  "schedule": [ null, null, null ],          // null = idle tick
  "expect": {
    "hand_written": { ... },   // written from the spec, before running anything
    "checks":       { ... },   // the full check set, from the reference run
    "digest":       { ... }    // canonical field state, from the reference run
  }
}
```

## The two kinds of expectation, and why the distinction matters

**`hand_written`** is derived from [`docs/spec/core.md`](../docs/spec/core.md)
before any code runs. These can fail for the reference implementation too, so
these are the ones that carry evidence.

**`digest` and `checks`** are generated from the Python reference. They prove the
four implementations *agree with each other*. They do not prove any of them is
right.

That distinction is not pedantry. `contradictions/004` is a defect that all
twelve vectors and three implementations agreed to miss — the corpus was
internally consistent and collectively wrong. Cross-implementation agreement is
a check on drift, not on truth. The Lean formalisation exists to supply what the
corpus structurally cannot.

## Coverage

| Level | Vectors | Assert |
|---|---|---|
| 2 | 2 | entities derived, not declared; weak coupling never condenses |
| 3 | 2 | events transform fields; dissolving relations dissolves the class |
| 4 | 4 | dimension generation fires, and only on persistent *irreducible* contradiction; absorption drives residual to zero; a split undoes itself unless accountability follows |
| 5 | 4 | translation loses; observation perturbs; declared detachment does not; worlds map partially |
| 6 | 0 | — |

**Level 6 has no vectors, deliberately.** "No fixed inventory of future
possibilities" is a constraint on what may be asserted. A suite claiming to
verify it would be asserting the completeness the source text rejects.

## Regenerating

```bash
cd impl/python && PYTHONPATH=. python3 tools/generate_vectors.py
```

The generator re-checks every hand-written expectation against the spec and
fails loudly if one no longer holds — so a change in behaviour cannot silently
rewrite the expectations that were supposed to constrain it. CI additionally
fails if the committed corpus is stale.

## Adding a vector

1. Add it to `VECTORS` in `impl/python/tools/generate_vectors.py` with
   `expect.checks` written **by hand from the spec**.
2. Regenerate. If your hand-written expectation fails, either the spec or the
   implementation is wrong — decide which before touching either.
3. Run the other three implementations. If they disagree, the spec is
   underspecified; that is a finding, and belongs in
   [`contradictions/`](../contradictions).
