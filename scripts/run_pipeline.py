"""Command-line entry point for the REData ETL pipeline."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from spain_energy_analytics.config import DATASETS
from spain_energy_analytics.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    previous_year = date.today().year - 1
    parser = argparse.ArgumentParser(description="Build the Spain Energy Analytics dataset")
    parser.add_argument("--start", default=f"{previous_year}-01-01", help="YYYY-MM-DD")
    parser.add_argument("--end", default=f"{previous_year}-12-31", help="YYYY-MM-DD")
    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=sorted(DATASETS),
        default=sorted(DATASETS),
        help="Datasets to extract",
    )
    parser.add_argument(
        "--time-trunc",
        choices=["hour", "day", "month", "year"],
        default=None,
        help=(
            "Override REData aggregation for every selected dataset. "
            "By default each dataset uses its validated resolution."
        ),
    )
    parser.add_argument(
        "--refresh-raw",
        action="store_true",
        help="Re-download raw JSON files even when they already exist",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]
    result = run_pipeline(
        start=date.fromisoformat(args.start),
        end=date.fromisoformat(args.end),
        datasets=args.datasets,
        project_root=project_root,
        time_trunc=args.time_trunc,
        refresh_raw=args.refresh_raw,
    )
    print("Pipeline completed successfully")
    print(f"Indicators:   {result.indicator_rows:,}")
    print(f"Observations: {result.observation_rows:,}")
    print(f"Dates:        {result.date_rows:,}")
    print(f"SQLite:       {result.database_path}")


if __name__ == "__main__":
    main()
