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
