"""Independent tests of historical public export; no network required."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from spain_energy_analytics.public_demo import publish_snapshot, validate_snapshot


def synthetic_2025() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Exercise the full-year coverage contract with >20k synthetic readings."""
    dates = pd.date_range("2025-01-01", periods=365, freq="D")
    keys = ["d:1", "p:1"] + [f"g:{n}" for n in range(13)]
    indicators = pd.DataFrame({
        "indicator_key": keys,
        "dataset": ["demand", "price"] + ["generation"] * 13,
        "indicator_title": ["Demand", "Price"] + [f"Tech {n}" for n in range(13)],
        "magnitude": ["MW", "EUR"] + ["MW"] * 13,
    })
    rows = []
    for day in dates:
        date_key = day.strftime("%Y-%m-%d")
        for hour in range(24):
            stamp = f"{date_key}T{hour:02d}:00:00Z"
            rows.append(("d:1", stamp, date_key, hour, float(hour + 100)))
            rows.append(("p:1", stamp, date_key, hour, float(hour + 30)))
        for tech in range(13):
            rows.append((f"g:{tech}", f"{date_key}T00:00:00Z",
                         date_key, 0, float(tech + 10)))
    facts = pd.DataFrame(rows, columns=[
        "indicator_key", "timestamp_utc", "date_key", "hour_local", "value",
    ])
    return indicators, facts


def test_public_demo_full_year_contract():
    indicators, facts = synthetic_2025()
    dims, obs = validate_snapshot(indicators, facts)
    assert len(obs) == 61 * 365
    assert len(dims) == 15
    assert obs["date_key"].nunique() == 365


def test_public_demo_detects_missing_days():
    indicators, facts = synthetic_2025()
    with pytest.raises(ValueError, match="365"):
        validate_snapshot(indicators, facts.loc[facts["date_key"] != "2025-04-09"])


def test_public_demo_detects_duplicate_utc_timestamp():
    indicators, facts = synthetic_2025()
    with pytest.raises(ValueError, match="Duplicate"):
        validate_snapshot(indicators, pd.concat([facts, facts.iloc[:1]], ignore_index=True))


def test_public_demo_detects_orphan_fact():
    indicators, facts = synthetic_2025()
    facts.loc[0, "indicator_key"] = "unknown:key"
    with pytest.raises(ValueError, match="do not match"):
        validate_snapshot(indicators, facts)


def test_public_demo_exports_reproducible_csvs(tmp_path: Path):
    indicators, facts = synthetic_2025()
    processed = tmp_path / "processed"
    processed.mkdir()
    indicators.to_csv(processed / "dim_indicator.csv", index=False)
    facts.to_csv(processed / "fact_observation.csv", index=False)
    snapshot = tmp_path / "public"
    report = publish_snapshot(processed, snapshot)
    assert report["observation_rows"] == len(facts)
    assert report["unique_dates"] == 365
    assert (snapshot / "indicators.csv").exists()
    assert (snapshot / "observations.csv").exists()
    assert (snapshot / "source.json").exists()
