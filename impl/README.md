# Implementations

Four implementations of [`docs/spec/core.md`](../docs/spec/core.md). Three run
the [shared corpus](../conformance); one proves theorems.

| | Role | Verify with |
|---|---|---|
| [`python/`](python) | reference implementation — the corpus digests are generated from it | `PYTHONPATH=. python3 -m pytest tests/ -q` |
| [`typescript/`](typescript) | independent implementation | `npm install && npm test` |
| [`julia/`](julia) | independent implementation | `julia --project=. -e 'using Pkg; Pkg.test()'` |
| [`lean/`](lean) | formalisation — states the spec's claims as theorems | `lake build` |

## Why four

Agreement between independent implementations catches drift: if one diverges,
the spec was underspecified somewhere, and that gap is a finding rather than a
bug to be papered over. Several details in the spec exist only because a port
exposed them — the truncation-toward-zero rule (§0), and the canonical event-key
ordering (§3), both of which would otherwise have diverged silently.

Lean's role is different and is the reason it is here. The other three *sample*
the spec's claims on twelve fields. Lean states them for all fields. That
difference is not decorative: `contradictions/004` is a requirement that all
twelve vectors and three implementations agreed to satisfy, and that Lean proved
false.

## Naming

Behaviour is identical; names follow each language's idiom. Julia uses
`advance` and `apply_event` for the spec's `step` and `apply`, and
`observe_read` for `read`, to avoid shadowing `Base`. The corpus is the arbiter,
not the identifiers.
