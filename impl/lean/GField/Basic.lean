/-
  A generative field -- Lean 4 formalisation of `docs/spec/core.md`.

  This implementation has a different job from the other three. Python,
  TypeScript and Julia run the shared conformance corpus, which *samples* the
  spec's claims. Lean states them as theorems and proves them for all inputs.

  Two things are established here that no test can establish:

  1. The absorption theorem (spec section 5): generating a dimension drives the
     residual that produced it to exactly zero. Proved for every field, not for
     the twelve in the corpus.
  2. A field state cannot exist without a satisfied precondition -- `applyEvent`
     takes the proof as an argument, so principle 2 holds by typing rather than
     by convention.

  It also refutes one of our own claims; see `loss_can_round_to_zero` at the end.

  No mathlib dependency: everything below is self-contained.
-/

namespace GField

/-! ## Section 0 -- arithmetic

The spec fixes rounding toward zero. Lean's `/` on `Int` floors, so the
specified operation is `Int.tdiv`, not `/`. This is exactly the kind of silent
cross-language divergence section 0 exists to prevent.
-/

def SCALE : Int := 1000
def THETA : Int := 500
def COHESION : Int := 600

/-- `v * f / SCALE`, truncating toward zero (spec section 0). -/
def scaleMul (v f : Int) : Int := Int.tdiv (v * f) SCALE

theorem scaleMul_identity (v : Int) : scaleMul v SCALE = v := by
  unfold scaleMul SCALE
  simp [Int.tdiv_eq_ediv]

theorem scaleMul_zero (v : Int) : scaleMul v 0 = 0 := by
  unfold scaleMul
  simp

/-- Truncation toward zero is odd-symmetric; floor division is not.
    This is the property that makes the four implementations agree. -/
theorem scaleMul_neg (v f : Int) : scaleMul (-v) f = -(scaleMul v f) := by
  unfold scaleMul
  rw [Int.neg_mul, Int.neg_tdiv]

/-! ## Sections 1-2 -- fields, relations, and derived entities -/

structure Relation where
  id : Nat
  a : Nat
  b : Nat
  w : List Int
deriving Repr, DecidableEq

structure Field where
  dims : List String
  sites : Nat
  relations : List Relation
deriving Repr

/-- Sum of a list of integers. Defined here rather than reused so that the
    lemmas below have no external dependency. -/
def lsum : List Int → Int
  | [] => 0
  | x :: xs => x + lsum xs

theorem lsum_append (a b : List Int) : lsum (a ++ b) = lsum a + lsum b := by
  induction a with
  | nil => simp [lsum]
  | cons x xs ih => simp [lsum, ih]; omega

theorem lsum_singleton (x : Int) : lsum [x] = x := by simp [lsum]

/-- Total modelled weight carried by a list of relations. -/
def totalW : List Relation → Int
  | [] => 0
  | r :: rs => lsum r.w + totalW rs

/-- What the field is accountable to, minus what it can currently express. -/
def residualOf (observed : Int) (rs : List Relation) : Int := observed - totalW rs

/-!
### Principle 1, structurally

`Entity` is a *definition*, not a structure. There is no constructor, so no
caller can produce one except by deriving it from relations. In the other three
implementations this is enforced by a test that greps the public API; here it is
enforced by the language.
-/

/-- Coupling between two sites: the sum of absolute weights on that pair. -/
def coupling (rs : List Relation) (a b : Nat) : Int :=
  match rs with
  | [] => 0
  | r :: rest =>
      let here := if r.a = a ∧ r.b = b then lsum (r.w.map Int.natAbs |>.map Int.ofNat) else 0
      here + coupling rest a b

/-- A pair is coupled when it clears the threshold. Derived, never declared. -/
def Coupled (rs : List Relation) (a b : Nat) : Prop := coupling rs a b ≥ THETA

instance (rs : List Relation) (a b : Nat) : Decidable (Coupled rs a b) := by
  unfold Coupled; exact inferInstance

theorem coupling_nil (a b : Nat) : coupling [] a b = 0 := rfl

/-- With no relations there is nothing to be coupled, so no entity can arise.
    The Python and TypeScript suites test this on one input; here it is total. -/
theorem no_relations_no_coupling (a b : Nat) : ¬ Coupled [] a b := by
  unfold Coupled
  rw [coupling_nil]
  decide

/-! ## Section 5 -- dimension generation, and the absorption theorem -/

/-- Extend every relation with a zero in the new coordinate. -/
def padZero (rs : List Relation) : List Relation :=
  rs.map (fun r => { r with w := r.w ++ [0] })

/-- The canonically first relation on a pair takes the residual in the new
    coordinate; every other relation takes zero, so the residual is absorbed
    exactly once (spec section 5). -/
def absorbHead (extra : Int) : List Relation → List Relation
  | [] => []
  | r :: rest => { r with w := r.w ++ [extra] } :: padZero rest

theorem totalW_padZero (rs : List Relation) : totalW (padZero rs) = totalW rs := by
  induction rs with
  | nil => simp [padZero, totalW]
  | cons r rest ih =>
      simp [padZero, totalW, lsum_append, lsum] at *
      omega

theorem totalW_absorbHead (extra : Int) (r : Relation) (rest : List Relation) :
    totalW (absorbHead extra (r :: rest)) = totalW (r :: rest) + extra := by
  simp [absorbHead, totalW, lsum_append, lsum_singleton, totalW_padZero]
  omega

/--
**Absorption.** Generating a dimension drives the residual that produced it to
exactly zero.

This is the load-bearing claim of spec section 5: the content of a new
coordinate is not arbitrary, it is precisely what the old space failed to
express. The conformance corpus checks this on twelve fields. Here it holds for
every non-empty field, for every observed value.
-/
theorem absorption (observed : Int) (r : Relation) (rest : List Relation) :
    residualOf observed (absorbHead (residualOf observed (r :: rest)) (r :: rest)) = 0 := by
  unfold residualOf
  rw [totalW_absorbHead]
  omega

/-- A generated dimension adds exactly one coordinate -- never zero, never two. -/
def generateDimension (f : Field) (name : String) (extra : Int) : Field :=
  { f with dims := f.dims ++ [name], relations := absorbHead extra f.relations }

theorem generateDimension_dims_succ (f : Field) (name : String) (extra : Int) :
    (generateDimension f name extra).dims.length = f.dims.length + 1 := by
  simp [generateDimension]

/-! ## Section 3 -- principle 2 by typing

`applyEvent` cannot be called without a proof that the precondition holds. In
the other implementations this is a runtime check that raises; here an
unsatisfied precondition is not expressible.
-/

inductive Event where
  | dissolve (support : List Nat)
  | feedback (a b : Nat)
deriving Repr, DecidableEq

def inside (support : List Nat) (r : Relation) : Bool :=
  support.contains r.a && support.contains r.b

def enabled (f : Field) : Event → Bool
  | .dissolve support => f.relations.any (inside support)
  | .feedback a b => f.relations.any (fun r => r.a = a && r.b = b)

def applyEvent (f : Field) (e : Event) (_h : enabled f e = true) : Field :=
  match e with
  | .dissolve support => { f with relations := f.relations.filter (fun r => !inside support r) }
  | .feedback a b =>
      { f with relations := f.relations ++
          [{ id := f.relations.length, a := a, b := b, w := f.dims.map (fun _ => 0) }] }

/-- Dissolving removes every relation inside the support. Nothing survives that
    the class was made of, which is principle 3: the classification has no
    existence apart from the relations sustaining it. -/
theorem dissolve_removes_inside (f : Field) (support : List Nat)
    (h : enabled f (.dissolve support) = true) :
    ∀ r ∈ (applyEvent f (.dissolve support) h).relations, inside support r = false := by
  intro r hr
  simp [applyEvent, List.mem_filter] at hr
  exact hr.2

/-! ## Section 8 -- and a claim of ours that is false

The spec requires `Loss(F) > 0` on the built-in ontology pairs, and our measure
is term coverage: `|residue| * SCALE / (|image| + |residue|)`, in integers.

That measure does not guarantee it. With integer division, a small residue
against a large image floors to zero -- a translation that lost something would
report having lost nothing. The corpus never catches this, because its fields
are small.

Recorded as `contradictions/004-loss-can-round-to-zero.md`.
-/

/-- Both operands are counts, so the measure is stated over `Nat`: truncating
    division and floor division coincide on non-negatives. -/
def loss (image residue : Nat) : Nat :=
  if image + residue = 0 then 0 else residue * 1000 / (image + residue)

/-- Loss is positive when the residue is an appreciable share of the source. -/
theorem loss_pos_of_small_image (image residue : Nat)
    (hr : residue ≥ 1) (hi : image ≤ 500 * residue) : loss image residue > 0 := by
  unfold loss
  rw [if_neg (by omega)]
  have hk : 0 < image + residue := by omega
  have := Nat.le_div_iff_mul_le hk (x := 1) (y := residue * 1000)
  omega

/--
**Refutation.** One term lost against a thousand kept reports zero loss.

So the spec's requirement is a property of the *fields we tested*, not of the
measure. Either the measure changes or the requirement weakens; the decision is
recorded, not silently resolved.
-/
theorem loss_can_round_to_zero : loss 1000 1 = 0 := by decide

end GField
