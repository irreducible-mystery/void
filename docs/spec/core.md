# Core specification v0

The language-independent definition of a generative field. Every implementation
in [`impl/`](../../impl) must satisfy this document exactly and must pass the
shared corpus in [`conformance/`](../../conformance).

This spec is **normative**. Where it makes a choice the source text leaves open,
the choice is marked **[OPEN → CHOICE]** with a pointer to the contradiction
record that tracks it. Those are our decisions, not the text's, and they are
revisable — per principle 7.

---

## 0. Determinism

Four implementations can only be compared if they agree bit-for-bit.

- **All quantities are integers.** No floating point anywhere in the core.
  Weights are fixed-point with scale `SCALE = 1000` (so `1500` means `1.5`).
- **No division.** Ratio comparisons are done by cross-multiplication.
  `a/b ≥ θ/SCALE` is evaluated as `a * SCALE ≥ θ * b` (with `b > 0`).
- **Ordering is canonical everywhere.** Site sets are stored ascending.
  Relations are ordered by `(a, b, id)`. When several candidates qualify for an
  operation, the lexicographically smallest is chosen. There are no ties.
- **Randomness**, where a driver needs it, uses this exact generator and no
  other:

  ```
  xorshift64*(s):
      s ^= s >> 12   (unsigned 64-bit)
      s ^= s << 25   (mask to 64 bits)
      s ^= s >> 27
      return (s * 0x2545F4914F6CDD1D) mod 2^64
  ```

  Implementations must mask to 64 bits at every step. The returned value is the
  new state; a draw in `[0, n)` is `state mod n`.

## 1. Field

A field `F` is:

| Component | Type | Meaning |
|---|---|---|
| `dims` | ordered list of names | the coordinates currently expressible (§4) |
| `sites` | `int` | number of addresses `0 .. sites-1` |
| `relations` | list of `Relation` | **the primitive** (§1) |
| `observed` | map `(a,b) → int` | coupling the field is accountable to |
| `tick` | `int` | discrete time |
| `history` | list of `EventRecord` | every transformation applied (§2, §12) |

A `Relation` is `{id: int, a: int, b: int, w: [int]}` with `a < b` and
`len(w) == len(dims)`.

**Sites are addresses, not individuals.** A site is an index with no identity of
its own. This is what makes principle 1 enforceable: there is nothing in the
data model that *is* a thing.

## 2. Entities are derived, never declared (§1, principle 1)

There is no operation that creates an entity. Implementations **must not**
expose one. An entity is computed from the relations:

```
coupling(a,b)      = Σ over relations r with (r.a,r.b) = (a,b) of Σ_d |r.w[d]|
candidate support  = a connected component, of size ≥ 2, of the graph whose
                     edges are the pairs with coupling(a,b) ≥ THETA,
                     which additionally satisfies cohesion (below)
entity             = a candidate support that has appeared, unchanged, for
                     PERSISTENCE consecutive ticks
```

A candidate has cohered but not yet lasted. Both are required: an entity is a
region of the relation graph that holds together *and* persists.

`cohesion(S)` compares internal to boundary coupling:

```
internal(S) = Σ coupling(a,b) for a,b ∈ S
boundary(S) = Σ coupling(a,b) for exactly one of a,b ∈ S
cohesion holds iff internal(S) * SCALE ≥ COHESION * (internal(S) + boundary(S))
```

This is `cell = persistent convergence of relations` made computable: an entity
is a region of the relation graph that both coheres and *lasts*.

Defaults: `THETA = 500`, `PERSISTENCE = 3`, `COHESION = 600`.

## 3. Events are the eight grammar rules (§2, §7)

§7 lists eight rule families; §2 makes transformation the primitive unit. They
are the same thing, so the grammar **is** the event vocabulary. An event is
`{name, params, precondition, apply}` and every field state must be reachable by
a recorded event (principle 2) — implementations must refuse to construct a
field state except through `apply`, other than the initial seed.

| # | Event | Precondition | Effect |
|---|---|---|---|
| 1 | `form_boundary(S)` | `S` non-empty, some boundary coupling > 0 | multiply weights crossing `∂S` by `BOUNDARY_DECAY`, integer-divided by `SCALE`, truncating toward zero |
| 2 | `differentiate(S)` | `\|S\| ≥ 4`, `S` is a candidate support | split `S` into `(S₁,S₂)` by the canonical minimum-coupling bisection; weaken cross-pairs by `BOUNDARY_DECAY`, strengthen intra-pairs by `REINFORCE` |
| 3 | `join(S,T)` | `S ∩ T = ∅`, both non-empty | add a relation between `min(S)` and `min(T)` with weight `JOIN_W` on dimension 0 |
| 4 | `branch(S)` | `sites + \|S\| ≤ MAX_SITES` | append `\|S\|` new sites duplicating `S`'s internal relations |
| 5 | `repeat(S)` | as `branch` | as `branch`, and additionally copy `S`'s boundary relations |
| 6 | `feedback(a,b)` | a relation `(a,b)` exists | add the reciprocal contribution: a second relation `(a,b)` with weight `FEEDBACK_W` on dimension 0 |
| 7 | `new_level(S)` | `\|S\| ≥ 2`, `sites < MAX_SITES` | append one site `L`, relate `L` to every member of `S` with weight `LEVEL_W` on dimension 0 |
| 8 | `dissolve(S)` | some relation lies inside `S` | remove every relation with both endpoints in `S` |

Defaults: `BOUNDARY_DECAY = 500`, `REINFORCE = 1500`, `JOIN_W = 700`,
`FEEDBACK_W = 600`, `LEVEL_W = 800`, `MAX_SITES = 64`.

The canonical minimum-coupling bisection of `S`: consider every split of `S`
into two non-empty parts induced by a prefix of `S`'s ascending order; choose the
one minimising cross-coupling; break ties by smallest prefix length. This is
deterministic and needs no search heuristic.

### Event keys

Every event instance has a canonical key, and the instance space is sorted by
it:

```
key(e) = name "(" join(params, ";") ")"      set-valued params comma-joined
         e.g.  form_boundary(0,1,2)   join(0,1;2,3)   feedback(0;1)
```

This is normative, not cosmetic. The instance space is *ordered* by this string,
and section 8 reads a bounded prefix of it, so a language-native representation
would change which terms an ontology yields and therefore its translation loss.

## 4. Possibility (§3)

```
P(F)      = { e : e.precondition holds in F }              -- accessible
gap(e,F)  = a non-negative integer, 0 exactly when e.precondition holds
becoming  = { e : gap(e,F) > 0 and gap has strictly decreased
                  over the last BECOMING_WINDOW ticks }
state     = (actual: F, accessible: P(F), becoming: becoming)
```

**[OPEN → CHOICE]** The source defines "what is becoming accessible" (§3) but
gives it no formal content. We read it as *monotonically decreasing distance to
enablement*. This is a choice; see
[`contradictions/003-becoming-accessible.md`](../../contradictions/003-becoming-accessible.md).

`BECOMING_WINDOW = 2`. Each event family defines its own `gap`; where a
precondition is a threshold, the gap is the shortfall, otherwise it is 0 or 1.

## 5. Dimension generation (§4) — the load-bearing part

The field is accountable to `observed`. What it can currently express is the sum
of its weights. The difference is a contradiction:

```
residual(a,b) = observed(a,b) - Σ_d w(a,b)[d]
contradiction at (a,b) iff |residual(a,b)| > TAU
```

A contradiction becomes **persistent** when it holds for `WINDOW` consecutive
ticks. Persistence alone is not sufficient — the text requires that the
contradiction be irreducible within the current space. So:

```
if some (a,b) has been in contradiction for WINDOW consecutive ticks
   and no event in P(F) strictly reduces Σ|residual| when applied for one tick
then
   emit DimensionEvent:
       dims ← dims ++ ["d{n}"]
       for each pair, the canonically first relation (lowest id) takes
           residual(pair) in the new coordinate; every other relation on that
           pair takes 0, so the residual is absorbed exactly once
       a pair with an `observed` value but no relation at all gets its first
           relation here, carrying 0 in every old coordinate and the residual
           in the new one
       the migration is recorded in history
```

History is a log of records, not a series of field snapshots, so migration of
"prior fields" is discharged by the recorded migration entry: any prior state
is reconstructed by replay, and takes 0 in the new coordinate by construction.

The second clause is what makes the new coordinate more than a correction term:
a pair the old space could not express **at all** becomes expressible only once
the dimension exists.

**Required property.** After a dimension event, `Σ|residual| = 0`. The
coordinate absorbs exactly what produced it. Conformance asserts this.

That is `persistent contradiction → new distinction → expanded space`, executing.
The new coordinate is exactly the part of the world the old space could not
express, which is why its content is determined rather than arbitrary.

Defaults: `TAU = 100`, `WINDOW = 3`.

**[OPEN → CHOICE]** `WINDOW` and `TAU` are free parameters; the text gives no
threshold for "persistent". See
[`contradictions/002-persistence-threshold.md`](../../contradictions/002-persistence-threshold.md).

## 6. Coupled dynamics (§8)

```
step(F, event, observe):
    1. apply the scheduled event (inner dynamics: ẋ = F(x,X))
    2. tick ← tick + 1
    3. merge `observe` into `observed`, if given
    4. update residual streaks
    5. test for dimension generation (outer dynamics: Ẋ = G(x,X))
    6. recompute candidates and gaps for this tick
```

Step 5 can change the dimensionality of everything in step 1. The two loops run
on the same clock and the state space is a state variable. Implementations
**must** perform step 5 after step 1 within the same tick, and must record a
`DimensionEvent` in history when it fires — the seam is where the content is, so
it is never hidden.

`observe` is **exogenous**: it is what the field is accountable to, and the
field does not choose it. Without it a driver could change the model but never
the world the model answers to, and the following would be underivable.

**Consequence — a distinction cannot be imposed by fiat.** `differentiate`
weakens a crossing relation, but if `observed` is unchanged the field is still
answerable to the old coupling. The resulting contradiction is persistent and
irreducible, so the field generates a coordinate that re-expresses exactly the
coupling the split removed, and the split undoes itself. Making a distinction
stick requires that what the field is accountable to changes too. This is a
derived property of the rules above, not an additional rule, and conformance
pins it so it cannot regress silently.

## 7. Individuation (§9)

Every entity carries a formation record:

```
Individual = { support, born_at, formation_event,
               maintained_by: [relation ids],
               dissolution_condition: "coupling below THETA",
               suppressed: [ alternative supports that were viable at born_at
                             but not selected ] }
```

`suppressed` is populated at a `differentiate` event by enumerating every
prefix-induced bisection and recording those not chosen. An individual is
explicitly temporary: when its support stops satisfying §2 it is closed with a
`died_at`, not deleted.

## 8. Ontologies and lossy translation (§5)

An ontology is a *view*: a total function from a field to a typed vocabulary.
Three are built in, exactly as the text names them:

| Ontology | Vocabulary | Reads |
|---|---|---|
| `O1` | objects, properties, causes | entities → objects; dimension values → properties; relations → causes |
| `O2` | processes, relations, constraints | events → processes; relations → relations; preconditions → constraints |
| `O3` | agents, meanings, purposes | observers → agents; readings → meanings; sustained gap-reduction → purposes |

A translation `F : Oᵢ → Oⱼ` returns `(image, residue)`. `residue` is the list of
source terms with no target term.

```
Loss(F) = |residue| * SCALE / |source terms|
```

Implementations **must** return the residue and **must not** provide a
translation that discards it. Conformance asserts `Loss(F) > 0` on the built-in
pairs: the vocabularies genuinely do not cover one another, which is the point of
§5.

**[OPEN → CHOICE]** The text asserts `Loss(F) > 0` without defining a measure.
Ours is term-coverage. See
[`contradictions/001-loss-metric.md`](../../contradictions/001-loss-metric.md).

> **Known defect — this requirement is not met in general.** The measure above
> uses integer division, so a small residue against a large image floors to
> zero: `loss(image = 1000, residue = 1) = 0`. A translation that lost something
> reports having lost nothing. Proved in
> `impl/lean/GField/Basic.lean` as `loss_can_round_to_zero`.
>
> All twelve conformance vectors pass `all_losses_positive` regardless, because
> their fields are small. Three implementations agree with each other and are
> wrong together — which is why the assertion above is scoped to *the built-in
> pairs at corpus scale*, and not stated as a property of the measure.
>
> Tracked as [`contradictions/004`](../../contradictions/004-loss-can-round-to-zero.md).
> Not silently patched: changing the constant until the tests stay green would
> be exactly the move principle 7 forbids.

## 9. Worlds (§10)

`World = { field view, relevance: map dimension → int weight }`. A partial map
`F_ij : W_i → W_j` is defined only on sites both worlds weight non-zero;
elsewhere it is undefined — represented as absence, never as a default value.
Interaction can create a new shared world by taking the union of supports where
two worlds both have non-zero relevance.

## 10. Observers (§11)

An observer is a **site in the field**, not an outside viewer:

```
read(o, F)  = π(o, F) → reading
back_action = the perturbation applied to F by that read
```

Every read applies its back-action before returning. An observer with no effect
must declare `back_action = 0` explicitly; implementations **must not** default
it (principle 6). Conformance includes a vector where reading changes the
subsequent entity decomposition — the observation changes what is observed.

## 11. Model versioning (§12)

`M_t` is the pair `(field, spec version)`. Every migration appends to a revision
log recording what changed and **what was lost**. No implementation may expose a
predicate named or meaning "complete". Principle 7 is enforced socially by CI
lint (see [`../../field/README.md`](../../field/README.md)), not by the type
system.

## 12. Conformance

An implementation is conformant at a level when it passes every vector tagged at
or below that level:

| Level | Name | Vectors assert |
|---|---|---|
| 2 | structured field | entities derived correctly; no declaration API exists |
| 3 | dynamic field | events transform fields; history is complete; identity follows arrows |
| **4** | **generative field** | **possibility sets; dimension generation fires; individuation records suppressed alternatives** |
| 5 | reflexive field | ontology translation with non-zero loss; worlds with partial maps; observer back-action |
| 6 | open becoming | not a test target — asserted only by the absence of completeness claims |

Level 6 has no vectors on purpose. It is a constraint on what may be asserted,
and a test suite claiming to verify it would violate it.
