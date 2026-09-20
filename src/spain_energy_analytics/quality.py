"""Lightweight data-quality checks for pipeline outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd


class DataQualityError(RuntimeError):
    """Raised when a required data-quality rule fails."""


@dataclass(frozen=True)
class QualityReport:
    indicator_rows: int
    observation_rows: int
    date_rows: int
    duplicate_observations: int
    null_values: int
    orphan_indicators: int
    orphan_dates: int
    min_timestamp_utc: str | None
    max_timestamp_utc: str | None

    def to_dict(self) -> dict:
        return asdict(self)


def run_quality_checks(
    indicators: pd.DataFrame, dates: pd.DataFrame, observations: pd.DataFrame
) -> QualityReport:
    """Validate primary keys, foreign keys, and required fact values."""

    duplicates = int(
        observations.duplicated(subset=["indicator_key", "timestamp_local"]).sum()
    )
    null_values = int(observations["value"].isna().sum()) if "value" in observations else 0

    indicator_keys = set(indicators.get("indicator_key", pd.Series(dtype=str)).astype(str))
    fact_indicator_keys = set(
        observations.get("indicator_key", pd.Series(dtype=str)).astype(str)
    )
    date_keys = set(dates.get("date_key", pd.Series(dtype=str)).astype(str))
    fact_date_keys = set(observations.get("date_key", pd.Series(dtype=str)).astype(str))

    orphan_indicators = len(fact_indicator_keys - indicator_keys)
    orphan_dates = len(fact_date_keys - date_keys)

    report = QualityReport(
        indicator_rows=len(indicators),
        observation_rows=len(observations),
        date_rows=len(dates),
        duplicate_observations=duplicates,
        null_values=null_values,
        orphan_indicators=orphan_indicators,
        orphan_dates=orphan_dates,
        min_timestamp_utc=(
            str(observations["timestamp_utc"].min()) if not observations.empty else None
        ),
        max_timestamp_utc=(
            str(observations["timestamp_utc"].max()) if not observations.empty else None
        ),
    )

    failures = {
        "duplicate_observations": duplicates,
        "null_values": null_values,
        "orphan_indicators": orphan_indicators,
        "orphan_dates": orphan_dates,
    }
    failed = {name: value for name, value in failures.items() if value}
    if failed:
        raise DataQualityError(f"Data-quality checks failed: {failed}")

    return report
