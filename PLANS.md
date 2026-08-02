# Three plans for building the generative field on GitHub

Status: **proposal — nothing chosen yet.** This document exists to be argued
with. It follows from [`docs/source/geometry-and-dynamic-systems-1.md`](docs/source/geometry-and-dynamic-systems-1.md)
(the canonical text) and [`docs/inventory.md`](docs/inventory.md) (what each
section demands of an implementation).

All three plans share one spine, taken from the paper itself:

- The **ladder** (binary → multitude → structured field → dynamic field →
  generative field → reflexive field → open becoming) is the roadmap. Levels 0–3
  are prior art. **Level 4 is the project.**
- The **seven closing principles** are the invariants — the acceptance criteria,
  in every plan, in whatever form that plan can enforce them.

Where they differ is in *what kind of object* the repository becomes.

---

## Plan A — The Engine

**A library that computes generative fields. The theory becomes runnable and therefore falsifiable.**

The repository is research software: a package that implements the twelve shifts
as actual types and operations, with the seven principles as a property-based
test suite.

### Shape

```
void/
├── src/gfield/
│   ├── relational.py     §1  relations stored; entities *derived* by a persistence functional
│   ├── events.py         §2  first-class morphisms; identity carried by arrow-continuity
│   ├── possibility.py    §3  P(x); state = (actual, accessible, becoming_accessible)
│   ├── dimensions.py     §4  contradiction detector → add_coordinate → migrate F_n → F_{n+1}
│   ├── ontology.py       §5  parallel schemas; translate() returns (image, residue); Loss > 0
│   ├── higher.py         §6  2-cells (α: r ⇒ r′), 3-cells (β: α ⇛ α′)
│   ├── grammar.py        §7  the 8 rule families as production rules over field structures
│   ├── dynamics.py       §8  coupled integrator: ẋ = F(x,X) and Ẋ = G(x,X)
│   ├── individuation.py  §9  symmetry-breaking; birth/maintenance/dissolution + suppressed alternatives
│   ├── worlds.py         §10 family of worlds, partial maps F_ij, colimits for new shared worlds
│   ├── observers.py      §11 observers as internal state variables with declared back-action
│   └── model.py          §12 M_t → M_{t+1} with a migration + residue log
├── tests/principles/     the seven principles as executable invariants
├── examples/             stem cell · ecosystem resilience · diagnosis
└── docs/
```

### The three hard parts (and how to attack them)

1. **§4 dimension generation.** The paper gives no threshold for "persistent
   contradiction." Concretely: maintain a constraint residual per relation; when
   a residual stays above tolerance for a window $w$ and cannot be reduced by
   any available transformation, emit a `DimensionEvent` that adds a coordinate
   and migrates all history into $\mathcal{F}_{n+1}$. The migration is the real
   engineering — every stored object must survive a schema change.
2. **§8 changing state space.** No off-the-shelf ODE solver permits $\mathcal{X}$
   to change mid-integration. Approach: integrate in segments, halt on a
   dimension event, extend the state vector with a principled initial value for
   the new coordinate, resume. The seam between segments is where the physics
   lives; it must be visible, not hidden.
3. **§6 higher cells.** Cap at 3-cells initially and *say so*. Going higher is a
   research project, not a sprint.

### Build order

| Phase | Delivers | Ladder level |
|---|---|---|
| 1 | `relational` + `events`, entities derived not declared, principle tests 1–3 green | 2–3 |
| 2 | `possibility` + `individuation`, the stem-cell example | 3–4 |
| 3 | `dimensions` + `dynamics` — the load-bearing phase | **4** |
| 4 | `ontology` + `worlds` + `observers` | 5 |
| 5 | `grammar` + `higher`, `model` versioning | 5 |

### Honest assessment

- **Strongest claim.** Nobody can dismiss a framework that runs. Phase 3 either
  works or it doesn't, and either outcome is worth knowing.
- **Real risk.** Formalising §4 requires inventing content the paper leaves
  open, and a weak choice there produces a toy that technically satisfies the
  spec while illuminating nothing. Mitigation: pick *one* domain (§ Questions
  below) and make dimension-generation earn its keep on a real example.
- **Slowest to first visible result.** Weeks before anything is showable.
- **Leverage available.** Levels 2–3 substantially exist in
  [Catlab.jl](https://github.com/AlgebraicJulia/Catlab.jl) /
  [AlgebraicDynamics.jl](https://github.com/AlgebraicJulia/AlgebraicDynamics.jl)
  (Julia) and [DisCoPy](https://arxiv.org/abs/2005.02975) (Python). Building on
  one of them means starting at level 3 instead of level 0 — at the cost of
  adopting their idiom.

---

## Plan B — The Commons

**The repository *is* a generative field: a versioned structure that models and modifies its own organization.**

This plan takes §12 literally. Rather than describing a reflexive field, the
repo instantiates one. Its governance *is* the theory, executing.

### Shape

```
void/
├── docs/                    the twelve shifts, published to GitHub Pages
│   ├── source/              canonical text + provenance
│   └── shifts/              one page per section, cross-linked to the field data
├── field/                   the field as diffable, PR-able data
│   ├── relations/*.yaml     §1  primary
│   ├── events/*.yaml        §2
│   ├── dimensions/*.yaml    §4  each with the contradiction that generated it
│   ├── ontologies/*.yaml    §5  parallel, none canonical
│   ├── translations/*.yaml  §5  each *must* declare its residue
│   └── worlds/*.yaml        §10
├── contradictions/          open paradoxes, tracked as first-class objects
├── revisions/               M_t → M_{t+1}; every release says what it lost
└── .github/                 CI that enforces the seven principles as lint
```

### The reflexive mechanism

This is the part that makes it more than a docs site:

- An issue labelled `contradiction` that survives **N release cycles unresolved**
  automatically triggers an RFC. If the RFC is accepted, it *adds a dimension* —
  a new field in the schema — and the migration is recorded in
  `field/dimensions/`. That is $\text{persistent contradiction} \to \text{new distinction} \to \text{expanded space}$
  running as an actual repository process, on a real clock.
- **CI enforces the principles as lint over `field/`:** an entity declared
  without generating relations fails (principle 1). A translation with no
  declared residue fails (principle 5 / §5). An observation with no declared
  back-action — even zero — fails (principle 6). A release whose notes claim
  completeness fails (principle 7).
- **Releases are $\mathcal{M}_t$.** Every tag ships a residue log: what this
  revision cost us. Never a claim of completeness.
- **Discussions carry ontological pluralism** — parallel perspective tracks that
  are explicitly *not* reconciled into one inventory.

### Honest assessment

- **Ships in days, not weeks.** Something real and public almost immediately.
- **Genuinely reflexive.** It is the only one of the three plans where §§10–12
  are satisfied *by the artifact itself* rather than simulated inside it. The
  repo becomes an existence proof.
- **Real risk.** Without an engine, it can decay into "a nicely organised set of
  documents." The reflexive mechanism must actually fire at least once, on a
  real contradiction, or the claim is theatre. Mitigation: seed
  `contradictions/` with the genuine gaps already catalogued in
  `docs/inventory.md` — the undefined $\mathrm{Loss}$ metric, the missing
  persistence threshold, the undefined "becoming accessible."
- **Depends on a cadence.** A reflexive process with no clock is just a folder.

---

## Plan C — The Instrument

**A browser-based generative field you can see, touch, and break. Deployed on GitHub Pages, no backend.**

Twelve scenes, one per shift, each a self-contained interactive that makes one
abstract claim immediately obvious.

### Shape

```
void/
├── app/
│   ├── engine/         deterministic, seeded simulation core (shared by all scenes)
│   └── scenes/
│       ├── 01-relational      entities visibly condense out of a relation flux
│       ├── 03-possibility     P(x) drawn as a reachable-future halo; two visually
│       │                      identical states with different futures
│       ├── 04-dimensions      a contradiction meter that, on saturation, *adds an axis
│       │                      to the view* — the whole plot reorganises
│       ├── 05-ontology        switch between the three ontologies; untranslatable
│       │                      residue stays highlighted rather than vanishing
│       ├── 08-dynamics        the state space visibly grows while the trajectory runs
│       ├── 09-individuation   symmetry-breaking, with suppressed alternatives as ghosts
│       ├── 10-worlds          five viewports (physician/patient/immune cell/microbe/insurer);
│       │                      partial maps between them
│       └── 11-observer        a probe that measurably perturbs what it measures
└── .github/workflows/pages.yml
```

Every scene is URL-addressable and embeddable. State exports to JSON.

### Honest assessment

- **By far the most legible.** A person understands "the space itself changed"
  in ten seconds of watching, where ten pages of prose may not land. The §4 and
  §8 scenes in particular do work that text cannot.
- **Best recruiting tool.** For a project whose barrier is that nobody knows what
  "generative field" means, this is the answer to that.
- **Real risk — and it is the serious one.** Visualisation without a genuine
  engine underneath is animation. A scene *depicting* dimension-generation while
  the axis addition is scripted rather than computed is a lie about the theory's
  central claim. Mitigation: the engine must actually compute the transitions,
  which means Plan C depends on at least Plan A phases 1–3.
- **Highest risk of premature polish** — of looking finished while asserting
  nothing checkable.

---

## Recommendation

These are not mutually exclusive, and the strongest version of the project is
one repository containing all three — but **sequenced**, because their
dependencies are real:

**Plan B skeleton now → Plan A core next → Plan C last.**

Reasoning:

1. **B first, because it costs days and is the only plan that is already true.**
   The reflexive-field claim is satisfied by the repository's own behaviour, and
   the contradictions worth seeding are already catalogued.
2. **A second, because it is the only plan that can be wrong.** Falsifiability
   is the point. Phase 3 (§4 + §8 together) is the actual thesis, and if it
   fails, everything else should be rewritten around that finding.
3. **C last, because it is honest only after A works.** An instrument built on
   a real engine is a demonstration; built on scripted animation it is a
   misrepresentation of the central claim.

A single monorepo — `docs/` + `field/` (B), `src/` (A), `app/` (C) — keeps the
ladder legible, because each level is visible in one place.

The alternative worth considering: if the goal is **reach** rather than
**rigour**, invert to C → B → A and accept that early scenes are illustrations
rather than simulations, clearly labelled as such. That is a legitimate choice,
but it should be made deliberately and stated in the README, not drifted into.

---

## Questions

> **Questions 1–4 and 7 are answered** — see [`DECISIONS.md`](DECISIONS.md).
> In short: all three plans, sequenced; an abstract core grounded in four
> languages rather than in a domain; Lean, Julia, Python and TypeScript
> together; and the lineage made explicit in [`RELATED.md`](RELATED.md).
>
> The rest are open. Question 3 is the one most worth revisiting now that the
> abstract core is real and checked.

### Decisive — these change which plan is right

1. **What should this *be*?** An engine (falsifiable research software), a
   commons (a living, reflexive body of work), an instrument (a public
   explainer), or all three sequenced? Everything else follows from this.
2. **Rigour or reach?** Is the target audience researchers who will judge this
   on formal seriousness, or a general readership who need to *get it*? This
   sets the C-vs-A ordering.
3. **Which domain grounds it?** The paper uses cell differentiation, stem cells,
   ecosystem resilience, clinical diagnosis, and child development as
   illustrations, all qualitative. Making *one* quantitative is the highest-
   leverage decision for anything runnable — §4 in particular needs a real
   example to avoid becoming a toy. Which one is closest to your own knowledge?
4. **Stack.** Python (most accessible, DisCoPy available), Julia (Catlab /
   AlgebraicDynamics — mathematically closest to §§6–8, steeper), TypeScript
   (required for C regardless), or a proof assistant (Lean/Agda — maximal rigour,
   much slower, and arguably in tension with §12's rejection of completeness).

### Consequential — needed before much is built

5. **This repo or a new one?** `irreducible-mystery/void` is currently empty. I
   lean toward keeping it: "void" reads well against §9's *preindividual field*.
   But if you want a discoverable name, `generative-field` is the obvious one.
   Public or private?
6. **Authorship and licence.** Is the PDF your own writing? Should it be
   committed as canonical source (I have transcribed it on that assumption —
   easily reverted)? Proposed: Apache-2.0 for code, CC BY 4.0 for prose. Any
   attribution line you want on the text?
7. **Lineage — explicit or not?** The paper cites no one, yet sits squarely
   among Simondon (individuation), Whitehead (events), Deleuze (multiplicity),
   Barad (mutual constitution), Kauffman (adjacent possible), Rosen
   (anticipatory systems), and applied category theory. Do you want a
   `RELATED.md` making that lineage explicit — which invites serious readers but
   also invites comparison — or should the text stand unattributed on its own
   terms? This is a positioning choice, not a technical one.
8. **Solo or collaborative?** Plan B's mechanism assumes contributors filing
   contradictions. If this is a solo project, the reflexive loop needs a
   different trigger — a scheduled self-review rather than community pressure.

### Housekeeping

9. **The truncated line.** On page 1, the display equation runs off the right
   margin: *"many entities ⟶ a system that generates entities, relations, and
   possible ⟨cut off⟩."* What was the missing word — "possibilities"? Do you
   have the original source file?
10. **"Yes."** The document opens mid-conversation. Is there a preceding turn —
    a question this is answering — that provides framing I should have?
11. **Part 1 of how many?** The filename says `_1`. If parts 2+ exist, I should
    read them before locking any structure, since §§4 and 8 are exactly where a
    sequel would add content.
12. **Cadence.** How much should I build before you review — a scaffold you
    react to this week, or a deep first implementation?
