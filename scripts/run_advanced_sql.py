"""Execute advanced SQL analyses against the reproducible SQLite model."""

import argparse
from pathlib import Path

from spain_energy_analytics.advanced_sql import DEFAULT_DB, ROOT, run

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "tables")
    args = parser.parse_args()
    for name, n in run(args.db, args.output).items():
        print(f"{name}: {n} rows")
