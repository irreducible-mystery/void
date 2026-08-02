"""Runner for the shared conformance corpus.

Every implementation in impl/ runs the same vectors from conformance/vectors
and must produce identical digests. Two kinds of check are applied:

  digest      -- cross-implementation agreement. Generated from this reference
                 implementation, so it proves the four agree, not that any of
                 them is right.
  assertions  -- hand-written from docs/spec/core.md. These are the ones that
                 can fail for the reference implementation too, and so are the
                 ones that carry evidence.
"""

from __future__ import annotations

import json
from pathlib import Path

from .core import Field, entities
from .dynamics import step
from .events import Event, becoming_accessible, possibility
from .views import ONTOLOGIES, Observer, World, partial_map, read, read_ontology, translate


def build(seed: dict) -> Field:
    observed = {tuple(int(x) for x in k.split(",")): v
                for k, v in (seed.get("observed") or {}).items()}
    return Field.seed(seed["dims"], seed["sites"],
                      [(r[0], r[1], r[2]) for r in seed["relations"]], observed)


def run_vector(vec: dict) -> dict:
    f = build(vec["seed"])
    for entry in vec.get("schedule", []):
        e, obs = None, None
        if entry is not None:
            if entry.get("name"):
                e = Event(entry["name"], tuple(
                    tuple(p) if isinstance(p, list) else p for p in entry["params"]))
            if entry.get("observe"):
                obs = {tuple(int(x) for x in k.split(",")): v
                       for k, v in entry["observe"].items()}
        f = step(f, e, obs)

    result = {"digest": f.digest()}
    checks: dict[str, object] = {
        "dimension_count": len(f.dims),
        "residual_total": f.digest()["residual_total"],
        "entity_count": len(entities(f)),
        "accessible_count": len(possibility(f)),
        "becoming_count": len(becoming_accessible(f)),
        "generated_dimension": any(h.name == "dimension" for h in f.history),
        "history_complete": all(h.tick <= f.tick for h in f.history),
    }

    if vec.get("check_translation"):
        obs = [Observer(site=0, back_action=0)]
        losses = {}
        for src in ONTOLOGIES:
            for tgt in ONTOLOGIES:
                if src != tgt:
                    t = translate(read_ontology(f, src, obs), src, tgt)
                    losses[f"{src}->{tgt}"] = t.loss()
        checks["translation_losses"] = losses
        checks["all_losses_positive"] = all(v > 0 for v in losses.values())

    if vec.get("check_observer"):
        before = [list(s) for s in entities(f)]
        probe = Observer(site=vec["check_observer"]["site"],
                         back_action=vec["check_observer"]["back_action"])
        _, g = read(f, probe)
        for _ in range(3):
            g = step(g, None)
        checks["entities_before_observation"] = before
        checks["entities_after_observation"] = [list(s) for s in entities(g)]
        checks["observation_changed_field"] = before != [list(s) for s in entities(g)]

    if vec.get("check_worlds"):
        spec = vec["check_worlds"]
        wi = World(spec["a"]["name"], spec["a"]["relevance"])
        wj = World(spec["b"]["name"], spec["b"]["relevance"])
        m = partial_map(f, wi, wj)
        checks["world_a_support"] = wi.support(f)
        checks["world_b_support"] = wj.support(f)
        checks["partial_map_domain"] = sorted(m)
        checks["map_is_partial"] = len(m) < len(set(wi.support(f)) | set(wj.support(f)))

    result["checks"] = checks
    return result


def compare(expected: dict, actual: dict) -> list[str]:
    failures = []
    if "digest" in expected and expected["digest"] != actual["digest"]:
        for k in sorted(set(expected["digest"]) | set(actual["digest"])):
            if expected["digest"].get(k) != actual["digest"].get(k):
                failures.append(
                    f"digest.{k}: expected {expected['digest'].get(k)!r}, "
                    f"got {actual['digest'].get(k)!r}")
    for k, want in (expected.get("checks") or {}).items():
        got = actual["checks"].get(k)
        if want != got:
            failures.append(f"checks.{k}: expected {want!r}, got {got!r}")
    return failures


def corpus_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "conformance" / "vectors"


def load_corpus(directory: Path | None = None) -> list[dict]:
    d = directory or corpus_dir()
    return [json.loads(p.read_text()) for p in sorted(d.glob("*.json"))]


def check_all(directory: Path | None = None) -> tuple[int, list[str]]:
    passed, failures = 0, []
    for vec in load_corpus(directory):
        actual = run_vector(vec)
        problems = compare(vec.get("expect", {}), actual)
        if problems:
            failures.extend(f"[{vec['id']}] {p}" for p in problems)
        else:
            passed += 1
    return passed, failures
