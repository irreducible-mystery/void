# 003 — "What is becoming accessible" has no formal content

**Status:** decided
**Raised by:** reading, `docs/inventory.md`
**Affects:** spec §4

## The contradiction

§3 of the source text gives a three-part state:

$$\text{state} = \text{what is actual} + \text{what is accessible} + \text{what is becoming accessible}$$

The first two are defined: actuality is the field, accessibility is
$\mathcal{P}(x)$. The third is named and never defined. It is also the one doing
the distinctive work — without it the state is just "now plus next", which is an
ordinary transition system.

## Why it is not merely a bug

If "becoming accessible" collapses into "accessible", §3 adds nothing to §2, and
the stem cell example loses its point: a stem cell and a differentiated cell are
supposed to differ in reachable futures, not only in current options.

## What would resolve it

**Decided:** monotonically decreasing distance to enablement.

Each event carries a `gap` — a non-negative integer, zero exactly when the
precondition holds. An event is *becoming accessible* when its gap is positive
and has strictly decreased across `BECOMING_WINDOW` ticks. It is not yet
possible, but the field is moving toward it.

Alternatives considered: a derivative of $\mathcal{P}$ over time (needs
$\mathcal{P}$ to be a smooth object, which it is not); and second-order
reachability, "accessible from something accessible" (definable, but that is a
fact about the current space rather than about becoming).

## Outcome

Adopted in spec §4. Conformance asserts that the becoming set is disjoint from
the accessible set — otherwise the distinction would be idle.

**Remaining unease.** Our reading makes "becoming accessible" a fact about
trajectory rather than about capacity. A stem cell arguably has a wider
repertoire *without* currently moving toward any of it. If that is right, this
resolution captures the wrong half of §3 and should be reopened.
