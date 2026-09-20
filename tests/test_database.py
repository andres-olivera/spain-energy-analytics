import json
import sqlite3
from pathlib import Path

from spain_energy_analytics.database import load_sqlite
from spain_energy_analytics.transform import build_date_dimension, normalize_payload

FIXTURE = Path(__file__).parent / "fixtures" / "ree_sample_payload.json"
SCHEMA = Path(__file__).parents[1] / "sql" / "schema.sql"


def test_load_sqlite_creates_queryable_star_model(tmp_path: Path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    indicators, facts = normalize_payload(payload, "generation")
    dates = build_date_dimension(facts)
    db_path = tmp_path / "test.db"

    load_sqlite(indicators, dates, facts, db_path, SCHEMA)

    connection = sqlite3.connect(db_path)
    try:
        indicator_count = connection.execute(
            "SELECT COUNT(*) FROM dim_indicator"
        ).fetchone()[0]
        fact_count = connection.execute(
            "SELECT COUNT(*) FROM fact_observation"
        ).fetchone()[0]
        joined = connection.execute(
            """
            SELECT COUNT(*)
            FROM fact_observation f
            JOIN dim_indicator i USING (indicator_key)
            JOIN dim_date d USING (date_key)
            """
        ).fetchone()[0]
    finally:
        connection.close()

    assert indicator_count == 2
    assert fact_count == 4
    assert joined == 4
