# 001 — The source asserts `Loss(F) > 0` but defines no measure

**Status:** decided (superseded in part by [004](004-loss-can-round-to-zero.md))
**Raised by:** reading, `docs/inventory.md`
**Affects:** spec §8

## The contradiction

§5 of the source text requires that translation between ontologies leaves a
residue:

$$\mathrm{Loss}(F) > 0$$

It gives no definition of `Loss`. Without one the requirement is unfalsifiable:
any implementation could satisfy it by declaring a constant.

## Why it is not merely a bug

The text's claim is substantive — that object-language and process-language do
not fully cover one another — but a claim about magnitudes needs a magnitude.
Choosing one is not a detail; it decides what "some meaning may be lost" means.

## What would resolve it

**Decided:** term coverage. The residue is the list of source terms with no
target term, and loss is its share of the source, in fixed point.

Alternatives considered and rejected for v0: information-theoretic measures
(require a distribution over terms we do not have), and structural measures
(require the ontologies to be presented as categories, which is level 6 work).

## Outcome

Adopted in spec §8. **Subsequently found insufficient** — see
[004](004-loss-can-round-to-zero.md). The decision stands as the current measure
while the defect is open.
