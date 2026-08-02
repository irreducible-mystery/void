# 002 — "Persistent contradiction" has no threshold

**Status:** decided
**Raised by:** reading, `docs/inventory.md`
**Affects:** spec §5

## The contradiction

§4 of the source text names the mechanism of dimensional generation:

$$\text{persistent contradiction} \rightarrow \text{new distinction} \rightarrow \text{expanded space}$$

But "persistent" is unquantified. How long must a contradiction last? Measured
against what? Without an answer the mechanism cannot be implemented at all —
either every transient disagreement generates a dimension, or none does.

## Why it is not merely a bug

The threshold is doing real conceptual work. Too low and the field generates
distinctions for noise; too high and it never generates any. The text's
examples — germ theory, ecosystems, robustness versus resilience — are all cases
where a contradiction persisted for a long time against sustained effort to
resolve it within the existing space. That suggests persistence alone was never
the whole criterion.

## What would resolve it

**Decided:** two conditions, not one.

1. `WINDOW = 3` consecutive ticks above `TAU = 100`, and
2. **irreducibility** — no presently accessible transformation reduces the total
   residual.

The second is the important half and is not in the text explicitly, though it is
implied by the examples. It is what stops the field generating a coordinate for
a contradiction it could simply have resolved by acting.

## Outcome

Adopted in spec §5. Conformance vector `L4-accord-generates-nothing` pins the
negative case: a field in accord with what it is accountable to invents nothing.

The specific constants remain arbitrary and are the weakest part of this
resolution. What is *not* arbitrary is the two-condition structure.
