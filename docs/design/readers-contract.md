# Readers Contract (Design)

## Detection & dispatch
- The dispatcher selects a reader using:
  - file **extension** (`.csv`, `.json`, `.jsonl`, `.xlsx`, `.parquet`, `.db`, `.sqlite`, `.html`, `.gz`, `.zip`)
  - **signature/magic bytes** (gzip/zip/parquet) and/or an explicit `--format`.
- If compressed (`.gz`/`.zip`), unwrap first, then re-detect inner type.
- `-` denotes **stdin** where supported (e.g., `zcat data.csv.gz | mfda read -`).
- Dispatcher resolves compression first (.gz/.zip), then inner format by name/signature; --format or hint overrides both

## Reader responsibilities (each plugin must)
- Accept a **source** (path/URI/stdin) and documented **options**.
- Return a **Table** that satisfies all invariants (see core model).
- Never print to stdout; log via the project logger and respect verbosity.
- Raise:
  - **FileFormatError** for parse issues or mismatched content,
  - **ConfigurationError** for invalid/contradictory options.

## Options (common + per-reader)
**Common**: `encoding`, `compression`, `limit`, `infer_dtypes: bool`.

- **CSV/TSV**: `delimiter`, `quotechar`, `header_row`, `decimal`, `thousands`.
- **JSON/JSONL**: `lines: bool` (JSONL mode), *(future)* `pointer/xpath`.
- **XLSX**: `sheet` (name|index), `header_row`.
- **Parquet**: *(optional)* `columns`.
- **SQLite**: `table` **or** `query` (mutually exclusive).
- **HTML**: `table_index`, *(future)* CSS selector.

## Minimal guarantees
- **Column names**: document policy (preserve vs. slugify); apply consistently.
- **Missing values**: normalize to a single sentinel (**null**) in Table.
- **Dtype inference**: document policy; e.g., `int → float → string` fallback with `errors="coerce"` behavior spelled out.
