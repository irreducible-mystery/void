#!/usr/bin/env python3
"""Enforce the seven principles at the level of the repository itself.

The implementations enforce the principles on *fields*. This enforces them on
the project: a repository that models and modifies its own organisation (§12)
has to be accountable to the same rules it applies.

Run:  python3 tools/lint_principles.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {".git", "node_modules", "dist", ".lake", "__pycache__", ".venv",
             "build", ".pytest_cache"}

# Principle 7. Phrases that assert closure. The check is deliberately narrow:
# it fires on claims *about this work*, not on the word "complete" as ordinary
# English ("the build completed", "a complete graph").
COMPLETENESS_CLAIMS = [
    r"\bthe (?:framework|model|spec(?:ification)?|field|theory) is (?:now )?complete\b",
    r"\bcomplete (?:framework|model|specification|account|inventory) of\b",
    r"\bfully (?:captures|specifies|describes) (?:the|all)\b",
    r"\bexhaustive (?:account|model|specification|inventory)\b",
    r"\bcovers (?:every|all) possible\b",
    r"\bnothing (?:further |more )?remains\b",
]

CONTRADICTION_SECTIONS = [
    "**Status:**",
    "**Raised by:**",
    "## The contradiction",
    "## Why it is not merely a bug",
    "## What would resolve it",
]


def walk(*globs: str):
    for g in globs:
        for p in ROOT.glob(g):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.is_file():
                yield p


def check_no_completeness_claims() -> list[str]:
    """Principle 7: no artifact may assert completeness."""
    out = []
    for p in walk("**/*.md"):
        # The lint's own definitions, and the contradiction describing the
        # defect, necessarily quote these phrases.
        if p.name == "lint_principles.py":
            continue
        text = p.read_text(encoding="utf8", errors="replace")
        for pattern in COMPLETENESS_CLAIMS:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                line = text[: m.start()].count("\n") + 1
                out.append(
                    f"{p.relative_to(ROOT)}:{line}: asserts completeness "
                    f"({m.group(0)!r}) -- principle 7")
    return out


def check_contradictions_are_well_formed() -> list[str]:
    """A contradiction missing 'what would resolve it' is a complaint, not a contradiction."""
    out = []
    d = ROOT / "contradictions"
    if not d.is_dir():
        return ["contradictions/ is missing -- the mechanism from section 4 has no home"]
    entries = sorted(p for p in d.glob("*.md") if p.name != "README.md")
    if not entries:
        out.append("contradictions/ has no entries; the known gaps in "
                   "docs/inventory.md should be recorded there")
    for p in entries:
        text = p.read_text(encoding="utf8")
        for section in CONTRADICTION_SECTIONS:
            if section not in text:
                out.append(f"{p.relative_to(ROOT)}: missing required section {section!r}")
    return out


def check_open_choices_are_tracked() -> list[str]:
    """Every choice the spec makes on the text's behalf must point to a live record."""
    out = []
    spec = ROOT / "docs" / "spec" / "core.md"
    if not spec.is_file():
        return ["docs/spec/core.md is missing"]
    text = spec.read_text(encoding="utf8")
    marks = text.count("[OPEN → CHOICE]")
    refs = set(re.findall(r"contradictions/(\d{3})[-\w]*\.md", text))
    if marks == 0:
        out.append("docs/spec/core.md declares no [OPEN -> CHOICE] markers; the "
                   "source text leaves gaps and the spec must say where it filled them")
    for ref in sorted(refs):
        if not list((ROOT / "contradictions").glob(f"{ref}-*.md")):
            out.append(f"docs/spec/core.md references contradictions/{ref} which does not exist")
    if marks > len(refs):
        out.append(f"docs/spec/core.md has {marks} [OPEN -> CHOICE] markers but "
                   f"only {len(refs)} contradiction references")
    return out


def check_revisions_state_their_residue() -> list[str]:
    """Principle 7: every revision records what it changed and what it lost."""
    out = []
    d = ROOT / "revisions"
    if not d.is_dir():
        return ["revisions/ is missing -- M_t -> M_{t+1} has no record"]
    entries = sorted(p for p in d.glob("*.md") if p.name != "README.md")
    if not entries:
        out.append("revisions/ has no entries")
    for p in entries:
        text = p.read_text(encoding="utf8")
        if "## What was lost" not in text:
            out.append(f"{p.relative_to(ROOT)}: no 'What was lost' section -- "
                       f"a revision that claims to have lost nothing must say so explicitly")
    return out


def check_no_declared_entities() -> list[str]:
    """Principle 1, across implementations: no API may create an entity."""
    out = []
    banned = re.compile(r"\b(?:def|function|fn|const)\s+(add_entity|create_entity|"
                        r"new_entity|make_entity|declare_entity)\b")
    for p in walk("impl/**/*.py", "impl/**/*.ts", "impl/**/*.jl", "impl/**/*.lean"):
        for i, line in enumerate(p.read_text(encoding="utf8", errors="replace").splitlines(), 1):
            m = banned.search(line)
            if m:
                out.append(f"{p.relative_to(ROOT)}:{i}: declares an entity "
                           f"({m.group(1)}) -- principle 1")
    return out


CHECKS = [
    ("principle 1 -- relations before isolated entities", check_no_declared_entities),
    ("principle 7 -- no completeness claims", check_no_completeness_claims),
    ("principle 7 -- revisions state their residue", check_revisions_state_their_residue),
    ("section 4 -- contradictions are well formed", check_contradictions_are_well_formed),
    ("section 4 -- spec choices are tracked", check_open_choices_are_tracked),
]


def main() -> int:
    failures: list[str] = []
    for name, fn in CHECKS:
        problems = fn()
        status = "ok" if not problems else f"{len(problems)} problem(s)"
        print(f"  [{status:>15}] {name}")
        failures.extend(problems)

    if failures:
        print("\nprinciple lint failed:\n", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1
    print("\nall principle checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
