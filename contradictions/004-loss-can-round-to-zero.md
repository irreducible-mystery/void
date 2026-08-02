# 004 — Our loss measure can report zero loss when something was lost

**Status:** open
**Raised by:** the Lean formalisation, `impl/lean/GField/Basic.lean`
**Affects:** spec §8, contradiction [001](001-loss-metric.md)

## The contradiction

The source text requires that translation between ontologies is lossy:

$$\mathrm{Loss}(F) > 0$$

It defines no measure, so we chose one ([001](001-loss-metric.md)): term
coverage, in integers, per spec §8.

$$\mathrm{Loss}(F) = \frac{|\text{residue}| \times \mathrm{SCALE}}{|\text{image}| + |\text{residue}|}$$

That measure does not have the property the text requires. With integer
division, a small residue against a large image floors to zero — a translation
that demonstrably lost something reports having lost nothing:

```lean
theorem loss_can_round_to_zero : loss 1000 1 = 0 := by decide
```

One term lost against a thousand kept. `Loss = 0`. The requirement is violated
by our own definition.

## Why it is not merely a bug

Three reasons.

**The conformance corpus cannot catch it.** All twelve vectors pass
`all_losses_positive`. Their fields are small, so the residue is always an
appreciable share of the source. The property holds *of the fields we tested*
and not of the measure. Every implementation agrees with every other, and all
four are wrong together. This is precisely the failure mode that made the Lean
layer worth building: agreement across implementations is not correctness.

**It is a real instance of §5.** The source says a fuller representation records
both the translation and its residue. We built something that records the
residue but can *report* it as negligible. Rounding the residue away is a
smaller version of the mistake §5 is about.

**It bears on §12.** The honest response is not to quietly change the constant
until the tests stay green. It is to state that the current measure is
provisional, and that our first resolution of 001 was insufficient.

## What would resolve it

Four candidates, none yet chosen:

1. **Rational loss.** Carry `(|residue|, |source|)` as a pair and never divide.
   Exact, and removes the failure entirely. Costs the convenience of a single
   comparable number.
2. **Report zero-vs-nonzero separately.** Keep the scalar for magnitude but add
   a boolean `lost_something` that is exact. Cheap; slightly redundant.
3. **Weight terms rather than count them.** Term coverage treats every term as
   equally significant, which is its own unexamined assumption — arguably the
   deeper problem, since §5's "some meaning may be lost" is about significance,
   not cardinality.
4. **Weaken the spec requirement** to "the residue is non-empty" and stop
   claiming anything about the scalar. Honest, and the smallest change.

Option 3 is the one that engages the source text rather than working around it,
and is also the largest. Option 1 is the smallest correct fix.

## Note

This entry exists because a proof assistant contradicted eleven passing test
suites across three languages. Recorded per principle 7: a revision states what
it lost, and here what we lost was a claim we thought we had.
