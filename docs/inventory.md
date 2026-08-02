# Formal inventory

A construct-by-construct reading of [the source text](source/geometry-and-dynamic-systems-1.md),
recording *what each section commits any implementation to*. This is the bridge
between the paper and any of the plans in [`../PLANS.md`](../PLANS.md).

Nothing here adds theory. Every row is traceable to a line in the source.

---

## The twelve shifts

| § | Shift | Formal content | What it demands of an implementation | Difficulty |
|---|---|---|---|---|
| 0 | *(baseline)* multitude | $\{p_1,\ldots,p_n\}$ | The thing to be superseded. A set of pre-identified members. | — |
| 1 | multitude → relational field | $A,B,C \to R(A,B),R(B,C)$; $\text{cell} = \text{persistent convergence of relations}$ | Relations are the stored primitive. Entities must be **derived** — computed as stability/persistence over a relation structure, not declared. | Medium |
| 2 | entities → events | $\text{event} = \text{transformation under conditions}$; $x_1 \xrightarrow{f_1} x_2 \xrightarrow{f_2} x_3$ | Morphisms are first-class, named, composable. Identity is carried by continuity of arrows, not by node identity. | Medium |
| 3 | positions → possibilities | $\mathcal{P}(x)$; $\text{state} = \text{actual} + \text{accessible} + \text{becoming accessible}$ | Every state carries a possibility set. Note the **third** modality: "becoming accessible" — a derivative of $\mathcal{P}$, not just $\mathcal{P}$ itself. Two states with identical actuality must be distinguishable. | Medium |
| 4 | fixed → generated dimensions | $\mathcal{F}_n \to \mathcal{F}_{n+1}$; $\text{persistent contradiction} \to \text{new distinction} \to \text{expanded space}$ | Schema evolution as a runtime operation. Requires a **contradiction detector** whose saturation triggers coordinate creation, plus migration of all prior data. | **Hard** |
| 5 | one ontology → pluralism | $\{\text{objects},\text{properties},\text{causes}\}$, $\{\text{processes},\text{relations},\text{constraints}\}$, $\{\text{agents},\text{meanings},\text{purposes}\}$; $F:\mathcal{O}_1\to\mathcal{O}_2$; $\mathrm{Loss}(F)>0$ | Multiple simultaneous schemas, none canonical. Translations are **lossy by design** and must return a residue, not throw it away. Recording the residue is a stated requirement. | Medium |
| 6 | relations → transformations of relations | $r \to r'$; $\alpha : r \Rightarrow r'$; $\beta : \alpha \Rrightarrow \alpha'$ | At minimum 2-cells and 3-cells. Rewriting edges, and rewriting the rewrites. | **Hard** |
| 7 | structure → generative grammar | $\mathcal{G} \to \{\mathcal{F}_1,\mathcal{F}_2,\ldots\}$ + 8 named rule families | A production/rewrite system over field structures. The object of study becomes $\mathcal{G}$, not any single $\mathcal{F}$. | Medium |
| 8 | fixed → changing possibility | $\mathcal{X}(t_1)\neq\mathcal{X}(t_2)$; $\dot{x}=F(x,\mathcal{X})$, $\dot{\mathcal{X}}=G(x,\mathcal{X})$ | An integrator where the state space is itself a state variable. Standard ODE solvers assume a fixed $\mathcal{X}$; this breaks that assumption on purpose. | **Hard** |
| 9 | space → individuation | $\text{preindividual} \to \text{differentiation} \to \text{temporary individual}$; symmetry-breaking; 5 questions | Entities carry birth / maintenance / dissolution records **and counterfactuals** ("which alternatives were suppressed?"). Individuals are explicitly temporary. | Medium |
| 10 | one world → space of worlds | $\mathcal{W}=\{W_1,\ldots,W_n\}$; $F_{ij}:W_i\to W_j$ *partial* | A structure of worlds with partial maps between them, where interaction can **create** new shared worlds. Observation changes the world observed. | Medium |
| 11 | observer/observed → mutual constitution | $y_i=\pi_i(x,o_i)$; $\dot{x}=F(x,o_i,y_i)$; $\dot{o_i}=G(o_i,x,y_i)$ | Observers are state variables *inside* the system. Measurement has back-action. No privileged external view exists. | Medium |
| 12 | totalization → inexhaustibility | $\mathcal{M}\neq\text{complete}$; $\mathcal{M}_t \to \mathcal{M}_{t+1}$ | The model is versioned, revisions are first-class recorded events, and the system must never assert closure. | Low (but governance-shaped) |

## The ladder = a conformance spec

The paper's own summary table is the most directly usable thing in it. Read as
levels, it gives a roadmap where each rung is independently demonstrable:

| Level | Name | Criterion | Satisfied by |
|---|---|---|---|
| 0 | binary | $A$ or $B$ | — |
| 1 | multitude | $\{A,B,C,\ldots\}$ | — |
| 2 | structured field | positions + relations + dimensions | §1 |
| 3 | dynamic field | positions and relations change over time | §2, §6, §8 (inner loop) |
| 4 | generative field | new positions, relations, **and dimensions** emerge | §3, §4, §7, §8 (outer loop), §9 |
| 5 | reflexive field | the field models and modifies its own organization | §5, §10, §11, §12 |
| 6 | open becoming | no fixed inventory of future possibilities | the limit; assertable only negatively |

Level 4 is the name of the project. Levels 0–3 are prior art (graphs, dynamical
systems, ABMs). **Level 4 is where the real work starts**, and level 6 can only
ever be honoured by *refusing to claim closure* — it is a constraint on
assertions, not a feature to ship.

## The seven principles = invariants

The closing list is a set of design rules. Each is mechanically checkable, which
makes them the natural test suite / lint rules for whatever gets built:

| # | Principle | Checkable form |
|---|---|---|
| 1 | relations before isolated entities | No entity may be *declared*; every entity must be derived from a relation structure. |
| 2 | events before static states | Every state must be reachable by a named, recorded transformation. No orphan states. |
| 3 | transformations before classifications | A class/type may only be defined as an invariant of transformations, never as a primitive tag. |
| 4 | individuation before fixed individuals | Every individual carries a formation record and a dissolution condition. |
| 5 | possibility-generation before a fixed possibility space | $\mathcal{P}$ must be computed, and the space must be extensible at runtime. |
| 6 | co-evolution before detached observation | Every observation must have a declared back-action, even if zero — zero must be *asserted*, not assumed. |
| 7 | revisability before final completeness | No artifact may assert completeness; every model version records what it revised and what it lost. |

## What the paper does *not* fix

Honest gaps — each is a design decision left to us, not an oversight to paper over:

- **No metric.** $\mathrm{Loss}(F) > 0$ is asserted but never quantified. Any
  implementation must invent a residue measure, and should say so loudly.
- **No convergence criterion.** "Persistent contradiction" (§4) has no threshold.
  How persistent? Over what window? This is a free parameter.
- **No mechanism for dimension *content*.** §4 says a new coordinate appears; it
  does not say what determines its semantics.
- **"Becoming accessible" (§3) is undefined** as a formal object — plausibly
  $d\mathcal{P}/dt$, but the text does not say.
- **Higher cells stop at $\beta$** (§6). Whether the tower is finite, or
  $\omega$-truncated, or genuinely infinite, is open.
- **No worked numeric example anywhere.** Every illustration is qualitative
  (cell, stem cell, ecosystem, diagnosis, child/adult). Choosing one to make
  quantitative is the single highest-leverage decision for a runnable version.

## Where the work is

The intellectual and computational neighbourhood is recorded in
[`RELATED.md`](../RELATED.md), section by section. What matters *for building* is
which sections are load-bearing.

Levels 2–3 of the ladder are ordinary: relation graphs and transition systems.
The distinctive claim is the **conjunction** of dimension-generation (§4),
coupled state/state-space dynamics (§8), and reflexivity (§12) in one framework
— a system that changes the space it moves in, and models the fact that it does.

That conjunction is where every hard engineering problem in
[`spec/core.md`](spec/core.md) turned out to be, and it is what
[`conformance/`](../conformance) is built to pin down.
