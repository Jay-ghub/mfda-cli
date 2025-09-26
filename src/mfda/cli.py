"""
Command: mfda read <path> [--format FMT] [--limit N] [--lines] [--sheet SHEET]

Behavior: detect → choose reader → call read() with relevant options → print:

columns: [...]

shape: (row cols)

first N records (preview)

"""

import argparse
import json
import sys
from collections.abc import Sequence

from mfda import analysis, validation
from mfda.dispatch import choose_reader, detect_format
from mfda.errors import ConfigurationError, FileFormatError
from mfda.visualization import save_bar_counts, save_histogram


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mfda", description="Multi-format data analysis")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # read subparser
    read = sub.add_parser("read", help="Preview records from a dataset")
    read.add_argument("path")
    read.add_argument("-f", "--format")
    read.add_argument("-n", "--limit", type=int, default=5)
    read.add_argument("--lines", action="store_true")
    read.add_argument("--sheet")

    # analyze subparser
    analyze = sub.add_parser("analyze", help="Summarize rows, columns, and value distributions")
    analyze.add_argument("path")
    analyze.add_argument("-f", "--format")
    analyze.add_argument("-k", "--top-k", type=int, default=3)
    analyze.add_argument("--lines", action="store_true")
    analyze.add_argument("--sheet")

    # visualization subparser
    viz = sub.add_parser(
        "viz", help="Visualize a column as histogram or bar chart", aliases=["visualize"]
    )
    viz.add_argument("path")
    viz.add_argument("-f", "--format")
    viz.add_argument("-k", "--top-k", type=int, default=3)
    viz.add_argument("--lines", action="store_true")
    viz.add_argument("--sheet")
    viz.add_argument("--hist")
    viz.add_argument("--bar")
    viz.add_argument("--out", required=True)

    # validate subparser
    validate = sub.add_parser("validate", help="Check records against a schema")
    validate.add_argument("path")
    validate.add_argument("-f", "--format")
    validate.add_argument("--lines", action="store_true")
    validate.add_argument("--sheet")
    validate.add_argument("--schema")

    # report subparser
    report = sub.add_parser(
        "report", help="Generate a Markdown report with analysis, validation, and charts"
    )
    report.add_argument("path")
    report.add_argument("--out", required=True)
    report.add_argument("--hist")
    report.add_argument("--hist-out")
    report.add_argument("--bar")
    report.add_argument("--bar-out")
    report.add_argument("-k", "--top-k", type=int, default=3)
    report.add_argument("-f", "--format")
    report.add_argument("--lines", action="store_true")
    report.add_argument("--sheet")
    report.add_argument("--schema")

    parser.add_argument("--version", action="version", version="mfda 1.0.0")

    args = parser.parse_args(argv)

    # read
    if args.cmd == "read":
        # step 2: detect format
        if args.format:
            fmt = args.format.lower().lstrip(".")
        else:
            fmt = detect_format(args.path)  # detect_format in dispatch

        if fmt is None:
            print(f"Error: unknown or unsupported format for {args.path}")
            return 2
        # step 3: choose reader
        reader = choose_reader(fmt)
        if reader is None:
            print(f"No reader available for format: {fmt}", file=sys.stderr)
            return 2
        # step 4: build kwargs
        kwargs = {"limit": args.limit}

        if fmt in {"json", "jsonl"} and args.lines:
            kwargs["lines"] = True

        if fmt == "xlsx" and args.sheet:
            if args.sheet.isdigit():
                kwargs["sheet"] = int(args.sheet)
            else:
                kwargs["sheet"] = args.sheet
        # step 5: call reader, print & errors
        try:
            table = reader.read(args.path, **kwargs)
            print("columns:", table.columns)
            print("shape:", table.shape)

            records = table.as_records()
            preview = min(args.limit or 5, len(records))
            print("records:")
            for rec in records[:preview]:
                print(json.dumps(rec, ensure_ascii=False))

            return 0
        except (FileFormatError, ConfigurationError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            return 1

    # analyze
    elif args.cmd == "analyze":
        # step 2: detect format
        if args.format:
            fmt = args.format.lower().lstrip(".")
        else:
            fmt = detect_format(args.path)  # detect_format in dispatch

        if fmt is None:
            print(f"Error: unknown or unsupported format for {args.path}")
            return 2

        # step 3: choose reader & build kwargs
        reader = choose_reader(fmt)
        if reader is None:
            print(f"No reader available for format: {fmt}", file=sys.stderr)
            return 2

        kwargs = {"limit": None}

        if fmt in {"json", "jsonl"} and args.lines:
            kwargs["lines"] = True

        if fmt == "xlsx" and args.sheet:
            if args.sheet.isdigit():
                kwargs["sheet"] = int(args.sheet)
            else:
                kwargs["sheet"] = args.sheet

        # step 4: read records
        try:
            table = reader.read(args.path, **kwargs)
            records = table.as_records()
            # run analysis
            rep = analysis.analyze(records, top_k=args.top_k)
            # print
            print("rows: ", rep.rows)
            print("columns: ", rep.columns)
            print()
            print("numeric:")
            for ns in rep.numeric:
                print(
                    f" {ns.column}\t count={ns.count} nulls={ns.nulls}"
                    f" distinct={ns.distinct} min={ns.min} max={ns.max} mean={ns.mean}"
                )

            print("categorical:")
            for cs in rep.categorical:
                print(
                    f" {cs.column}\t count={cs.count} nulls={cs.nulls}"
                    f" distinct={cs.distinct}, top={cs.top}"
                )

            return 0

        except (FileFormatError, ConfigurationError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            return 1

    # visualize
    elif args.cmd == "viz":
        # hist and bar mutually exclusive
        if args.hist and args.bar:
            print("Error: choose either --hist or --bar (not both)")
            return 2
        if not args.hist and not args.bar:
            print("Error: must provide --hist or --bar")
            return 2
        # detect format
        if args.format:
            fmt = args.format.lower().lstrip(".")
        else:
            fmt = detect_format(args.path)

        if fmt is None:
            print(f"Error: unknown or unsupported format for {args.path}")
            return 2
        # step 3: choose reader
        reader = choose_reader(fmt)
        if reader is None:
            print(f"Error : no reader available for {fmt}")
            return 2
        # step 4: build kwargs
        kwargs = {"limit": None}
        if fmt in {"json", "jsonl"} and args.lines:
            kwargs["lines"] = True
        if fmt == "xlsx" and args.sheet:
            if args.sheet.isdigit():
                kwargs["sheet"] = int(args.sheet)
            else:
                kwargs["sheet"] = args.sheet
        # step 5: read records
        try:
            table = reader.read(args.path, **kwargs)
            records = table.as_records()

            # step 6: visualization
            if args.hist:
                save_histogram(records, column=args.hist, out_path=args.out)
                print(f"Wrote histogram to {args.out}")
            elif args.bar:
                save_bar_counts(records, column=args.bar, out_path=args.out, top_k=args.top_k)
                print(f"Wrote bar chart to {args.out}")

            return 0
        except (FileFormatError, ConfigurationError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            return 1

    # validation
    elif args.cmd == "validate":
        # 1: detect format
        if args.format:
            fmt = args.format.lower().lstrip(".")
        else:
            fmt = detect_format(args.path)

        if fmt is None:
            print(f"Error: unknown or unsupported format for {args.path}")
            return 2
        # 2: reader + kwargs
        reader = choose_reader(fmt)
        if reader is None:
            print(f"Error: no reader available for {fmt}")
            return 2
        kwargs = {"limit": None}
        if fmt in {"json", "jsonl"} and args.lines:
            kwargs["lines"] = True
        if fmt == "xlsx" and args.sheet:
            kwargs["sheet"] = int(args.sheet) if args.sheet.isdigit() else args.sheet

        # 3: read records
        try:
            table = reader.read(args.path, **kwargs)
            records = table.as_records()
            if args.schema:
                with open(args.schema, encoding="utf-8") as f:
                    schema = json.load(f)
            if not args.schema:
                print("No schema provided, skipping rule checks.")
                return 2
            # 4: validation
            vrep = validation.validate(records, schema)
            # 5: print + errors
            print(f"rows: {vrep.row_count}")
            print(f"columns: {vrep.column_count}")

            for issue in vrep.issues:
                print(
                    f"code={issue.code} column={issue.column} "
                    f"count={issue.count} examples={issue.examples}"
                )
            return 0
        except (FileFormatError, ConfigurationError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            return 1

    # report
    elif args.cmd == "report":
        if args.hist and not args.hist_out:
            print("Error: --hist requires --hist-out")
            return 2
        if args.bar and not args.bar_out:
            print("Error: --bar requires --bar-out")
            return 2
        # detect format
        if args.format:
            fmt = args.format.lower().lstrip(".")
        else:
            fmt = detect_format(args.path)

        if fmt is None:
            print(f"Error: unknown or unsupported format for {args.path}")
            return 2

        # choose reader & build kwargs
        reader = choose_reader(fmt)
        if reader is None:
            print(f"No reader available for format: {fmt}", file=sys.stderr)
            return 2

        kwargs = {"limit": None}

        if fmt in {"json", "jsonl"} and args.lines:
            kwargs["lines"] = True

        if fmt == "xlsx" and args.sheet:
            if args.sheet.isdigit():
                kwargs["sheet"] = int(args.sheet)
            else:
                kwargs["sheet"] = args.sheet

        # read records
        try:
            table = reader.read(args.path, **kwargs)
            records = table.as_records()
            # run analysis + validation
            rep = analysis.analyze(records, top_k=args.top_k)
            if args.schema:
                with open(args.schema, encoding="utf-8") as f:
                    schema = json.load(f)
            else:
                schema = {}
                print("No schema provided, skipping rule checks.")
            vrep = validation.validate(records, schema)

            # generate charts
            if args.hist:
                save_histogram(records, column=args.hist, out_path=args.hist_out)
            if args.bar:
                save_bar_counts(records, column=args.bar, out_path=args.bar_out, top_k=args.top_k)

            # write markdown
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(f"# Report for {args.path}\n\n")
                f.write("## Overview\n")
                f.write(f"- Rows: {rep.rows}\n")
                f.write(f"- Columns: {rep.columns}\n\n")

                # numeric
                f.write("## Numeric columns\n")
                if not rep.numeric:
                    f.write("- None\n")
                else:
                    for ns in rep.numeric:
                        f.write(
                            f"- {ns.column}: count={ns.count}, nulls={ns.nulls}, "
                            f"distinct={ns.distinct}, min={ns.min}, max={ns.max}, mean={ns.mean}\n"
                        )  # noqa: E501
                f.write("\n")

                # categorical
                f.write("## Categorical columns\n")
                if not rep.categorical:
                    f.write("- None\n")
                else:
                    for cs in rep.categorical:
                        f.write(
                            f"- {cs.column}: count={cs.count}, nulls={cs.nulls}, "
                            f"distinct={cs.distinct}, top={cs.top}\n"
                        )
                f.write("\n")

                # validation
                f.write("## Validation issues\n")
                if not vrep.issues:
                    f.write("- None\n")
                else:
                    for issue in vrep.issues:
                        f.write(
                            f"- code={issue.code}, column={issue.column}, "
                            f"count={issue.count}, examples={issue.examples}\n"
                        )
                f.write("\n")

                # charts
                f.write("## Charts\n")
                if args.hist:
                    f.write(f"- Histogram for `{args.hist}`: ![]({args.hist_out})\n")
                if args.bar:
                    f.write(f"- Bar chart for `{args.bar}`: ![]({args.bar_out})\n")

            return 0

        except (FileFormatError, ConfigurationError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
