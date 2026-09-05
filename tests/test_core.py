import pytest

from linkeval.core import RecordUniverse


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
