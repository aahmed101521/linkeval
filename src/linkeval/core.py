"""Core data structures for linkeval."""

from collections.abc import Hashable, Iterable, Set


class RecordUniverse:
    """An explicit ordered universe of unique record identifiers."""

    def __init__(self, records: Iterable[Hashable]) -> None:
        """Create a record universe from caller-supplied record identifiers."""
        if isinstance(records, Set):
            raise TypeError("record universe requires an explicitly ordered iterable")

        self._records = tuple(records)
        self._positions: dict[Hashable, int] = {}

        for position, record in enumerate(self._records):
            if record in self._positions:
                raise ValueError("record identifiers must be unique")

            self._positions[record] = position

    @property
    def records(self) -> tuple[Hashable, ...]:
        """Return record identifiers in their original universe order."""
        return self._records

    def position(self, record: Hashable) -> int:
        """Return the internal position assigned to a record."""
        return self._positions[record]

    def __contains__(self, record: object) -> bool:
        """Return whether a record belongs to the universe."""
        return record in self._positions


class RecordPair:
    """An unordered pair of distinct records from a record universe."""

    def __init__(
        self,
        universe: RecordUniverse,
        first: Hashable,
        second: Hashable,
    ) -> None:
        """Create and canonicalise a pair within a record universe."""
        first_position = universe.position(first)
        second_position = universe.position(second)

        if first_position == second_position:
            raise ValueError("a record cannot be paired with itself")

        self._universe = universe

        if first_position < second_position:
            self._records = (first, second)
        else:
            self._records = (second, first)

    @property
    def records(self) -> tuple[Hashable, Hashable]:
        """Return the pair in canonical universe order."""
        return self._records

    def __eq__(self, other: object) -> bool:
        """Return whether two pairs represent the same relationship."""
        if not isinstance(other, RecordPair):
            return NotImplemented

        return self._universe is other._universe and self._records == other._records

    def __hash__(self) -> int:
        """Return a hash consistent with unordered-pair equality."""
        return hash((self._universe, self._records))
