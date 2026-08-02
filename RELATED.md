# Lineage and related work

The source text cites no one. It nonetheless sits in a well-populated
neighbourhood, and naming that neighbourhood is useful in two different ways:
it tells a serious reader where the ideas come from, and it tells a builder
which parts of the ladder already exist and should be borrowed rather than
rebuilt.

**This is a starting point, not a survey.** It records the connections that were
visible from the text itself. Additions welcome — the sections are deliberately
shaped to be extended.

---

## Conceptual lineage

Each entry names the section of the source text it bears on. None of these are
claims about influence; they are claims about proximity.

| Source §  | Idea | Neighbourhood |
|---|---|---|
| §1, ladder | multiplicity; becoming; the priority of relations over relata | Deleuze |
| §2 | events before static states; process as primitive | Whitehead's process metaphysics |
| §3 | reachable futures; expanding possibility | Kauffman's *adjacent possible*; the "unprestatable phase space" literature |
| §3 | states that include what is not yet actual | Rosen, anticipatory systems |
| §4 | contradiction as a mechanism that generates new distinctions | dialectical traditions; Hegel by way of systems theory |
| §6 | transformations of transformations; higher cells | applied category theory; higher categories |
| §9 | individuation; the preindividual field; symmetry-breaking | Simondon — the closest single antecedent for this section |
| §10 | operative worlds rather than views of one world | perspectival realism; institution theory for the partial-mapping formalism |
| §10 | categories reorganising what they classify | Hacking's looping effects |
| §11 | mutual constitution of observer and observed | Barad's intra-action; second-order cybernetics (von Foerster, Maturana & Varela) |
| §12 | revisability over completeness | fallibilism; Peirce |

## Computational neighbours

Levels 2–3 of the ladder are well served by existing tools. Anything this
project builds at those levels should be understood as a deliberate choice to
stay self-contained, not as novelty.

| Project | What it already does | Bearing here |
|---|---|---|
| [Catlab.jl](https://github.com/AlgebraicJulia/Catlab.jl) | computational category theory; C-sets | §§1, 6 — relational structure and rewriting |
| [AlgebraicDynamics.jl](https://github.com/AlgebraicJulia/AlgebraicDynamics.jl) | compositional open dynamical systems via operads | §8 — but within a *fixed* state space |
| [DisCoPy](https://arxiv.org/abs/2005.02975) | monoidal categories and string diagrams in Python | §6 — 2-cells and functorial translation |
| [CatColab](https://topos.institute/blog/2024-10-02-introducing-catcolab/) | interactive modelling on double theories | §5, §10 — plural formalisms side by side |
| sheaf-theoretic data fusion | gluing partial local views, with obstruction | §10 — partial maps $F_{ij}$ and their failure to glue |

## Where this differs

Worth stating plainly, since the point of a lineage section is to make the
comparison possible rather than to avoid it.

Each neighbour above handles some part of the ladder well. What none of them
attempt is the **conjunction** that defines level 4 and above:

- **§4 dimension-generation** — the state space gains a coordinate at runtime,
  determined by what the old space could not express;
- **§8 coupled dynamics** — the state space is itself a state variable, evolving
  on the same clock as the state;
- **§12 reflexivity** — the model records its own revisions and refuses closure.

Compositional dynamical systems compose systems *within* a fixed state space.
Category-theoretic modelling tools let you change formalism, but by editing the
model rather than by the model changing itself. The conjunction is where the
engineering here actually went, and it is the part most exposed to criticism —
which is the reason to name the comparison rather than leave it implicit.

## Open question for this document

Whether the connections above are *antecedents* (the text is working in these
traditions) or *convergences* (it arrived independently at nearby positions) is
not something this repository can settle, and the table above deliberately does
not claim either. See [`DECISIONS.md`](DECISIONS.md) §4.
