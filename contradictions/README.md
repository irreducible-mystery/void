# Contradictions

Open problems, tracked as first-class objects rather than as footnotes.

This directory is the mechanism from §4 of the source text, running on a real
clock:

```
persistent contradiction → new distinction → expanded space
```

A contradiction here is not a bug. It is a place where the framework is
answerable to something it cannot currently express. Some will be resolved by a
decision, some by a new distinction that expands the spec, and some will stay
open for a long time. Staying open is a legitimate state; pretending to be
closed is not.

## Lifecycle

| State | Meaning |
|---|---|
| `open` | identified, not yet resolved |
| `persistent` | has survived N revisions unresolved — eligible to generate a distinction |
| `generative` | resolved by expanding the spec; the resolution names what was added |
| `decided` | resolved by choosing, with the alternatives recorded |
| `dissolved` | ceased to be a contradiction because the framing changed |

`persistent` is the interesting state. Per §4, a contradiction that persists and
cannot be reduced within the current space is exactly what licenses adding a new
distinction. That is the same rule `dynamics.generate_dimension` applies to
fields, applied to the project.

## Required sections

Every entry must carry: **Status**, **Raised by**, **The contradiction**,
**Why it is not merely a bug**, and **What would resolve it**. CI enforces this
(`tools/lint_principles.py`) — not as bureaucracy, but because an entry missing
"what would resolve it" is a complaint rather than a contradiction.

## Current entries

| # | Contradiction | Status |
|---|---|---|
| [001](001-loss-metric.md) | The source asserts `Loss(F) > 0` but defines no measure | decided |
| [002](002-persistence-threshold.md) | "Persistent contradiction" has no threshold | decided |
| [003](003-becoming-accessible.md) | "What is becoming accessible" has no formal content | decided |
| [004](004-loss-can-round-to-zero.md) | Our chosen loss measure can report zero loss when something was lost | open |

Entries 001–003 are gaps in the source text. Entry 004 is a defect in **our own
resolution** of 001, found by the Lean formalisation. That distinction matters:
the framework is answerable to its own decisions too.
