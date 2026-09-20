"""SQLite loading utilities."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def load_sqlite(
    indicators: pd.DataFrame,
    dates: pd.DataFrame,
    observations: pd.DataFrame,
    db_path: Path,
    schema_path: Path,
) -> None:
    """Rebuild the analytical SQLite database in one transaction."""

    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema = schema_path.read_text(encoding="utf-8")

    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema)
        connection.execute("DELETE FROM fact_observation")
        connection.execute("DELETE FROM dim_date")
        connection.execute("DELETE FROM dim_indicator")

        indicators.to_sql("dim_indicator", connection, if_exists="append", index=False)
        dates.to_sql("dim_date", connection, if_exists="append", index=False)
        observations.to_sql("fact_observation", connection, if_exists="append", index=False)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
