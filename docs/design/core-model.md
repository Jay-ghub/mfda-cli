# Core Model — Table & Schema (Design Contract)

## Table abstraction (what it is)
- Rectangular data with **unique** string column names; row count ≥ 0.
- Missing values are allowed in any column and represented uniformly as **null** in the Table abstraction.
- Stores **logical dtypes** (not Python types): `int`, `float`, `bool`, `string`, `categorical`, `datetime`, `date`, `time`.
- Carries **metadata**: `source` (path/URI), `format`, `encoding`, `dialect` (CSV/TSV details), and `created_at`.

### Shape
- `shape` is a tuple: `(n_rows, n_cols)`.
- Invariant: each row has exactly `n_cols` fields.

## Invariants (must always hold)
- `len(columns) == n_cols` and **columns are unique** strings.
- `types` maps **every** column name to **one** logical dtype.
- `shape == (n_rows, n_cols)` and is consistent with stored rows.

## Core operations (to implement later; API only)
- `select(columns)` → new Table with a subset of columns.
- `cast(column, to_dtype, errors="raise|coerce|ignore")` → same rows, new dtype.
- `head(n)` → preview rows (no side effects).
- `as_records()` → read-only list of dicts for printing/validation.
- `memory_usage()` → approximate bytes (optional).
- `to_pandas()` → optional integration helper; **do not depend on it internally**.

## Logical dtype notes
- `categorical` may track a set of known categories; “other/rare” bucketing is allowed later at the analysis layer.
- `datetime` policy: **store and log in UTC using ISO-8601**. Convert to/from local time only at I/O boundaries. Naive inputs are interpreted as UTC unless the user specifies otherwise (documented at the reader level).

## Schema object (separate from Table)
A **Schema** describes what you **expect**:
- Mapping: column → expected logical dtype and constraints.
- Constraints (optional):
  - `required: bool`
  - `unique: bool | list[str]` (composite keys)
  - numeric ranges (`min`, `max`)
  - categorical `allowed_values: set[str]`
  - string `regex: str`
  - `nullable: bool`
- **Keep Schema separate from Table**: Table is what you read; Schema is what you enforce during validation.
