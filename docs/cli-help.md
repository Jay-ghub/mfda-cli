# mfda — Multi-format Data Analysis
**Version:** 1.0.0

Read, validate, analyze, and visualize tabular data from multiple file formats.

---

## Global options
- `-h, --help` — Show help and exit
- `--version` — Show version and exit

---

## Subcommands

### read — Preview records
``
```bash
mfda read <path> [-f FORMAT] [-n LIMIT] [--lines] [--sheet SHEET]

### analyze — Summarize rows, columns, and value distributions
``bash
mfda analyze <path> [-f FORMAT] [-k TOP_K] [--lines] [--sheet SHEET]

### viz (alias: visualize) — Generate basic charts
```bash
mfda viz <path> [-f FORMAT] [-k TOP_K] [--lines] [--sheet SHEET]
          [--hist COL | --bar COL] --out FILE
mfda analyze <path> [-f FORMAT] [-k TOP_K] [--lines] [--sheet SHEET]

### validate — Check records against a schema
```bash
mfda validate <path> [-f FORMAT] [--lines] [--sheet SHEET] [--schema FILE.json]

### report — Generate Markdown report with analysis, validation, and charts
```bash
mfda report <path> --out REPORT.md
           [--hist COL --hist-out FILE]
           [--bar COL --bar-out FILE]
           [-k TOP_K] [-f FORMAT] [--lines] [--sheet SHEET] [--schema FILE.json]
´´

---

## Exit codes

0 — success
1 — unexpected runtime error
2 — user error (bad args, unknown format, etc.)

---

##Examples
# Preview 5 rows from CSV
mfda read data/customers.csv

# Analyze JSON Lines file with explicit --lines
mfda analyze data/events.json --lines

# Generate histogram
mfda viz data/customers.csv --hist age --out age.png

# Validate against a schema
mfda validate data/customers.csv --schema schema.json

# Full report with charts
mfda report data/customers.csv --out report.md --hist age --hist-out age.png
