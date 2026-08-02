"""The reference implementation against the shared corpus.

The other three implementations run the same vectors. If this passes and one of
them does not, they disagree, and the spec is the arbiter.
"""

from __future__ import annotations

from gfield.conformance import check_all, load_corpus, run_vector


def test_corpus_is_not_empty():
    assert load_corpus(), "no conformance vectors found"


def test_reference_passes_the_corpus():
    passed, failures = check_all()
    assert not failures, "\n".join(failures)
    assert passed == len(load_corpus())


def test_hand_written_expectations_are_what_they_claim():
    """The digests are generated; these are not. Only these carry evidence."""
    for vec in load_corpus():
        hand = vec["expect"].get("hand_written")
        assert hand, f"{vec['id']} has no hand-written expectation"
        actual = run_vector(vec)
        for k, want in hand.items():
            assert actual["checks"][k] == want, (
                f"{vec['id']}: spec says {k}={want!r}, got {actual['checks'][k]!r}")


def test_every_level_is_covered():
    levels = {v["level"] for v in load_corpus()}
    assert {2, 3, 4, 5} <= levels, f"levels missing from the corpus: {levels}"


def test_level_6_has_no_vectors():
    """Open becoming is a constraint on assertion, not a test target.

    A suite claiming to verify it would be asserting the completeness the source
    text rejects.
    """
    assert not [v for v in load_corpus() if v["level"] >= 6]
