import pytest
from hypothesis import given
from hypothesis import strategies as st

from linkeval.core import (
    RecordCluster,
    RecordPair,
    RecordPairSet,
    RecordUniverse,
    cluster_to_pairs,
    pairs_to_clusters,
)


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


def test_record_cluster_normalizes_records_by_universe_order() -> None:
    universe = RecordUniverse(["A", "B", "C", "D"])

    cluster = RecordCluster(universe, ["C", "A", "B"])

    assert cluster.records == ("A", "B", "C")


def test_record_cluster_collapses_duplicate_records() -> None:
    universe = RecordUniverse(["A", "B", "C"])

    cluster = RecordCluster(universe, ["C", "A", "A", "B"])

    assert cluster.records == ("A", "B", "C")
    assert len(cluster) == 3


def test_record_cluster_rejects_record_outside_universe() -> None:
    universe = RecordUniverse(["A", "B"])

    with pytest.raises(KeyError):
        RecordCluster(universe, ["A", "X"])


def test_record_cluster_rejects_empty_cluster() -> None:
    universe = RecordUniverse(["A", "B"])

    with pytest.raises(ValueError):
        RecordCluster(universe, [])


def test_singleton_record_cluster_is_valid() -> None:
    universe = RecordUniverse(["A", "B"])

    cluster = RecordCluster(universe, ["A"])

    assert cluster.records == ("A",)
    assert len(cluster) == 1


def test_record_cluster_reports_membership() -> None:
    universe = RecordUniverse(["A", "B", "C"])
    cluster = RecordCluster(universe, ["A", "C"])

    assert "A" in cluster
    assert "C" in cluster
    assert "B" not in cluster


def test_record_cluster_iteration_is_deterministic() -> None:
    universe = RecordUniverse(["A", "B", "C"])
    cluster = RecordCluster(universe, ["C", "A", "B"])

    assert list(cluster) == ["A", "B", "C"]


def test_record_cluster_exposes_universe() -> None:
    universe = RecordUniverse(["A", "B"])

    cluster = RecordCluster(universe, ["A"])

    assert cluster.universe is universe


def test_record_clusters_ignore_input_order_for_equality() -> None:
    universe = RecordUniverse(["A", "B", "C"])

    first = RecordCluster(universe, ["A", "B", "C"])
    second = RecordCluster(universe, ["C", "A", "B"])

    assert first == second


def test_equal_record_clusters_have_same_hash() -> None:
    universe = RecordUniverse(["A", "B", "C"])

    first = RecordCluster(universe, ["A", "B", "C"])
    second = RecordCluster(universe, ["C", "A", "B"])

    assert hash(first) == hash(second)


def test_record_clusters_from_different_universes_are_not_equal() -> None:
    first_universe = RecordUniverse(["A", "B"])
    second_universe = RecordUniverse(["A", "B"])

    first = RecordCluster(first_universe, ["A", "B"])
    second = RecordCluster(second_universe, ["A", "B"])

    assert first != second


def test_record_cluster_is_not_equal_to_unrelated_object() -> None:
    universe = RecordUniverse(["A", "B"])
    cluster = RecordCluster(universe, ["A", "B"])

    assert cluster != ("A", "B")


@given(
    first=st.text(min_size=1),
    second=st.text(min_size=1),
    third=st.text(min_size=1),
)
def test_record_cluster_is_invariant_to_input_order(
    first: str,
    second: str,
    third: str,
) -> None:
    unique_records = list(dict.fromkeys([first, second, third]))

    universe = RecordUniverse(unique_records)

    forward = RecordCluster(universe, unique_records)
    reverse = RecordCluster(universe, list(reversed(unique_records)))

    assert forward == reverse
    assert forward.records == reverse.records
    assert hash(forward) == hash(reverse)


@given(
    first=st.text(min_size=1),
    second=st.text(min_size=1),
)
def test_record_cluster_is_invariant_to_duplicate_records(
    first: str,
    second: str,
) -> None:
    unique_records = list(dict.fromkeys([first, second]))

    universe = RecordUniverse(unique_records)

    cluster = RecordCluster(
        universe,
        unique_records + unique_records + unique_records,
    )

    assert cluster.records == tuple(unique_records)
    assert len(cluster) == len(unique_records)


def test_singleton_cluster_converts_to_empty_pair_set() -> None:
    universe = RecordUniverse(["A"])
    cluster = RecordCluster(universe, ["A"])

    pair_set = cluster_to_pairs(cluster)

    assert pair_set.universe is universe
    assert len(pair_set) == 0


def test_two_record_cluster_converts_to_one_pair() -> None:
    universe = RecordUniverse(["A", "B"])
    cluster = RecordCluster(universe, ["A", "B"])

    pair_set = cluster_to_pairs(cluster)

    assert len(pair_set) == 1
    assert [pair.records for pair in pair_set] == [
        ("A", "B"),
    ]


def test_three_record_cluster_converts_to_all_unordered_pairs() -> None:
    universe = RecordUniverse(["A", "B", "C"])
    cluster = RecordCluster(universe, ["C", "A", "B"])

    pair_set = cluster_to_pairs(cluster)

    assert [pair.records for pair in pair_set] == [
        ("A", "B"),
        ("A", "C"),
        ("B", "C"),
    ]


def test_cluster_to_pairs_uses_cluster_universe() -> None:
    universe = RecordUniverse(["A", "B", "C"])
    cluster = RecordCluster(universe, ["A", "B", "C"])

    pair_set = cluster_to_pairs(cluster)

    assert pair_set.universe is universe

    for pair in pair_set:
        assert pair.universe is universe


def test_cluster_to_pairs_does_not_modify_cluster() -> None:
    universe = RecordUniverse(["A", "B", "C"])
    cluster = RecordCluster(universe, ["C", "A", "B"])
    original_records = cluster.records

    cluster_to_pairs(cluster)

    assert cluster.records == original_records


def test_cluster_to_pairs_generates_no_self_pairs() -> None:
    universe = RecordUniverse(["A", "B", "C"])
    cluster = RecordCluster(universe, ["A", "B", "C"])

    pair_set = cluster_to_pairs(cluster)

    for pair in pair_set:
        first, second = pair.records
        assert first != second


def test_cluster_to_pairs_generates_no_duplicate_pairs() -> None:
    universe = RecordUniverse(["A", "B", "C", "D"])
    cluster = RecordCluster(universe, ["A", "B", "C", "D"])

    pair_set = cluster_to_pairs(cluster)

    assert len(pair_set) == len(set(pair_set))


@given(st.lists(st.text(min_size=1), min_size=1, max_size=12))
def test_cluster_to_pairs_obeys_pair_count_invariant(records: list[str]) -> None:
    unique_records = list(dict.fromkeys(records))

    universe = RecordUniverse(unique_records)
    cluster = RecordCluster(universe, unique_records)

    pair_set = cluster_to_pairs(cluster)

    n_records = len(unique_records)
    expected_pairs = n_records * (n_records - 1) // 2

    assert len(pair_set) == expected_pairs


def test_empty_pair_set_converts_to_no_clusters() -> None:
    universe = RecordUniverse(["A", "B"])
    pair_set = RecordPairSet(universe, [])

    clusters = pairs_to_clusters(pair_set)

    assert clusters == ()


def test_single_edge_converts_to_one_cluster() -> None:
    universe = RecordUniverse(["A", "B"])
    pair_set = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )

    clusters = pairs_to_clusters(pair_set)

    assert len(clusters) == 1
    assert clusters[0].records == ("A", "B")
    assert clusters[0].universe is universe


def test_transitive_pairs_form_one_cluster() -> None:
    universe = RecordUniverse(["A", "B", "C"])
    pair_set = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "B", "C"),
        ],
    )

    clusters = pairs_to_clusters(pair_set)

    assert len(clusters) == 1
    assert clusters[0].records == ("A", "B", "C")


def test_disconnected_pairs_form_separate_clusters() -> None:
    universe = RecordUniverse(["A", "B", "C", "D"])
    pair_set = RecordPairSet(
        universe,
        [
            RecordPair(universe, "C", "D"),
            RecordPair(universe, "A", "B"),
        ],
    )

    clusters = pairs_to_clusters(pair_set)

    assert [cluster.records for cluster in clusters] == [
        ("A", "B"),
        ("C", "D"),
    ]


def test_pairs_to_clusters_does_not_emit_unused_universe_records() -> None:
    universe = RecordUniverse(["A", "B", "C", "D"])
    pair_set = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )

    clusters = pairs_to_clusters(pair_set)

    assert [cluster.records for cluster in clusters] == [
        ("A", "B"),
    ]


def test_pairs_to_clusters_uses_pair_set_universe() -> None:
    universe = RecordUniverse(["A", "B", "C"])
    pair_set = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "B", "C"),
        ],
    )

    clusters = pairs_to_clusters(pair_set)

    for cluster in clusters:
        assert cluster.universe is universe


def test_pairs_to_clusters_does_not_modify_pair_set() -> None:
    universe = RecordUniverse(["A", "B", "C"])
    pairs = [
        RecordPair(universe, "A", "B"),
        RecordPair(universe, "B", "C"),
    ]
    pair_set = RecordPairSet(universe, pairs)
    original_pairs = tuple(pair.records for pair in pair_set)

    pairs_to_clusters(pair_set)

    assert tuple(pair.records for pair in pair_set) == original_pairs


def test_no_record_appears_in_multiple_clusters() -> None:
    universe = RecordUniverse(["A", "B", "C", "D", "E"])
    pair_set = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "B", "C"),
            RecordPair(universe, "D", "E"),
        ],
    )

    clusters = pairs_to_clusters(pair_set)

    records = [record for cluster in clusters for record in cluster]

    assert len(records) == len(set(records))


def test_pairs_to_clusters_handles_cycles() -> None:
    universe = RecordUniverse(["A", "B", "C"])
    pair_set = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "B", "C"),
            RecordPair(universe, "A", "C"),
        ],
    )

    clusters = pairs_to_clusters(pair_set)

    assert len(clusters) == 1
    assert clusters[0].records == ("A", "B", "C")


@given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
def test_complete_cluster_pair_round_trip_preserves_cluster(
    records: list[str],
) -> None:
    unique_records = list(dict.fromkeys(records))

    universe = RecordUniverse(unique_records)
    cluster = RecordCluster(universe, unique_records)

    pair_set = cluster_to_pairs(cluster)
    clusters = pairs_to_clusters(pair_set)

    if len(unique_records) == 1:
        assert clusters == ()
    else:
        assert len(clusters) == 1
        assert clusters[0] == cluster
