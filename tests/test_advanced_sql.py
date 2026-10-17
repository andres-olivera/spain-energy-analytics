"""Smoke-test query library against isolated SQLite fixture without network."""
import sqlite3
from pathlib import Path

import pandas as pd

from spain_energy_analytics.advanced_sql import named_queries, run

ROOT = Path(__file__).resolve().parents[1]


def test_advanced_sql_queries_execute(tmp_path):
    database = tmp_path / "analytics.db"
    schema = (ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")
    with sqlite3.connect(database) as conn:
        conn.executescript(schema)
        conn.executemany(
            "INSERT INTO dim_indicator (indicator_key,dataset,indicator_id,indicator_title) "
            "VALUES (?,?,?,?)",
            [
                ("d:1", "demand", "1", "Demand"),
                ("p:1", "price", "1", "Price"),
                ("g:1", "generation", "1", "Wind"),
            ],
        )
        conn.executemany(
            "INSERT INTO dim_date (date_key,date,year,quarter,month,month_name,day,"
            "day_name,iso_week,is_weekend) VALUES (?,?,?,?,?,?,?,?,?,?)",
            [
                ("2025-01-01", "2025-01-01", 2025, 1, 1, "January", 1, "Wednesday", 1, 0),
                ("2025-01-04", "2025-01-04", 2025, 1, 1, "January", 4, "Saturday", 1, 1),
            ],
        )
        rows = []
        for indicator, val in [("d:1", 140), ("p:1", 55), ("g:1", 90)]:
            for i, date in enumerate(("2025-01-01", "2025-01-04")):
                ts = f"{date}T12:00:00+01:00"
                utc = f"{date}T11:00:00Z"
                rows.append((indicator, ts, utc, date, 12, 0, val + i * 20))
        conn.executemany(
            "INSERT INTO fact_observation (indicator_key,timestamp_local,timestamp_utc,"
            "date_key,hour_local,minute_local,value) VALUES (?,?,?,?,?,?,?)", rows
        )
    output = tmp_path / "output"
    summary = run(database, output)
    assert len(summary) == 5
    assert (output / "monthly_price_change.csv").exists()
    assert len(pd.read_csv(output / "monthly_generation_rank.csv")) > 0
    assert len(pd.read_csv(output / "monthly_extreme_price_hours.csv")) == 2


def test_named_query_titles():
    text = (ROOT / "sql" / "advanced_analysis.sql").read_text(encoding="utf-8")
    names = named_queries(text)
    assert set(names) == {
        "monthly_price_change", "rolling_demand", "demand_weekday_contrast",
        "monthly_extreme_price_hours", "monthly_generation_rank",
    }
