import pytest
from hypothesis import given
from hypothesis import strategies as st

from linkeval.core import RecordPair, RecordPairSet, RecordUniverse


def test_record_universe_preserves_input_order() -> None:
    records = ["A17", 25, ("source", 3)]

    universe = RecordUniverse(records)

    assert universe.records == ("A17", 25, ("source", 3))


def test_record_universe_assigns_positions_from_input_order() -> None:
    records = ["A17", 25, ("source", 3)]

    universe = RecordUniverse(records)

    assert universe.position("A17") == 0
    assert universe.position(25) == 1
    assert universe.position(("source", 3)) == 2


def test_record_universe_rejects_duplicate_records() -> None:
    records = ["A17", "B92", "A17"]

    with pytest.raises(ValueError):
        RecordUniverse(records)


def test_record_universe_reports_membership() -> None:
    universe = RecordUniverse(["A17", "B92"])

    assert "A17" in universe
    assert "B92" in universe
    assert "X03" not in universe


def test_record_universe_position_rejects_unknown_record() -> None:
    universe = RecordUniverse(["A17", "B92"])

    with pytest.raises(KeyError):
        universe.position("X03")


def test_record_universe_rejects_unordered_set_input() -> None:
    records = {"A17", "B92", "X03"}

    with pytest.raises(TypeError):
        RecordUniverse(records)


def test_record_pair_preserves_canonical_universe_order() -> None:
    universe = RecordUniverse(["A17", "B92", "X03"])

    pair = RecordPair(universe, "B92", "A17")

    assert pair.records == ("A17", "B92")


def test_record_pair_canonicalisation_supports_heterogeneous_ids() -> None:
    universe = RecordUniverse(["A17", 25, ("source", 3)])

    pair = RecordPair(universe, 25, "A17")

    assert pair.records == ("A17", 25)


def test_record_pair_rejects_self_pair() -> None:
    universe = RecordUniverse(["A17", "B92"])

    with pytest.raises(ValueError):
        RecordPair(universe, "A17", "A17")


def test_record_pair_rejects_record_outside_universe() -> None:
    universe = RecordUniverse(["A17", "B92"])

    with pytest.raises(KeyError):
        RecordPair(universe, "A17", "X03")


def test_reversed_record_pairs_are_equal() -> None:
    universe = RecordUniverse(["A17", "B92"])

    first = RecordPair(universe, "A17", "B92")
    second = RecordPair(universe, "B92", "A17")

    assert first == second


def test_reversed_record_pairs_have_same_hash() -> None:
    universe = RecordUniverse(["A17", "B92"])

    first = RecordPair(universe, "A17", "B92")
    second = RecordPair(universe, "B92", "A17")

    assert hash(first) == hash(second)


def test_duplicate_logical_pairs_collapse_in_set() -> None:
    universe = RecordUniverse(["A17", "B92"])

    pairs = {
        RecordPair(universe, "A17", "B92"),
        RecordPair(universe, "B92", "A17"),
    }

    assert len(pairs) == 1


@given(
    first=st.text(min_size=1),
    second=st.text(min_size=1),
)
def test_record_pair_canonicalisation_is_symmetric(
    first: str,
    second: str,
) -> None:
    if first == second:
        return

    universe = RecordUniverse([first, second])

    forward = RecordPair(universe, first, second)
    reverse = RecordPair(universe, second, first)

    assert forward == reverse
    assert forward.records == reverse.records
    assert hash(forward) == hash(reverse)


def test_record_pair_is_not_equal_to_unrelated_object() -> None:
    universe = RecordUniverse(["A17", "B92"])
    pair = RecordPair(universe, "A17", "B92")

    assert pair != ("A17", "B92")


def test_record_pairs_from_different_universes_are_not_equal() -> None:
    first_universe = RecordUniverse(["A17", "B92"])
    second_universe = RecordUniverse(["A17", "B92"])

    first = RecordPair(first_universe, "A17", "B92")
    second = RecordPair(second_universe, "A17", "B92")

    assert first != second


def test_record_pair_exposes_universe() -> None:
    universe = RecordUniverse(["A", "B"])

    pair = RecordPair(universe, "A", "B")

    assert pair.universe is universe


def test_empty_record_pair_set_is_valid() -> None:
    universe = RecordUniverse(["A", "B"])

    pair_set = RecordPairSet(universe, [])

    assert len(pair_set) == 0


def test_record_pair_set_reports_length() -> None:
    universe = RecordUniverse(["A", "B", "C"])
    pair_ab = RecordPair(universe, "A", "B")
    pair_ac = RecordPair(universe, "A", "C")

    pair_set = RecordPairSet(universe, [pair_ab, pair_ac])

    assert len(pair_set) == 2


def test_record_pair_set_reports_membership() -> None:
    universe = RecordUniverse(["A", "B", "C"])
    pair_ab = RecordPair(universe, "A", "B")
    pair_ac = RecordPair(universe, "A", "C")

    pair_set = RecordPairSet(universe, [pair_ab])

    assert pair_ab in pair_set
    assert pair_ac not in pair_set


def test_record_pair_set_collapses_duplicate_pairs() -> None:
    universe = RecordUniverse(["A", "B"])
    pair = RecordPair(universe, "A", "B")

    pair_set = RecordPairSet(universe, [pair, pair])

    assert len(pair_set) == 1


def test_record_pair_set_collapses_reversed_logical_pairs() -> None:
    universe = RecordUniverse(["A", "B"])
    forward = RecordPair(universe, "A", "B")
    reverse = RecordPair(universe, "B", "A")

    pair_set = RecordPairSet(universe, [forward, reverse])

    assert len(pair_set) == 1


def test_record_pair_set_rejects_pair_from_different_universe() -> None:
    first_universe = RecordUniverse(["A", "B"])
    second_universe = RecordUniverse(["A", "B"])
    pair = RecordPair(second_universe, "A", "B")

    with pytest.raises(ValueError):
        RecordPairSet(first_universe, [pair])


def test_record_pair_set_iteration_uses_universe_order() -> None:
    universe = RecordUniverse(["A", "B", "C"])
    pair_bc = RecordPair(universe, "B", "C")
    pair_ab = RecordPair(universe, "A", "B")

    pair_set = RecordPairSet(universe, [pair_bc, pair_ab])

    assert [pair.records for pair in pair_set] == [
        ("A", "B"),
        ("B", "C"),
    ]


def test_record_pair_set_exposes_universe() -> None:
    universe = RecordUniverse(["A", "B"])

    pair_set = RecordPairSet(universe, [])

    assert pair_set.universe is universe


@given(
    first=st.text(min_size=1),
    second=st.text(min_size=1),
)
def test_record_pair_set_is_invariant_to_pair_orientation(
    first: str,
    second: str,
) -> None:
    if first == second:
        return

    universe = RecordUniverse([first, second])

    forward = RecordPair(universe, first, second)
    reverse = RecordPair(universe, second, first)

    pair_set = RecordPairSet(universe, [forward, reverse])

    assert len(pair_set) == 1
    assert forward in pair_set
    assert reverse in pair_set


@given(
    first=st.text(min_size=1),
    second=st.text(min_size=1),
)
def test_record_pair_set_is_invariant_to_duplicate_pairs(
    first: str,
    second: str,
) -> None:
    if first == second:
        return

    universe = RecordUniverse([first, second])
    pair = RecordPair(universe, first, second)

    pair_set = RecordPairSet(universe, [pair, pair, pair])

    assert len(pair_set) == 1
    assert pair in pair_set


def test_record_pair_set_iteration_uses_second_position_as_tiebreaker() -> None:
    universe = RecordUniverse(["A", "B", "C"])
    pair_ac = RecordPair(universe, "A", "C")
    pair_ab = RecordPair(universe, "A", "B")

    pair_set = RecordPairSet(universe, [pair_ac, pair_ab])

    assert [pair.records for pair in pair_set] == [
        ("A", "B"),
        ("A", "C"),
    ]
