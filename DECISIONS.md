# Decisions

Answers to the questions in [`PLANS.md`](PLANS.md), and what followed from them.
Recorded so that later work can see what was chosen and reopen it deliberately
rather than by drift.

## 1. What this should be — **all three, sequenced**

Not one of the three plans but all of them, in dependency order: the Commons
first because it is already true, the Engine next because it is the only part
that can be *wrong*, the Instrument last because it is honest only once an
engine exists.

**Consequence:** a monorepo. `docs/` + `contradictions/` + `revisions/` (B),
`impl/` + `conformance/` (A), and `app/` (C, not yet begun).

## 2. Grounding — **abstract, grounded in four languages**

No domain commitment. The generative field is specified abstractly, and the
grounding comes from independent implementation in four languages rather than
from a worked biological or clinical example.

**Consequence, and it is the whole architecture:** four implementations only
cohere if they answer to one thing. Hence a normative, language-independent
[specification](docs/spec/core.md) plus a shared
[conformance corpus](conformance/). Everything is integer fixed-point with no
division and a canonical event-key ordering, so the four can be compared
bit-for-bit.

**What it costs:** the source text's illustrations — cell, stem cell, ecosystem,
diagnosis, child — remain unmodelled. Nothing here has been shown to say
anything true about any of them. Recorded in
[`revisions/000-v0.md`](revisions/000-v0.md).

## 3. Stack — **all four: Lean, Julia, Python, TypeScript**

| | Role | Status |
|---|---|---|
| **Python** | reference implementation; the corpus is generated from it | 30 tests |
| **TypeScript** | independent implementation | 12 tests |
| **Julia** | independent implementation | 67 assertions |
| **Lean 4** | formalisation — proves what the others can only sample | builds, no `sorry` |

Lean's role is deliberately different. Python, TypeScript and Julia run the same
vectors, which *sample* the spec's claims. Lean states them as theorems.

**This immediately paid for itself.** Lean proved that our loss measure does not
satisfy the requirement the spec placed on it — a defect all twelve vectors and
three implementations agreed to miss, because agreement across implementations
is not correctness. See
[`contradictions/004`](contradictions/004-loss-can-round-to-zero.md).

## 4. Lineage — **made explicit** (revised)

Initially answered as "stands on its own", then revised: the lineage should be
recorded. It lives in [`RELATED.md`](RELATED.md).

That document names the neighbourhood — Simondon on individuation, Whitehead on
events, Deleuze on multiplicity, Barad on mutual constitution, Kauffman on
expanding possibility, Rosen on anticipation, applied category theory on
higher cells — section by section against the source text, together with the
computational projects that already cover levels 2–3.

It is a **starting point to be extended**, not a survey, and it deliberately
does not claim whether these are antecedents or convergences.

**Why this is the better answer:** the point of the section is to make
comparison possible rather than to pre-empt it. `RELATED.md` therefore ends by
stating where this work differs — the conjunction of §4, §8 and §12 — which is
the part most exposed to criticism and the part worth being explicit about.

**Scope:** this governs how the *ideas* are positioned. Engineering
dependencies — Julia's `JSON`, the TypeScript compiler — are cited where used,
as tools rather than as intellectual ancestry.

---

## Reopening

Per principle 7 these are revisable. Decision 2 is the one most likely to want
revisiting: the abstract core is now real and checked, and a single worked domain
would test whether §4's dimension-generation says anything about a case anyone
cares about. That is the natural next question, and it is not answered here.
