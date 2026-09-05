import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from linkeval.core import (
    PairwiseCounts,
    RecordCluster,
    RecordPair,
    RecordPairSet,
    RecordUniverse,
    cluster_to_pairs,
    false_link_rate,
    missing_match_rate,
    pairs_to_clusters,
    pairwise_counts,
    pairwise_f1,
    pairwise_precision,
    pairwise_recall,
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


def test_pairwise_counts_perfect_prediction() -> None:
    universe = RecordUniverse(["A", "B", "C", "D"])

    truth = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "C", "D"),
        ],
    )
    prediction = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "C", "D"),
        ],
    )

    counts = pairwise_counts(truth, prediction)

    assert counts == PairwiseCounts(tp=2, fp=0, fn=0)


def test_pairwise_counts_partial_prediction() -> None:
    universe = RecordUniverse(["A", "B", "C", "D", "X"])

    truth = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "C", "D"),
        ],
    )
    prediction = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "C", "X"),
        ],
    )

    counts = pairwise_counts(truth, prediction)

    assert counts == PairwiseCounts(tp=1, fp=1, fn=1)


def test_pairwise_counts_empty_truth_and_prediction() -> None:
    universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(universe, [])
    prediction = RecordPairSet(universe, [])

    counts = pairwise_counts(truth, prediction)

    assert counts == PairwiseCounts(tp=0, fp=0, fn=0)


def test_pairwise_counts_empty_prediction() -> None:
    universe = RecordUniverse(["A", "B", "C"])

    truth = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "A", "C"),
        ],
    )
    prediction = RecordPairSet(universe, [])

    counts = pairwise_counts(truth, prediction)

    assert counts == PairwiseCounts(tp=0, fp=0, fn=2)


def test_pairwise_counts_empty_truth() -> None:
    universe = RecordUniverse(["A", "B", "C"])

    truth = RecordPairSet(universe, [])
    prediction = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "A", "C"),
        ],
    )

    counts = pairwise_counts(truth, prediction)

    assert counts == PairwiseCounts(tp=0, fp=2, fn=0)


def test_pairwise_counts_rejects_different_universes() -> None:
    first_universe = RecordUniverse(["A", "B"])
    second_universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(
        first_universe,
        [RecordPair(first_universe, "A", "B")],
    )
    prediction = RecordPairSet(
        second_universe,
        [RecordPair(second_universe, "A", "B")],
    )

    with pytest.raises(ValueError):
        pairwise_counts(truth, prediction)


def test_pairwise_counts_is_orientation_invariant() -> None:
    universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )
    prediction = RecordPairSet(
        universe,
        [RecordPair(universe, "B", "A")],
    )

    counts = pairwise_counts(truth, prediction)

    assert counts == PairwiseCounts(tp=1, fp=0, fn=0)


def test_pairwise_counts_does_not_modify_inputs() -> None:
    universe = RecordUniverse(["A", "B", "C"])

    truth = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )
    prediction = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "C")],
    )

    truth_before = tuple(pair.records for pair in truth)
    prediction_before = tuple(pair.records for pair in prediction)

    pairwise_counts(truth, prediction)

    assert tuple(pair.records for pair in truth) == truth_before
    assert tuple(pair.records for pair in prediction) == prediction_before


@given(
    st.sets(
        st.tuples(
            st.integers(min_value=0, max_value=5),
            st.integers(min_value=0, max_value=5),
        )
    ),
    st.sets(
        st.tuples(
            st.integers(min_value=0, max_value=5),
            st.integers(min_value=0, max_value=5),
        )
    ),
)
def test_pairwise_counts_truth_partition_invariant(
    truth_indices: set[tuple[int, int]],
    prediction_indices: set[tuple[int, int]],
) -> None:
    universe = RecordUniverse(list(range(6)))

    truth_pairs = [
        RecordPair(universe, first, second)
        for first, second in truth_indices
        if first != second
    ]
    prediction_pairs = [
        RecordPair(universe, first, second)
        for first, second in prediction_indices
        if first != second
    ]

    truth = RecordPairSet(universe, truth_pairs)
    prediction = RecordPairSet(universe, prediction_pairs)

    counts = pairwise_counts(truth, prediction)

    assert counts.tp + counts.fn == len(truth)


@given(
    st.sets(
        st.tuples(
            st.integers(min_value=0, max_value=5),
            st.integers(min_value=0, max_value=5),
        )
    ),
    st.sets(
        st.tuples(
            st.integers(min_value=0, max_value=5),
            st.integers(min_value=0, max_value=5),
        )
    ),
)
def test_pairwise_counts_prediction_partition_invariant(
    truth_indices: set[tuple[int, int]],
    prediction_indices: set[tuple[int, int]],
) -> None:
    universe = RecordUniverse(list(range(6)))

    truth_pairs = [
        RecordPair(universe, first, second)
        for first, second in truth_indices
        if first != second
    ]
    prediction_pairs = [
        RecordPair(universe, first, second)
        for first, second in prediction_indices
        if first != second
    ]

    truth = RecordPairSet(universe, truth_pairs)
    prediction = RecordPairSet(universe, prediction_pairs)

    counts = pairwise_counts(truth, prediction)

    assert counts.tp + counts.fp == len(prediction)


def test_false_link_rate_perfect_prediction() -> None:
    universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )
    prediction = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )

    assert false_link_rate(truth, prediction) == 0.0


def test_missing_match_rate_perfect_prediction() -> None:
    universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )
    prediction = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )

    assert missing_match_rate(truth, prediction) == 0.0


def test_false_link_rate_partial_prediction() -> None:
    universe = RecordUniverse(["A", "B", "C", "D", "X"])

    truth = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "C", "D"),
        ],
    )
    prediction = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "C", "X"),
        ],
    )

    assert false_link_rate(truth, prediction) == 0.5


def test_missing_match_rate_partial_prediction() -> None:
    universe = RecordUniverse(["A", "B", "C", "D", "X"])

    truth = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "C", "D"),
        ],
    )
    prediction = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "C", "X"),
        ],
    )

    assert missing_match_rate(truth, prediction) == 0.5


def test_false_link_rate_all_predicted_links_are_false() -> None:
    universe = RecordUniverse(["A", "B", "C"])

    truth = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )
    prediction = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "C")],
    )

    assert false_link_rate(truth, prediction) == 1.0


def test_missing_match_rate_all_true_links_are_missed() -> None:
    universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )
    prediction = RecordPairSet(universe, [])

    assert missing_match_rate(truth, prediction) == 1.0


def test_false_link_rate_is_nan_when_no_links_are_predicted() -> None:
    universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )
    prediction = RecordPairSet(universe, [])

    assert math.isnan(false_link_rate(truth, prediction))


def test_missing_match_rate_is_nan_when_truth_has_no_links() -> None:
    universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(universe, [])
    prediction = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )

    assert math.isnan(missing_match_rate(truth, prediction))


def test_flr_and_mmr_are_nan_when_both_pair_sets_are_empty() -> None:
    universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(universe, [])
    prediction = RecordPairSet(universe, [])

    assert math.isnan(false_link_rate(truth, prediction))
    assert math.isnan(missing_match_rate(truth, prediction))


def test_flr_and_mmr_are_orientation_invariant() -> None:
    universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )
    prediction = RecordPairSet(
        universe,
        [RecordPair(universe, "B", "A")],
    )

    assert false_link_rate(truth, prediction) == 0.0
    assert missing_match_rate(truth, prediction) == 0.0


@given(
    st.sets(
        st.tuples(
            st.integers(min_value=0, max_value=5),
            st.integers(min_value=0, max_value=5),
        )
    ),
    st.sets(
        st.tuples(
            st.integers(min_value=0, max_value=5),
            st.integers(min_value=0, max_value=5),
        )
    ),
)
def test_false_link_rate_is_bounded_when_defined(
    truth_indices: set[tuple[int, int]],
    prediction_indices: set[tuple[int, int]],
) -> None:
    universe = RecordUniverse(list(range(6)))

    truth = RecordPairSet(
        universe,
        [
            RecordPair(universe, first, second)
            for first, second in truth_indices
            if first != second
        ],
    )
    prediction = RecordPairSet(
        universe,
        [
            RecordPair(universe, first, second)
            for first, second in prediction_indices
            if first != second
        ],
    )

    value = false_link_rate(truth, prediction)

    if not math.isnan(value):
        assert 0.0 <= value <= 1.0


@given(
    st.sets(
        st.tuples(
            st.integers(min_value=0, max_value=5),
            st.integers(min_value=0, max_value=5),
        )
    ),
    st.sets(
        st.tuples(
            st.integers(min_value=0, max_value=5),
            st.integers(min_value=0, max_value=5),
        )
    ),
)
def test_missing_match_rate_is_bounded_when_defined(
    truth_indices: set[tuple[int, int]],
    prediction_indices: set[tuple[int, int]],
) -> None:
    universe = RecordUniverse(list(range(6)))

    truth = RecordPairSet(
        universe,
        [
            RecordPair(universe, first, second)
            for first, second in truth_indices
            if first != second
        ],
    )
    prediction = RecordPairSet(
        universe,
        [
            RecordPair(universe, first, second)
            for first, second in prediction_indices
            if first != second
        ],
    )

    value = missing_match_rate(truth, prediction)

    if not math.isnan(value):
        assert 0.0 <= value <= 1.0


def test_flr_and_mmr_reject_different_universes() -> None:
    first_universe = RecordUniverse(["A", "B"])
    second_universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(
        first_universe,
        [RecordPair(first_universe, "A", "B")],
    )
    prediction = RecordPairSet(
        second_universe,
        [RecordPair(second_universe, "A", "B")],
    )

    with pytest.raises(ValueError):
        false_link_rate(truth, prediction)

    with pytest.raises(ValueError):
        missing_match_rate(truth, prediction)


def test_flr_and_mmr_ignore_duplicate_logical_pairs() -> None:
    universe = RecordUniverse(["A", "B", "C"])

    truth = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "A", "B"),
        ],
    )
    prediction = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "B", "A"),
            RecordPair(universe, "A", "C"),
            RecordPair(universe, "A", "C"),
        ],
    )

    assert false_link_rate(truth, prediction) == 0.5
    assert missing_match_rate(truth, prediction) == 0.0


def test_flr_and_mmr_do_not_modify_inputs() -> None:
    universe = RecordUniverse(["A", "B", "C"])

    truth = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )
    prediction = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "C")],
    )

    truth_before = tuple(pair.records for pair in truth)
    prediction_before = tuple(pair.records for pair in prediction)

    false_link_rate(truth, prediction)
    missing_match_rate(truth, prediction)

    assert tuple(pair.records for pair in truth) == truth_before
    assert tuple(pair.records for pair in prediction) == prediction_before


def test_pairwise_precision_perfect_prediction() -> None:
    universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )
    prediction = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )

    assert pairwise_precision(truth, prediction) == 1.0


def test_pairwise_recall_perfect_prediction() -> None:
    universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )
    prediction = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )

    assert pairwise_recall(truth, prediction) == 1.0


def test_pairwise_f1_perfect_prediction() -> None:
    universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )
    prediction = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )

    assert pairwise_f1(truth, prediction) == 1.0


def test_pairwise_metrics_partial_prediction() -> None:
    universe = RecordUniverse(["A", "B", "C", "D", "X"])

    truth = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "C", "D"),
        ],
    )
    prediction = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "C", "X"),
        ],
    )

    assert pairwise_precision(truth, prediction) == 0.5
    assert pairwise_recall(truth, prediction) == 0.5
    assert pairwise_f1(truth, prediction) == 0.5


def test_pairwise_precision_is_nan_when_no_links_are_predicted() -> None:
    universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )
    prediction = RecordPairSet(universe, [])

    assert math.isnan(pairwise_precision(truth, prediction))


def test_pairwise_recall_is_nan_when_truth_has_no_links() -> None:
    universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(universe, [])
    prediction = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )

    assert math.isnan(pairwise_recall(truth, prediction))


def test_pairwise_f1_is_nan_when_truth_and_prediction_are_empty() -> None:
    universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(universe, [])
    prediction = RecordPairSet(universe, [])

    assert math.isnan(pairwise_f1(truth, prediction))


def test_pairwise_f1_is_zero_when_all_true_links_are_missed() -> None:
    universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )
    prediction = RecordPairSet(universe, [])

    assert pairwise_f1(truth, prediction) == 0.0


def test_pairwise_f1_is_zero_when_all_predicted_links_are_false() -> None:
    universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(universe, [])
    prediction = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )

    assert pairwise_f1(truth, prediction) == 0.0


def test_pairwise_precision_is_one_minus_false_link_rate() -> None:
    universe = RecordUniverse(["A", "B", "C"])

    truth = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )
    prediction = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "A", "C"),
        ],
    )

    assert pairwise_precision(truth, prediction) == 1.0 - false_link_rate(
        truth,
        prediction,
    )


def test_pairwise_recall_is_one_minus_missing_match_rate() -> None:
    universe = RecordUniverse(["A", "B", "C"])

    truth = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "A", "C"),
        ],
    )
    prediction = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )

    assert pairwise_recall(truth, prediction) == 1.0 - missing_match_rate(
        truth,
        prediction,
    )


@given(
    st.sets(
        st.tuples(
            st.integers(min_value=0, max_value=5),
            st.integers(min_value=0, max_value=5),
        )
    ),
    st.sets(
        st.tuples(
            st.integers(min_value=0, max_value=5),
            st.integers(min_value=0, max_value=5),
        )
    ),
)
def test_pairwise_metrics_are_bounded_when_defined(
    truth_indices: set[tuple[int, int]],
    prediction_indices: set[tuple[int, int]],
) -> None:
    universe = RecordUniverse(list(range(6)))

    truth = RecordPairSet(
        universe,
        [
            RecordPair(universe, first, second)
            for first, second in truth_indices
            if first != second
        ],
    )
    prediction = RecordPairSet(
        universe,
        [
            RecordPair(universe, first, second)
            for first, second in prediction_indices
            if first != second
        ],
    )

    values = (
        pairwise_precision(truth, prediction),
        pairwise_recall(truth, prediction),
        pairwise_f1(truth, prediction),
    )

    for value in values:
        if not math.isnan(value):
            assert 0.0 <= value <= 1.0


@given(
    st.sets(
        st.tuples(
            st.integers(min_value=0, max_value=5),
            st.integers(min_value=0, max_value=5),
        )
    ),
    st.sets(
        st.tuples(
            st.integers(min_value=0, max_value=5),
            st.integers(min_value=0, max_value=5),
        )
    ),
)
def test_pairwise_precision_and_recall_match_linkage_error_complements(
    truth_indices: set[tuple[int, int]],
    prediction_indices: set[tuple[int, int]],
) -> None:
    universe = RecordUniverse(list(range(6)))

    truth = RecordPairSet(
        universe,
        [
            RecordPair(universe, first, second)
            for first, second in truth_indices
            if first != second
        ],
    )
    prediction = RecordPairSet(
        universe,
        [
            RecordPair(universe, first, second)
            for first, second in prediction_indices
            if first != second
        ],
    )

    precision = pairwise_precision(truth, prediction)
    recall = pairwise_recall(truth, prediction)
    flr = false_link_rate(truth, prediction)
    mmr = missing_match_rate(truth, prediction)

    if not math.isnan(precision):
        assert math.isclose(precision, 1.0 - flr)

    if not math.isnan(recall):
        assert math.isclose(recall, 1.0 - mmr)


def test_pairwise_precision_recall_f1_reject_different_universes() -> None:
    first_universe = RecordUniverse(["A", "B"])
    second_universe = RecordUniverse(["A", "B"])

    truth = RecordPairSet(
        first_universe,
        [RecordPair(first_universe, "A", "B")],
    )
    prediction = RecordPairSet(
        second_universe,
        [RecordPair(second_universe, "A", "B")],
    )

    with pytest.raises(ValueError):
        pairwise_precision(truth, prediction)

    with pytest.raises(ValueError):
        pairwise_recall(truth, prediction)

    with pytest.raises(ValueError):
        pairwise_f1(truth, prediction)


def test_pairwise_precision_recall_f1_ignore_orientation_and_duplicates() -> None:
    universe = RecordUniverse(["A", "B", "C"])

    truth = RecordPairSet(
        universe,
        [
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "B", "A"),
        ],
    )
    prediction = RecordPairSet(
        universe,
        [
            RecordPair(universe, "B", "A"),
            RecordPair(universe, "A", "B"),
            RecordPair(universe, "A", "C"),
            RecordPair(universe, "A", "C"),
        ],
    )

    assert pairwise_precision(truth, prediction) == 0.5
    assert pairwise_recall(truth, prediction) == 1.0

    expected_f1 = 2.0 / 3.0
    assert math.isclose(pairwise_f1(truth, prediction), expected_f1)


def test_pairwise_precision_recall_f1_do_not_modify_inputs() -> None:
    universe = RecordUniverse(["A", "B", "C"])

    truth = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "B")],
    )
    prediction = RecordPairSet(
        universe,
        [RecordPair(universe, "A", "C")],
    )

    truth_before = tuple(pair.records for pair in truth)
    prediction_before = tuple(pair.records for pair in prediction)

    pairwise_precision(truth, prediction)
    pairwise_recall(truth, prediction)
    pairwise_f1(truth, prediction)

    assert tuple(pair.records for pair in truth) == truth_before
    assert tuple(pair.records for pair in prediction) == prediction_before
