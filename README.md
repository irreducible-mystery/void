# void

**The generative field** — a representation in which new positions, relations,
and *dimensions* can emerge, rather than one that maps a fixed inventory of
things.

> A multitude says, "There are many."
> A structured field says, "The many have relations."
> A generative field says: "The relations generate new forms of multiplicity —
> and can transform what it means for something to count as one, many, related,
> or possible."

One specification, four implementations, and a shared corpus that holds them to
it.

```
docs/spec/core.md      normative, language-independent
conformance/vectors/   12 shared vectors every implementation must pass
impl/python            reference implementation           30 tests
impl/typescript        independent implementation         12 tests
impl/julia             independent implementation         67 assertions
impl/lean              formalisation — proofs, not samples
contradictions/        open problems, tracked as first-class objects
revisions/             M_t -> M_{t+1}, each stating what it lost
```

## The ladder

The source text's own summary is the roadmap. Levels 0–3 are ordinary. Level 4
is the name of the project. Level 6 is a constraint on what may be claimed, not
a feature to ship.

| Level | | | Status |
|---|---|---|---|
| 0 | binary | $A$ or $B$ | — |
| 1 | multitude | $\{A, B, C, \ldots\}$ | — |
| 2 | structured field | positions plus relations and dimensions | implemented |
| 3 | dynamic field | positions and relations changing over time | implemented |
| **4** | **generative field** | **new positions, relations, and dimensions emerge** | **implemented** |
| 5 | reflexive field | the field models and modifies its own organization | partial |
| 6 | open becoming | no fixed inventory of future possibilities | not a target |

## What level 4 means here, concretely

The field is accountable to couplings it does not control. When what it can
express falls short of that, the gap is a contradiction. A contradiction that
**persists** and that no available transformation can **reduce** causes the field
to generate a new coordinate — and the content of that coordinate is exactly
what the old space could not express, so generating it drives the shortfall to
zero.

That last property is proved for all fields, not sampled:

```lean
theorem absorption (observed : Int) (r : Relation) (rest : List Relation) :
    residualOf observed (absorbHead (residualOf observed (r :: rest)) (r :: rest)) = 0
```

A consequence worth stating, because it was derived rather than designed: **a
distinction cannot be imposed by fiat.** Split a convergence while the field is
still accountable to the old coupling, and it regenerates that coupling as a new
dimension — the split undoes itself. Making a distinction stick requires that
what the field answers to changes too.

## The invariants

Everything here is accountable to the text's seven closing principles, enforced
as executable tests in the implementations and as
[repository lint](tools/lint_principles.py) on the project itself:

1. relations before isolated entities — *no API can declare an entity; they are derived*
2. events before static states — *no field state exists without a recorded transformation*
3. transformations before classifications — *dissolve the relations and the class goes*
4. individuation before fixed individuals — *every individual carries its formation, its dissolution condition, and what was suppressed*
5. possibility-generation before a fixed possibility space — *the space grows*
6. co-evolution before detached observation — *back-action must be declared, even when zero*
7. revisability before final completeness — *every revision states what it lost*

## Running it

```bash
cd impl/python     && PYTHONPATH=. python3 -m pytest tests/ -q
cd impl/typescript && npm install && npm test
cd impl/julia      && julia --project=. -e 'using Pkg; Pkg.test()'
cd impl/lean       && lake build
python3 tools/lint_principles.py
```

## Reading order

| | |
|---|---|
| [`docs/source/`](docs/source/geometry-and-dynamic-systems-1.md) | the canonical text, transcribed unaltered |
| [`docs/inventory.md`](docs/inventory.md) | what each of the twelve shifts demands, and what the text leaves open |
| [`docs/spec/core.md`](docs/spec/core.md) | the normative specification |
| [`DECISIONS.md`](DECISIONS.md) | what was chosen, and what it cost |
| [`RELATED.md`](RELATED.md) | lineage, computational neighbours, and where this differs |
| [`contradictions/`](contradictions/) | what is still wrong, including in our own work |
| [`PLANS.md`](PLANS.md) | the three plans and their sequencing |

## Status

Level 4 has runnable, cross-checked content. Level 5 is partial. One
requirement in the specification is **known not to hold** —
[`contradictions/004`](contradictions/004-loss-can-round-to-zero.md), found by
the Lean formalisation after three implementations and twelve vectors agreed to
miss it.

In keeping with principle 7, no artifact in this repository asserts
completeness, and CI fails if one starts to.
