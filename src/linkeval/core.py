"""Core data structures for linkeval."""

from collections.abc import Hashable, Iterable, Iterator, Set
from itertools import combinations


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

    @property
    def universe(self) -> RecordUniverse:
        """Return the universe to which the pair belongs."""
        return self._universe

    def __eq__(self, other: object) -> bool:
        """Return whether two pairs represent the same relationship."""
        if not isinstance(other, RecordPair):
            return NotImplemented

        return self._universe is other._universe and self._records == other._records

    def __hash__(self) -> int:
        """Return a hash consistent with unordered-pair equality."""
        return hash((self._universe, self._records))


class RecordPairSet:
    """A validated deterministic collection of record pairs."""

    def __init__(
        self,
        universe: RecordUniverse,
        pairs: Iterable[RecordPair],
    ) -> None:
        """Create a pair set whose pairs all belong to one universe."""
        self._universe = universe
        unique_pairs: set[RecordPair] = set()

        for pair in pairs:
            if pair.universe is not universe:
                raise ValueError(
                    "all record pairs must belong to the pair set universe"
                )

            unique_pairs.add(pair)

        self._pairs = tuple(
            sorted(
                unique_pairs,
                key=lambda pair: (
                    universe.position(pair.records[0]),
                    universe.position(pair.records[1]),
                ),
            )
        )
        self._pair_lookup = frozenset(self._pairs)

    @property
    def universe(self) -> RecordUniverse:
        """Return the record universe associated with this pair set."""
        return self._universe

    def __len__(self) -> int:
        """Return the number of unique logical pairs."""
        return len(self._pairs)

    def __contains__(self, pair: object) -> bool:
        """Return whether a record pair belongs to the pair set."""
        return pair in self._pair_lookup

    def __iter__(self) -> Iterator[RecordPair]:
        """Iterate over pairs in deterministic universe order."""
        return iter(self._pairs)


class RecordCluster:
    """A validated deterministic cluster of records."""

    def __init__(
        self,
        universe: RecordUniverse,
        records: Iterable[Hashable],
    ) -> None:
        """Create a record cluster within one explicit record universe."""
        self._universe = universe

        unique_records: set[Hashable] = set()

        for record in records:
            universe.position(record)
            unique_records.add(record)

        if not unique_records:
            raise ValueError("a record cluster must contain at least one record")

        self._records = tuple(
            sorted(
                unique_records,
                key=universe.position,
            )
        )
        self._record_lookup = frozenset(self._records)

    @property
    def records(self) -> tuple[Hashable, ...]:
        """Return cluster records in canonical universe order."""
        return self._records

    @property
    def universe(self) -> RecordUniverse:
        """Return the record universe associated with this cluster."""
        return self._universe

    def __len__(self) -> int:
        """Return the number of unique records in the cluster."""
        return len(self._records)

    def __contains__(self, record: object) -> bool:
        """Return whether a record belongs to the cluster."""
        return record in self._record_lookup

    def __iter__(self) -> Iterator[Hashable]:
        """Iterate over records in deterministic universe order."""
        return iter(self._records)

    def __eq__(self, other: object) -> bool:
        """Return whether two clusters represent the same logical cluster."""
        if not isinstance(other, RecordCluster):
            return NotImplemented

        return self._universe is other._universe and self._records == other._records

    def __hash__(self) -> int:
        """Return a hash consistent with cluster equality."""
        return hash((self._universe, self._records))


def cluster_to_pairs(cluster: RecordCluster) -> RecordPairSet:
    """Return the unordered record pairs implied by a record cluster."""
    universe = cluster.universe

    pairs = (
        RecordPair(universe, first, second)
        for first, second in combinations(cluster.records, 2)
    )

    return RecordPairSet(universe, pairs)


def pairs_to_clusters(pair_set: RecordPairSet) -> tuple[RecordCluster, ...]:
    """Return connected record clusters implied by a record pair set."""
    universe = pair_set.universe

    adjacency: dict[Hashable, set[Hashable]] = {}

    for pair in pair_set:
        first, second = pair.records

        adjacency.setdefault(first, set()).add(second)
        adjacency.setdefault(second, set()).add(first)

    visited: set[Hashable] = set()
    clusters: list[RecordCluster] = []

    records = sorted(adjacency, key=universe.position)

    for start in records:
        if start in visited:
            continue

        component: set[Hashable] = set()
        stack = [start]

        while stack:
            record = stack.pop()

            if record in visited:
                continue

            visited.add(record)
            component.add(record)

            for neighbor in adjacency[record]:
                if neighbor not in visited:
                    stack.append(neighbor)

        clusters.append(RecordCluster(universe, component))

    return tuple(clusters)
