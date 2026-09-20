import json
from pathlib import Path

from spain_energy_analytics.transform import build_date_dimension, normalize_payload

FIXTURE = Path(__file__).parent / "fixtures" / "ree_sample_payload.json"


def test_normalize_payload_builds_dimensions_and_facts() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    indicators, facts = normalize_payload(payload, "generation")

    assert len(indicators) == 2
    assert len(facts) == 4
    assert set(indicators["indicator_key"]) == {"generation:12", "generation:14"}
    assert facts.loc[0, "date_key"] == "2026-01-01"
    assert facts.loc[0, "timestamp_utc"].endswith("Z")
    assert facts["value"].sum() == 12300.0


def test_build_date_dimension_has_one_row_per_local_date() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    _, facts = normalize_payload(payload, "generation")
    dates = build_date_dimension(facts)

    assert len(dates) == 1
    row = dates.iloc[0]
    assert row["date_key"] == "2026-01-01"
    assert row["year"] == 2026
    assert row["month"] == 1
    assert row["is_weekend"] == 0
