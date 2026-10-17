"""Build an auditable, read-only, compact demo snapshot from the ETL tables.

This is intentionally a public *derived* snapshot: no REData JSON is committed.
The records retain original indicator identifiers, UTC instants and source
magnitudes, so the public app need not guess units or combine unlike series.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

INDICATOR_FIELDS = ["indicator_key", "dataset", "indicator_title", "magnitude"]
OBSERVATION_FIELDS = [
    "indicator_key", "timestamp_utc", "date_key", "hour_local", "value",
]
VALID_DATASETS = {"demand", "generation", "price"}


def validate_snapshot(
    indicators: pd.DataFrame,
    observations: pd.DataFrame,
    year: int = 2025,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Require a complete, consistently keyed historical year."""
    missing_i = set(INDICATOR_FIELDS) - set(indicators.columns)
    missing_f = set(OBSERVATION_FIELDS) - set(observations.columns)
    if missing_i or missing_f:
        raise ValueError(
            f"Missing columns: indicators={sorted(missing_i)}, facts={sorted(missing_f)}"
        )
    dims = indicators.loc[:, INDICATOR_FIELDS].copy()
    facts = observations.loc[:, OBSERVATION_FIELDS].copy()
    if dims.empty or facts.empty:
        raise ValueError("Snapshot input is empty")
    if dims["indicator_key"].duplicated().any():
        raise ValueError("Duplicate indicator dimension keys")
    if facts[["indicator_key", "timestamp_utc"]].duplicated().any():
        raise ValueError("Duplicate indicator / UTC timestamp observations")
    if facts[OBSERVATION_FIELDS].isnull().any().any():
        raise ValueError("Null fact fields are not allowed")
    facts["value"] = pd.to_numeric(facts["value"], errors="raise")
    facts["hour_local"] = pd.to_numeric(facts["hour_local"], errors="raise").astype(int)
    if (~facts["hour_local"].between(0, 23)).any():
        raise ValueError("Invalid local hours")
    dates = pd.to_datetime(facts["date_key"], format="%Y-%m-%d", errors="raise")
    if (dates.dt.year != year).any():
        raise ValueError("Found observations outside the intended demo year")
    if dates.dt.normalize().nunique() != 365:
        raise ValueError("Expected all 365 calendar dates for a non-leap-year demo")
    if len(facts) < 20000:
        raise ValueError("Unexpectedly incomplete full-year ETL output")
    if not facts["indicator_key"].isin(dims["indicator_key"]).all():
        raise ValueError("Some observations do not match a dimension key")
    if not VALID_DATASETS.issubset(set(dims["dataset"])):
        raise ValueError("Missing one or more required dataset categories")
    for category in VALID_DATASETS:
        keys = dims.loc[dims["dataset"] == category, "indicator_key"]
        if not facts["indicator_key"].isin(keys).any():
            raise ValueError(f"No observations for {category}")
    return (
        dims.sort_values(["dataset", "indicator_title", "indicator_key"]).reset_index(
            drop=True
        ),
        facts.sort_values(["date_key", "timestamp_utc", "indicator_key"]).reset_index(
            drop=True
        ),
    )


def publish_snapshot(
    processed_dir: str | Path,
    output_dir: str | Path,
    year: int = 2025,
) -> dict:
    """Export only the columns needed by the public portfolio dashboard."""
    processed = Path(processed_dir)
    result = Path(output_dir)
    dims = pd.read_csv(processed / "dim_indicator.csv")
    facts = pd.read_csv(processed / "fact_observation.csv")
    dimensions, observations = validate_snapshot(dims, facts, year)
    result.mkdir(parents=True, exist_ok=True)
    dimensions.to_csv(result / "indicators.csv", index=False)
    observations.to_csv(result / "observations.csv", index=False)
    summary = {
        "year": year,
        "source": "Red Eléctrica REData API",
        "source_url": "https://apidatos.ree.es",
        "observation_rows": int(len(observations)),
        "indicators": int(len(dimensions)),
        "unique_dates": int(observations["date_key"].nunique()),
        "per_dataset": {
            name: int(observations["indicator_key"].isin(
                dimensions.loc[dimensions["dataset"] == name, "indicator_key"]
            ).sum())
            for name in sorted(VALID_DATASETS)
        },
        "method": "Full-year validated ETL, public analytic extract (not live data)",
    }
    (result / "source.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return summary
