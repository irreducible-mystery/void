"""The seven closing principles of the source text, as executable invariants.

Each test names the principle it enforces. A failure here means the
implementation has drifted from the text, not merely from the spec.
"""

from __future__ import annotations

import inspect

import pytest

import gfield
from gfield import (Event, Field, Model, Observer, Registry, World, apply,
                    becoming_accessible, candidates, entities, instances,
                    partial_map, possibility, read, read_ontology, residual_total,
                    run_tracked, step, translate)


def triangle() -> Field:
    """Three mutually related sites, with one pair the dimensions cannot account for."""
    return Field.seed(
        dims=["d0"], sites=6,
        relations=[(0, 1, [600]), (1, 2, [600]), (0, 2, [600])],
        observed={(0, 1): 900, (1, 2): 600, (0, 2): 600},
    )


# --- 1. relations before isolated entities --------------------------------

def test_no_entity_may_be_declared():
    names = [n for n in dir(gfield) if callable(getattr(gfield, n))]
    offenders = [n for n in names
                 if any(k in n.lower() for k in ("add_entity", "create_entity",
                                                 "new_entity", "make_entity",
                                                 "declare"))]
    assert offenders == [], f"entity declaration API present: {offenders}"


def test_entities_are_a_function_of_relations_alone():
    f = triangle()
    for _ in range(3):
        f = step(f, None)
    assert entities(f) == [(0, 1, 2)]

    g = Field.seed(dims=["d0"], sites=6, relations=[], observed={})
    for _ in range(3):
        g = step(g, None)
    assert entities(g) == [], "with no relations there can be no entities"


def test_weak_coupling_yields_no_entity():
    f = Field.seed(dims=["d0"], sites=4,
                   relations=[(0, 1, [100])], observed={(0, 1): 100})
    for _ in range(4):
        f = step(f, None)
    assert entities(f) == [], "coupling below THETA must not condense into a thing"


# --- 2. events before static states ---------------------------------------

def test_every_transformation_is_recorded():
    f = triangle()
    before = len(f.history)
    f = step(f, Event("feedback", (0, 1)))
    names = [h.name for h in f.history[before:]]
    assert "feedback" in names, "an applied event left no trace in history"


def test_a_field_state_cannot_be_reached_without_a_recorded_event():
    f = triangle()
    e = Event("differentiate", ((0, 1, 2),))
    with pytest.raises(ValueError):
        apply(f, e)  # precondition unmet: |S| < 4


def test_identity_follows_the_arrows_not_the_points():
    f = triangle()
    for _ in range(3):
        f = step(f, None)
    support = entities(f)[0]
    g = step(f, Event("branch", (support,)))
    for _ in range(3):
        g = step(g, None)
    assert support in entities(g), "the original convergence must survive branching"
    assert len(entities(g)) == 2, "branching must produce a second convergence"


# --- 3. transformations before classifications ----------------------------

def test_classification_changes_only_through_transformation():
    f = triangle()
    for _ in range(3):
        f = step(f, None)
    assert entities(f) == [(0, 1, 2)]
    g = step(f, Event("dissolve", ((0, 1, 2),)))
    for _ in range(3):
        g = step(g, None)
    assert entities(g) == [], "dissolving the relations must dissolve the class"


# --- 4. individuation before fixed individuals ----------------------------

def test_individuals_carry_formation_and_dissolution_records():
    f = triangle()
    _, reg = run_tracked(f, [None, None, None, None])
    assert reg.all(), "no individual was ever registered"
    for ind in reg.all():
        assert ind.born_at is not None
        assert ind.formation_event
        assert ind.dissolution_condition
        assert ind.maintained_by


def test_individuals_are_temporary_and_closure_is_recorded():
    f = triangle()
    schedule = [None, None, None, Event("dissolve", ((0, 1, 2),)), None, None, None]
    _, reg = run_tracked(f, schedule)
    closed = [i for i in reg.all() if i.died_at is not None]
    assert closed, "an individual that stopped cohering was not closed out"


def chain() -> Field:
    """A 4-site chain whose weakest internal link is the canonical place to split."""
    return Field.seed(
        dims=["d0"], sites=8,
        relations=[(0, 1, [600]), (1, 2, [900]), (2, 3, [900])],
        observed={(0, 1): 600, (1, 2): 900, (2, 3): 900},
    )


def test_suppressed_alternatives_are_recorded():
    f = chain()
    for _ in range(3):
        f = step(f, None)
    support = entities(f)[0]
    assert support == (0, 1, 2, 3)

    # The split halves the crossing weight, but the field is still accountable
    # to the old coupling. Unless what it is accountable to also changes, the
    # contradiction that opens here is resolved by regenerating that coupling as
    # a new dimension -- and the split undoes itself. So the driver states that
    # the world changed along with the split.
    _, reg = run_tracked(f, [
        (Event("differentiate", (support,)),
         {(0, 1): 300, (1, 2): 1350, (2, 3): 1350}), None, None, None])
    suppressed = [i for i in reg.all() if i.suppressed]
    assert suppressed, "differentiation recorded no unchosen alternative"
    assert any(i.support == (1, 2, 3) for i in reg.all()), "the split produced no individual"


def test_a_split_undoes_itself_while_accountability_is_unchanged():
    """A distinction cannot be imposed on a field still answerable to the old couplings.

    Not a workaround for the test above -- this is the behaviour the spec
    requires, made explicit so it cannot regress silently.
    """
    f = chain()
    for _ in range(3):
        f = step(f, None)
    support = entities(f)[0]
    f = step(f, Event("differentiate", (support,)))
    for _ in range(5):
        f = step(f, None)
    assert any(h.name == "dimension" for h in f.history)
    assert entities(f) == [(0, 1, 2, 3)], (
        "the field should have regenerated the coupling the split tried to remove")


# --- 5. possibility-generation before a fixed possibility space -----------

def test_possibility_is_computed_not_declared():
    f = triangle()
    for _ in range(3):
        f = step(f, None)
    p = possibility(f)
    assert p, "no transformation is accessible from a live field"
    assert set(p) <= set(instances(f))
    assert all(gfield.enabled(f, e) for e in p)


def test_the_space_itself_can_grow():
    """The central claim: a persistent, irreducible contradiction adds a coordinate."""
    f = triangle()
    assert len(f.dims) == 1
    for _ in range(3):
        f = step(f, None)
    assert len(f.dims) == 2, "the field failed to generate a dimension"
    assert any(h.name == "dimension" for h in f.history)


def test_the_generated_dimension_resolves_what_generated_it():
    f = triangle()
    assert residual_total(f) == 300
    for _ in range(3):
        f = step(f, None)
    assert residual_total(f) == 0, (
        "the new coordinate must absorb the residual that produced it")


def test_a_reducible_contradiction_does_not_generate_a_dimension():
    """Persistence alone is not enough; the text requires irreducibility."""
    f = Field.seed(dims=["d0"], sites=6,
                   relations=[(0, 1, [600]), (1, 2, [600]), (0, 2, [600])],
                   observed={(0, 1): 600, (1, 2): 600, (0, 2): 600})
    for _ in range(5):
        f = step(f, None)
    assert len(f.dims) == 1, "a field in accord with itself invented a distinction"


def test_becoming_accessible_is_distinct_from_accessible():
    f = triangle()
    for _ in range(4):
        f = step(f, None)
    assert set(becoming_accessible(f)).isdisjoint(set(possibility(f)))


# --- 6. co-evolution before detached observation --------------------------

def test_back_action_must_be_declared():
    with pytest.raises(ValueError):
        Observer(site=0, back_action=None)


def test_observation_changes_what_is_observed():
    f = triangle()
    for _ in range(3):
        f = step(f, None)
    before = entities(f)
    reading, g = read(f, Observer(site=0, back_action=100))
    assert reading > 0
    for _ in range(3):
        g = step(g, None)
    assert entities(g) != before, "a probe with back-action left the field unchanged"


def test_a_detached_observer_must_say_so_and_then_changes_nothing():
    f = triangle()
    for _ in range(3):
        f = step(f, None)
    reading, g = read(f, Observer(site=0, back_action=0))
    assert reading > 0
    assert g.digest() == f.digest()


# --- 7. revisability before final completeness ----------------------------

def test_no_completeness_predicate_exists():
    offenders = []
    for name in dir(gfield):
        obj = getattr(gfield, name)
        if any(k in name.lower() for k in ("complete", "total_model", "exhaustive")):
            offenders.append(name)
        if inspect.isclass(obj):
            offenders += [f"{name}.{m}" for m in dir(obj)
                          if "complete" in m.lower() and not m.startswith("__")]
    assert offenders == [], f"a completeness claim is expressible: {offenders}"


def test_a_revision_must_state_its_residue():
    f = triangle()
    m = Model(field=f)
    with pytest.raises(ValueError):
        m.revise(f, changed="something", lost="")
    m2 = m.revise(f, changed="something", lost="none identified")
    assert m2.revisions[-1].lost


def test_the_model_reports_its_limits():
    m = Model(field=triangle())
    assert m.limits(), "a model that claims no limits is claiming completeness"


# --- ontological pluralism (section 5) ------------------------------------

def test_translation_between_ontologies_always_loses_something():
    f = triangle()
    for _ in range(3):
        f = step(f, None)
    obs = [Observer(site=0, back_action=0)]
    for src in ("O1", "O2", "O3"):
        for tgt in ("O1", "O2", "O3"):
            if src == tgt:
                continue
            terms = read_ontology(f, src, obs)
            t = translate(terms, src, tgt)
            assert t.loss() > 0, f"{src}->{tgt} claimed a lossless translation"
            assert t.residue, f"{src}->{tgt} produced no residue to record"


def test_worlds_map_only_partially():
    f = triangle()
    for _ in range(3):
        f = step(f, None)
    f = step(f, Event("new_level", ((0, 1, 2),)))
    a = World("a", {"d0": 1000})
    b = World("b", {"d1": 1000})
    m = partial_map(f, a, b)
    union = set(a.support(f)) | set(b.support(f))
    assert len(m) < len(union), "the mapping between worlds was total"


def test_determinism_of_the_specified_generator():
    assert gfield.xorshift64s(1) == 5180492295206395165
    assert gfield.scale_mul(-1500, 500) == -750, "must truncate toward zero"
    assert gfield.scale_mul(1500, 500) == 750
