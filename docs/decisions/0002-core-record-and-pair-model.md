# ADR 0002: Core Record and Pair Model

## Status

Accepted

## Context

`linkeval` requires a clear representation of the records and record pairs over which entity-resolution evaluation is performed.

The statistical meaning of later evaluation metrics depends on this representation. In particular, the library must make explicit:

- which records belong to the evaluation universe;
- which record pairs are valid;
- whether pair orientation matters;
- how duplicate representations of the same logical pair are handled;
- which information belongs to the evaluation data model and which belongs to an external modelling workflow.

For the initial `linkeval` implementation, the primary setting is deduplication within a single collection of records.

Let the record universe be

\[
R = \{r_1, r_2, \ldots, r_n\}.
\]

A possible relationship is then formed between two distinct records belonging to \(R\).

For deduplication, the relationship is unordered. Therefore,

\[
(r_i,r_j)
\]

and

\[
(r_j,r_i)
\]

represent the same logical pair.

The library must also support arbitrary user-provided record identifiers. Such identifiers may be strings, integers, tuples, or other hashable objects, and different identifiers are not necessarily mutually orderable in Python.

Directly canonicalising pairs with an operation such as

```python
tuple(sorted((a, b)))
```

would therefore impose an unnecessary ordering requirement on public record identifiers.

The user's ER Transformer research also provides an important future use case. That evaluation setting is naturally bipartite, with records from file \(A\) linked to records from file \(B\), and a source record may have multiple valid target partners.

Those semantics are different from single-universe unordered deduplication and should not be silently conflated with it.

## Decision

`linkeval` v0.1 will use an explicit single-record universe as the primary data model for deduplication.

The universe will:

1. contain a unique collection of public record identifiers;
2. reject duplicate record identifiers at construction;
3. assign every record a deterministic internal position according to the explicit order in which records are supplied;
4. preserve the original public record identifiers unchanged.

Universe construction will preserve the caller-provided record order. It will not derive an order by sorting or hashing public record identifiers. Inputs that do not provide an explicit record order, such as sets, are therefore not suitable as direct universe inputs.

A valid pair will:

1. contain exactly two records;
2. require both records to belong to the associated universe;
3. reject self-pairs;
4. represent an unordered relationship.

Pair canonicalisation will use the universe's internal positions rather than directly comparing or sorting public record identifiers.

For example, if the universe establishes:

```text
record ID    internal position
A17          0
B92          1
X03          2
```

then a user-provided pair

```text
(B92, A17)
```

can be represented canonically as

```text
(A17, B92)
```

because the internal positions are 1 and 0.

This does not require `A17` and `B92` themselves to support ordering.

Duplicate logical pairs will therefore collapse deterministically:

```text
(A17, B92)
(B92, A17)
```

represent one relationship rather than two.

Training/test membership will not be part of the fundamental record or pair representation.

Training splits, test splits, blocking assignments, model scores, and similar workflow-specific information belong to higher-level modelling or evaluation inputs rather than to the identity of a record pair itself.

## Statistical Interpretation

The explicit universe defines the population of records to which a deduplication evaluation refers.

Pair validity is therefore not only a software-validation concern. It is part of the statistical definition of the evaluation problem.

Rejecting records outside the universe prevents accidental evaluation of relationships that are not part of the declared population.

Rejecting self-pairs reflects the fact that deduplication concerns relationships between distinct records.

Treating pair orientation as irrelevant reflects the symmetry of the deduplication relation:

\[
\{r_i,r_j\} = \{r_j,r_i\}.
\]

These assumptions apply to the single-universe deduplication model introduced here. They must not automatically be imposed on future bipartite linkage models.

## Consequences

### Positive consequences

- The evaluation universe is explicit rather than inferred from observed pairs.
- Invalid pairs can be detected early.
- Self-pairs cannot silently enter later metric calculations.
- Pair equality has a clear deduplication interpretation.
- Arbitrary hashable record identifiers can be supported without requiring them to be mutually orderable.
- Duplicate logical pairs can be handled deterministically.
- Training and test workflow information remains separated from the statistical identity of a pair.
- The model provides a clear foundation for later pair sets, cluster representations, and pairwise evaluation metrics.

### Trade-offs

- Every pair must be interpreted relative to a universe.
- The library must maintain an internal mapping from public record identifiers to deterministic positions.
- The initial representation is deliberately specialised to single-universe deduplication rather than attempting to provide one universal pair abstraction for every entity-resolution setting.

## Deferred Decisions

This ADR does not define the implementation of:

- bipartite record universes;
- directed source-to-target linkage;
- source-record evaluation with multiple valid partners;
- FLR or MMR;
- cluster representations;
- blocking;
- training/test splitting;
- model scores or thresholds.

Future bipartite support may introduce an abstraction such as:

```python
BipartiteUniverse(left=..., right=...)
```

where valid pairs cross from the left universe to the right universe.

Such a representation would have different validity and orientation semantics from the unordered pair model defined here.

The two evaluation settings should remain distinguishable in the public API.

## Alternatives Considered

### Infer the universe from observed pairs

Rejected because records with no observed or predicted pair would disappear from the representation.

This can obscure the statistical denominator and make later evaluation depend unintentionally on the submitted pairs.

### Store raw two-element tuples only

Rejected because tuples alone do not enforce universe membership, self-pair validation, or unordered-pair semantics.

### Canonicalise by sorting record identifiers

Rejected because arbitrary valid record identifiers are not guaranteed to be mutually orderable.

### Encode training/test membership in the pair object

Rejected because training/test status describes how observations are used in a modelling workflow, not the identity of the relationship between two records.

The complete evaluation truth may also differ from the labels retained for model training.

### Use the same pair abstraction for deduplication and bipartite linkage immediately

Deferred because the statistical semantics differ.

A premature universal abstraction risks hiding important distinctions such as direction, source-record denominators, and multiple valid target partners.

## Future Work

Later ADRs may define:

- a pair-set abstraction;
- bipartite universes;
- source-record linkage truth;
- multiple-valid-partner evaluation;
- cluster representations and conversions;
- FLR/MMR denominator conventions.
