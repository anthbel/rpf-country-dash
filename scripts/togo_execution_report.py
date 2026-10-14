"""Write the DGBF's standard budget execution tables for one year to an xlsx file.

Reads boost.tgo_execution straight from the configured database (no query
cache), with the same environment as the dashboard:

    python scripts/togo_execution_report.py --year 2025 --out execution_2025.xlsx
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.togo_execution import normalise_execution  # noqa: E402
from components.togo_execution_report import build_report  # noqa: E402
from queries import QueryService  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--year", type=int, required=True, help="budget year, e.g. 2025")
    parser.add_argument("--out", required=True, help="path of the xlsx file to write")
    args = parser.parse_args(argv)

    df = normalise_execution(QueryService.get_instance().get_togo_execution_data(persistent=False))
    try:
        content = build_report(df, args.year)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    with open(args.out, "wb") as f:
        f.write(content)
    print(f"{args.out}: {len(content)} bytes, year {args.year}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
