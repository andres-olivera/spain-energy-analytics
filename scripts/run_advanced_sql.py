"""Execute read-only advanced SQL analyses on the locally generated SQLite model."""
from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
QUERY_FILE = ROOT / "sql" / "advanced_analysis.sql"
DEFAULT_DB = ROOT / "data" / "processed" / "spain_energy.db"


def named_queries(sql_text: str) -> dict[str, str]:
    """Parse explicit -- QUERY: name blocks, rejecting unsafe or empty sections."""
    parts = re.split(r"(?m)^-- QUERY: ([a-z][a-z0-9_]*)\s*$", sql_text)
    result = {}
    for name, body in zip(parts[1::2], parts[2::2], strict=True):
        clean = body.strip()
        if not clean or not clean.endswith(";"):
            raise ValueError(f"Incomplete SQL query: {name}")
        if name in result:
            raise ValueError(f"Duplicate SQL query name: {name}")
        # Named sections contain one readonly SQL SELECT/CTE query each.
        if not re.search(r"(?im)^WITH\s", clean) and not re.search(
            r"(?im)^SELECT\s", clean
        ):
            raise ValueError(f"Expected CTE or SELECT in {name}")
        result[name] = clean
    if len(result) < 5:
        raise ValueError("Expected five named advanced portfolio queries")
    return result


def run(db_path: Path, output_dir: Path, queries_path: Path = QUERY_FILE) -> dict:
    if not db_path.is_file():
        raise FileNotFoundError(
            f"No local SQLite database at {db_path}. Run scripts/run_pipeline.py first."
        )
    queries = named_queries(queries_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    # Readonly URI prevents accidental DB modification.
    with sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True) as conn:
        for name, query in queries.items():
            frame = pd.read_sql_query(query, conn)
            frame.to_csv(output_dir / f"{name}.csv", index=False)
            results[name] = len(frame)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "tables")
    args = parser.parse_args()
    results = run(args.db, args.output)
    for key, n in results.items():
        print(f"{key}: {n} rows")
