"""
Core Model (design contract only; no implementation)

This module describes the internal 'Table' abstraction and the separate 'Schema'.

Table (see docs/design/core-model.md):
- Rectangular, unique string column names; missing values allowed as a single null sentinel.
- Logical dtypes: int, float, bool, string, categorical, datetime, date, time.
- Metadata: source, format, encoding, dialect, created_at.
- Shape: (n_rows, n_cols), consistent across rows.

Schema (see docs/design/core-model.md):
- Expected logical dtype per column plus optional constraints:
  required/unique keys, numeric ranges, categorical allowed_values, string regex, nullable.
- Enforced by validation step; separate from the Table itself.

No classes or functions are defined here yet; this file exists so linters, docs, and
tests can reference the intended contracts without pulling in implementation.
"""
