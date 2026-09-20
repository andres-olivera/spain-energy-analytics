"""Run a compact SQL portfolio analysis against the local SQLite database."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

QUERIES = {
    "coverage_by_dataset": """
        SELECT i.dataset, COUNT(*) AS observations,
               MIN(f.timestamp_local) AS first_timestamp,
               MAX(f.timestamp_local) AS last_timestamp
        FROM fact_observation AS f
        JOIN dim_indicator AS i USING (indicator_key)
        GROUP BY i.dataset
        ORDER BY i.dataset;
    """,
    "top_generation_indicators": """
        SELECT i.indicator_title, AVG(f.value) AS average_value,
               MAX(f.value) AS maximum_value, COUNT(*) AS observations
        FROM fact_observation AS f
        JOIN dim_indicator AS i USING (indicator_key)
        WHERE i.dataset = 'generation'
        GROUP BY i.indicator_title
        ORDER BY average_value DESC
        LIMIT 10;
    """,
    "demand_weekday_vs_weekend": """
        SELECT i.indicator_title, d.is_weekend, AVG(f.value) AS average_value
        FROM fact_observation AS f
        JOIN dim_indicator AS i USING (indicator_key)
        JOIN dim_date AS d USING (date_key)
        WHERE i.dataset = 'demand'
        GROUP BY i.indicator_title, d.is_weekend
        ORDER BY i.indicator_title, d.is_weekend;
    """,
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    db_path = root / "data" / "processed" / "spain_energy.db"
    if not db_path.exists():
        raise SystemExit("Database not found. Run scripts/run_pipeline.py first.")

    output_dir = root / "reports" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    try:
        for name, query in QUERIES.items():
            frame = pd.read_sql_query(query, connection)
            frame.to_csv(output_dir / f"{name}.csv", index=False)
            print(f"\n{name}\n{'-' * len(name)}")
            print(frame.to_string(index=False))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
