# mfda

Multi-Format Data Analysis (mfda) is a lightweight command-line tool for exploring, validating, and reporting on datasets across multiple formats.

---

## Quickstart

Preview a CSV:

```bash
mfda read tests/fixtures/tiny_customers.csv --limit 2
```

Summarize a dataset:

```bash
mfda analyze tests/fixtures/tiny_customers.csv
```

Validate against a schema:

```bash
mfda validate tests/fixtures/tiny_customers.csv --schema tests/fixtures/customer_schema.json
```

Visualize a column:

```bash
mfda viz tests/fixtures/tiny_customers.csv --hist age --out age_hist.png
```

Generate a Markdown report:

```bash
mfda report tests/fixtures/tiny_customers.csv --out report.md --hist age --hist-out age.png
```

---

## Supported formats

| Format   | Extensions             | Notes                               |
|----------|------------------------|-------------------------------------|
| CSV      | `.csv`                 | configurable header row, limit rows |
| JSON     | `.json`, `.jsonl`      | JSON arrays or JSON Lines (`--lines`) |
| Excel    | `.xlsx`                | `--sheet` for sheet name/index      |
| HTML     | `.html`, `.htm`        | parses `` elements           |
| SQLite   | `.db`, `.sqlite`       | table or custom query               |
| Parquet  | `.parquet`             | via `pyarrow`                       |

---

## Troubleshooting

**“unknown or unsupported format”**
→ Check the file extension or pass `--format` explicitly.

**“Provide either table or query, not both”**
→ For SQLite, you must choose only one mode.

**“No numeric data in column …”**
→ You tried to plot a histogram on a non-numeric column.

**“No schema provided, skipping rule checks.”**
→ `validate` or `report` ran without a schema; either pass `--schema` or ignore if you don’t need validation.

**“Error: could not parse JSON schema”**
→ Your schema file isn’t valid JSON; check with `jq . schema.json`.

---

## CLI Reference

Run:

```bash
mfda --help
mfda read --help
mfda analyze --help
mfda validate --help
mfda viz --help
mfda report --help
```

See [docs/cli-help.md](docs/cli-help.md) for the full output.

---

## Development

- Python 3.10+ recommended
- Install dev tools:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pre-commit install
```

- Run checks:

```bash
ruff check .
mypy src
pytest
```

---
######################TBD###########################
## Changelog

See [CHANGELOG.md]

---

## Contributing

See [CONTRIBUTING.md]
#####################TBD############################
---

## License

Apache-2.0.
