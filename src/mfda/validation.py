"""
Validation module.

Defines data models for schema validation and validation results.

Schema shape:
{
    "id":   {"required": True, "unique": True, "type": "integer"},
    "age":  {"type": "number", "min": 0, "max": 120},
    "name": {"required": True, "type": "string"},
}
"""

from dataclasses import dataclass, field

Schema = dict[str, dict[str, object]]


@dataclass
class ValidationIssue:
    code: str
    column: str | None
    count: int
    examples: list[int]


@dataclass
class ValidationReport:
    row_count: int
    column_count: int
    issues: list[ValidationIssue] = field(default_factory=list)


def infer_schema(records: list[dict[str, object]], sample: int | None = 50) -> Schema:
    raise NotImplementedError


def validate(records: list[dict[str, object]], schema: Schema) -> ValidationReport:
    row_count = len(records)
    column_count = len({k for r in records for k in r})
    issues: list[ValidationIssue] = []

    for col, rules in schema.items():
        # Required
        if rules.get("required"):
            bad_rows = [i for i, r in enumerate(records) if col not in r or r[col] is None]
            if bad_rows:
                issues.append(ValidationIssue("missing_required", col, len(bad_rows), bad_rows[:5]))

        # Unique
        if rules.get("unique"):
            seen: dict[object, int] = {}
            dupes = []
            for i, r in enumerate(records):
                val = r.get(col)
                # skip NULL
                if val is None:
                    continue
                # record dupes
                if val in seen:
                    dupes.append(i)
                else:
                    seen[val] = i
            if dupes:
                issues.append(ValidationIssue("duplicate", col, len(dupes), dupes[:5]))

        # Range
        if "min" in rules or "max" in rules:
            lows: list[int] = []
            highs: list[int] = []
            min_val = rules.get("min")
            max_val = rules.get("max")

            for i, r in enumerate(records):
                val = r.get(col)
                if not isinstance(val, (int, float)):  # noqa: UP038
                    continue
                if isinstance(min_val, (int, float)) and val < min_val:  # noqa: UP038
                    lows.append(i)
                if isinstance(max_val, (int, float)) and val > max_val:  # noqa: UP038
                    highs.append(i)
            if lows:
                issues.append(ValidationIssue("out_of_range", col, len(lows), lows[:5]))
            if highs:
                issues.append(ValidationIssue("out_of_range", col, len(highs), highs[:5]))

    return ValidationReport(row_count, column_count, issues)
